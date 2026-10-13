"""
Part 4 — Operator API (REST)
Flask REST API consumed by the operator CLI (and any other tool).
All endpoints require the X-Auth-Token header.
"""

import logging
import threading
from functools import wraps

from flask import Flask, jsonify, request, Response

from database import AgentStore, TaskStore, KeyStore
from task_queue import TaskQueue
import capabilities as cap_registry

log = logging.getLogger(__name__)


def create_app(
    agent_store: AgentStore,
    task_store: TaskStore,
    key_store: KeyStore,
    task_queue: TaskQueue,
    auth_token: str,
) -> Flask:
    app = Flask(__name__)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    def require_auth(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.headers.get("X-Auth-Token") != auth_token:
                return jsonify({"error": "Unauthorized"}), 401
            return f(*args, **kwargs)
        return wrapper

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------
    @app.route("/agents", methods=["GET"])
    @require_auth
    def list_agents():
        return jsonify(agent_store.list_all())

    @app.route("/agents/<agent_id>", methods=["GET"])
    @require_auth
    def get_agent(agent_id: str):
        agent = agent_store.get(agent_id)
        if not agent:
            return jsonify({"error": "Not found"}), 404
        return jsonify(agent)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------
    @app.route("/agents/<agent_id>/tasks", methods=["GET"])
    @require_auth
    def list_tasks(agent_id: str):
        return jsonify(task_store.list_for_agent(agent_id))

    @app.route("/agents/<agent_id>/tasks", methods=["POST"])
    @require_auth
    def create_task(agent_id: str):
        body = request.get_json(force=True)
        capability = body.get("capability")
        params = body.get("params", {})
        if not capability:
            return jsonify({"error": "'capability' is required"}), 400
        try:
            task_id = task_queue.enqueue(agent_id, capability, params)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify({"task_id": task_id}), 201

    @app.route("/tasks/<task_id>", methods=["GET"])
    @require_auth
    def get_task(task_id: str):
        task = task_queue.get(task_id)
        if not task:
            return jsonify({"error": "Not found"}), 404
        return jsonify(task)

    # ------------------------------------------------------------------
    # Capabilities (metadata only — execution happens on the client)
    # ------------------------------------------------------------------
    @app.route("/capabilities", methods=["GET"])
    @require_auth
    def list_capabilities():
        return jsonify(cap_registry.list_capabilities())

    return app


class OperatorApiServer:
    def __init__(self, app: Flask):
        self._app = app
        self._server = None
        self._thread: threading.Thread | None = None

    def start(self, host: str = "127.0.0.1", port: int = 8081):
        from werkzeug.serving import make_server
        self._server = make_server(host, port, self._app)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        log.info("Operator API started on %s:%d", host, port)

    def stop(self):
        if self._server:
            self._server.shutdown()
            log.info("Operator API stopped.")
