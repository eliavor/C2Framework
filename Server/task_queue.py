"""
Part 3 — Task Queue
Manages the lifecycle of tasks dispatched to agents.
Operators enqueue tasks; agents dequeue and return results.
"""

import json
import uuid

from database import AgentStore, TaskStore


class TaskQueue:
    def __init__(self, agent_store: AgentStore, task_store: TaskStore):
        self._agents = agent_store
        self._tasks = task_store

    def enqueue(self, agent_id: str, capability: str, params: dict) -> str:
        """Create a pending task for an agent. Returns the new task ID."""
        if not self._agents.get(agent_id):
            raise ValueError(f"Unknown agent: {agent_id}")
        task_id = str(uuid.uuid4())
        self._tasks.create(task_id, agent_id, capability, params)
        return task_id

    def dequeue(self, agent_id: str) -> dict | None:
        """
        Pop the next pending task for an agent and mark it as dispatched.
        Returns the task dict (with params deserialized), or None.
        """
        task = self._tasks.get_next_pending(agent_id)
        if not task:
            return None
        self._tasks.update_status(task["id"], "dispatched")
        task["params"] = json.loads(task["params"])
        return task

    def complete(self, task_id: str, result: str):
        self._tasks.update_status(task_id, "completed", result)

    def fail(self, task_id: str, error: str):
        self._tasks.update_status(task_id, "failed", error)

    def get(self, task_id: str) -> dict | None:
        task = self._tasks.get(task_id)
        if task and isinstance(task.get("params"), str):
            task["params"] = json.loads(task["params"])
        return task
