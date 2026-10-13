"""
Part 1 — Connection Handler
Abstract base class for agent-facing transport. Implement a new subclass to
add any transport (TCP, DNS, ICMP, etc.) without touching the crypto or
data-parsing layers.

Bundled implementation: TcpConnectionHandler (raw TCP, no HTTP).

Wire protocol:
  client -> server : "<command> <agent_id>\n"   e.g. "keepalive abcdeabcde"
  server -> client : "<response>"               e.g. "OK" or "shell_exec"
"""

import logging
import socket
import threading
from abc import ABC, abstractmethod
from typing import Callable

log = logging.getLogger(__name__)

# Callback signature: (agent_id: str, raw_bytes: bytes) -> bytes
MessageCallback = Callable[[str, bytes], bytes]


class ConnectionHandler(ABC):
    """
    Subclass this to add a new transport. The only contract:
      - Call self._dispatch(agent_id, raw) to process an incoming message.
      - Return the bytes that _dispatch returns as the response.
    """

    def __init__(self):
        self._callback: MessageCallback | None = None

    def set_message_callback(self, callback: MessageCallback):
        self._callback = callback

    def _dispatch(self, agent_id: str, raw: bytes) -> bytes:
        if self._callback is None:
            log.warning("No message callback registered.")
            return b""
        return self._callback(agent_id, raw)

    @abstractmethod
    def start(self, host: str, port: int):
        """Start listening for agent connections (non-blocking)."""

    @abstractmethod
    def stop(self):
        """Gracefully stop the listener."""


# ---------------------------------------------------------------------------
# Concrete implementation: raw TCP
# ---------------------------------------------------------------------------

class TcpConnectionHandler(ConnectionHandler):
    """
    One TCP connection per beacon. Client sends "<command> <agent_id>",
    server replies with the response string and closes the connection.
    """

    def __init__(self):
        super().__init__()
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self, host: str = "0.0.0.0", port: int = 9000):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((host, port))
        self._sock.listen(64)
        self._running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()
        log.info("TCP agent listener started on %s:%d", host, port)

    def _accept_loop(self):
        while self._running:
            try:
                conn, addr = self._sock.accept()
                threading.Thread(
                    target=self._handle_conn, args=(conn, addr), daemon=True
                ).start()
            except OSError:
                break

    def _handle_conn(self, conn: socket.socket, addr):
        with conn:
            try:
                data = conn.recv(4096)
                if not data:
                    return
                parts = data.decode().strip().split(" ", 1)
                command  = parts[0]
                agent_id = parts[1] if len(parts) > 1 else ""
                response = self._dispatch(agent_id, command.encode())
                conn.sendall(response)
            except Exception as exc:
                log.warning("Error handling connection from %s: %s", addr, exc)

    def stop(self):
        self._running = False
        if self._sock:
            self._sock.close()
            log.info("TCP agent listener stopped.")
