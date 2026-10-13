"""
Part 1 — Connection Handler
Abstract base class for agent-facing transport. Implement a new subclass to
add any transport (HTTPS, DNS, ICMP, etc.) without touching the crypto or
data-parsing layers.

Bundled implementation: HttpConnectionHandler (plain HTTP, dev/test use only).
"""

import logging
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
# Concrete implementation: HTTP
# ---------------------------------------------------------------------------

class HttpConnectionHandler(ConnectionHandler):
    """
    Agents POST raw (encrypted) bytes to  POST /beacon/<agent_id>.
    The response body carries the encrypted reply.
    """

    def __init__(self):
        super().__init__()
        from flask import Flask
        self._app = Flask(__name__)
        self._server = None
        self._thread: threading.Thread | None = None
        self._register_routes()

    def _register_routes(self):
        from flask import request, Response

        @self._app.route("/beacon/<agent_id>", methods=["POST"])
        def beacon(agent_id: str):
            raw = request.get_data()
            response_bytes = self._dispatch(agent_id, raw)
            return Response(response_bytes, content_type="application/octet-stream")

    def start(self, host: str = "0.0.0.0", port: int = 8080):
        from werkzeug.serving import make_server

        self._server = make_server(host, port, self._app)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        log.info("Agent listener started on %s:%d", host, port)

    def stop(self):
        if self._server:
            self._server.shutdown()
            log.info("Agent listener stopped.")
