# Server

The C2 backend. Handles all agent connections, task management, and exposes a REST API for the operator.

---

## Structure

The server is split into five components, each in its own file:

| File | Role |
|---|---|
| `database.py` | SQLite storage for agents, tasks, and keys. Computes agent status from `last_seen`. |
| `data_parser_crypto.py` | Message serialization. Crypto will be added here when ready. |
| `task_queue.py` | Task lifecycle: enqueue, dispatch, complete, fail |
| `connection_handler.py` | Abstract transport base class + raw TCP implementation |
| `operator_api.py` | REST API consumed by the operator CLI |
| `main.py` | Entry point, wires all components together |

Capabilities live in `capabilities/`:

| File | Role |
|---|---|
| `capabilities/base.py` | Abstract `Capability` class to extend |
| `capabilities/__init__.py` | Registry: maps capability names to classes |
| `capabilities/shell_exec.py` | Built-in: run a shell command |

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Running

```bash
python main.py
```

By default:
- Agent listener: `0.0.0.0:9000`
- Operator API: `127.0.0.1:9001`
- Operator token: `changeme`

Override the token with an environment variable:

```bash
C2_OPERATOR_TOKEN=mysecrettoken python main.py
```

---

## Agent Status

Agents do not hold a persistent connection. The server determines whether an agent is active or inactive based on its `last_seen` timestamp. Any agent that has not beaconed within `STALE_SECONDS` (default: 120s) is reported as `inactive`. This value is set at the top of `database.py` and should be roughly 2-3x your expected beacon interval.

---

## Adding a Capability

1. Create a new file in `capabilities/`, subclass `Capability`, and set `name` and `description`.
2. Implement `execute(params: dict) -> str`.
3. Import and register the class in `capabilities/__init__.py`.

```python
# capabilities/screenshot.py
from capabilities.base import Capability

class Screenshot(Capability):
    name = "screenshot"
    description = "Capture a screenshot of the active desktop"

    def execute(self, params: dict) -> str:
        ...
```

```python
# capabilities/__init__.py
from capabilities.screenshot import Screenshot
register(Screenshot)
```

Nothing else in the server needs to change.

---

## Adding a Transport

Subclass `ConnectionHandler`, implement `start()` and `stop()`, and call `self._dispatch(agent_id, raw_bytes)` when a message arrives. The parsing layer is unaware of the transport.

```python
class DnsConnectionHandler(ConnectionHandler):
    def start(self, host, port): ...
    def stop(self): ...
```

Swap the handler in `main.py` and everything else keeps working.

---

## Agent Communication Protocol

> No encryption is in place yet. All messages are plain text. This will change.

Agents do not maintain a persistent connection. Each beacon opens a raw TCP connection, sends a single line, reads a single word back, and closes.

### Transport

```
TCP  0.0.0.0:9000
```

One connection per beacon. No HTTP, no headers, no framing — just bytes.

### Agent → server

```
keepalive <agent_id>
```

`agent_id` is a 10-character string chosen by the implant and fixed for its lifetime. Any printable characters are fine; avoid spaces and newlines since the server splits on the first space.

Example:

```
keepalive abcdeabcde
```

### Server → agent

The server replies with a single word and closes the connection.

| Response | Meaning |
|---|---|
| `OK` | No task queued — go back to sleep |
| `shell_exec` | A shell command is waiting |

Example (no task):

```
OK
```

Example (task ready):

```
shell_exec
```

### Full beacon flow

```
client                          server
  |                               |
  |-- TCP connect ---------------->|
  |-- "keepalive abcdeabcde" ----->|
  |<-- "OK"  (or "shell_exec") ---|
  |-- TCP close ------------------>|
```

At most one task is dispatched per beacon. Result reporting is not yet implemented.

---

## Operator REST API

All endpoints require the header `X-Auth-Token: <token>`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/agents` | List all agents with live status |
| `GET` | `/agents/<id>` | Get a single agent |
| `GET` | `/agents/<id>/tasks` | List all tasks for an agent |
| `POST` | `/agents/<id>/tasks` | Queue a new task |
| `GET` | `/tasks/<id>` | Get a task and its result |
| `GET` | `/capabilities` | List registered capabilities |

### Queue a task

```
POST /agents/<id>/tasks
Content-Type: application/json
X-Auth-Token: <token>

{
    "capability": "shell_exec",
    "params": { "command": "whoami" }
}
```

Response:

```json
{ "task_id": "<uuid>" }
```

### Task statuses

| Status | Meaning |
|---|---|
| `pending` | Queued, not yet sent to the agent |
| `dispatched` | Delivered to the agent on its last beacon |
| `completed` | Agent returned output |
| `failed` | Agent reported an error |
