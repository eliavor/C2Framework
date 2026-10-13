"""
Part 5 — Database (State & Keys)
Stores agents, tasks, and per-agent encryption keys using SQLite.
"""

import sqlite3
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "c2.db"

_local = threading.local()


def _conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(str(DB_PATH))
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn


# Agents that have not beaconed within this window are shown as inactive.
# Set to roughly 2-3x your expected beacon interval.
STALE_SECONDS = 120


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_status(last_seen: str) -> str:
    try:
        ts = datetime.fromisoformat(last_seen)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        return "active" if age <= STALE_SECONDS else "inactive"
    except Exception:
        return "unknown"


def init_db():
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id        TEXT PRIMARY KEY,
                hostname  TEXT NOT NULL,
                ip        TEXT NOT NULL,
                os        TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                status    TEXT NOT NULL DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id         TEXT PRIMARY KEY,
                agent_id   TEXT NOT NULL,
                capability TEXT NOT NULL,
                params     TEXT NOT NULL DEFAULT '{}',
                status     TEXT NOT NULL DEFAULT 'pending',
                result     TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            );

            CREATE TABLE IF NOT EXISTS agent_keys (
                agent_id TEXT PRIMARY KEY,
                key_hex  TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            );
        """)


class AgentStore:
    def register(self, agent_id: str, hostname: str, ip: str, os_info: str):
        with _conn() as c:
            c.execute(
                """INSERT INTO agents (id, hostname, ip, os, last_seen, status)
                   VALUES (?, ?, ?, ?, ?, 'active')
                   ON CONFLICT(id) DO UPDATE SET
                     hostname=excluded.hostname, ip=excluded.ip,
                     os=excluded.os, last_seen=excluded.last_seen,
                     status='active'""",
                (agent_id, hostname, ip, os_info, _now()),
            )

    def heartbeat(self, agent_id: str):
        with _conn() as c:
            c.execute("UPDATE agents SET last_seen=? WHERE id=?", (_now(), agent_id))

    def get(self, agent_id: str) -> dict | None:
        row = _conn().execute(
            "SELECT * FROM agents WHERE id=?", (agent_id,)
        ).fetchone()
        if not row:
            return None
        agent = dict(row)
        agent["status"] = _compute_status(agent["last_seen"])
        return agent

    def list_all(self) -> list[dict]:
        rows = _conn().execute(
            "SELECT * FROM agents ORDER BY last_seen DESC"
        ).fetchall()
        agents = [dict(r) for r in rows]
        for a in agents:
            a["status"] = _compute_status(a["last_seen"])
        return agents


class TaskStore:
    def create(self, task_id: str, agent_id: str, capability: str, params: dict):
        now = _now()
        with _conn() as c:
            c.execute(
                """INSERT INTO tasks
                   (id, agent_id, capability, params, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'pending', ?, ?)""",
                (task_id, agent_id, capability, json.dumps(params), now, now),
            )

    def get_next_pending(self, agent_id: str) -> dict | None:
        row = _conn().execute(
            """SELECT * FROM tasks WHERE agent_id=? AND status='pending'
               ORDER BY created_at LIMIT 1""",
            (agent_id,),
        ).fetchone()
        return dict(row) if row else None

    def update_status(self, task_id: str, status: str, result: str | None = None):
        with _conn() as c:
            c.execute(
                "UPDATE tasks SET status=?, result=?, updated_at=? WHERE id=?",
                (status, result, _now(), task_id),
            )

    def get(self, task_id: str) -> dict | None:
        row = _conn().execute(
            "SELECT * FROM tasks WHERE id=?", (task_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_for_agent(self, agent_id: str) -> list[dict]:
        rows = _conn().execute(
            "SELECT * FROM tasks WHERE agent_id=? ORDER BY created_at DESC",
            (agent_id,),
        ).fetchall()
        return [dict(r) for r in rows]


class KeyStore:
    def set_key(self, agent_id: str, key_hex: str):
        with _conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO agent_keys (agent_id, key_hex) VALUES (?, ?)",
                (agent_id, key_hex),
            )

    def get_key(self, agent_id: str) -> str | None:
        row = _conn().execute(
            "SELECT key_hex FROM agent_keys WHERE agent_id=?", (agent_id,)
        ).fetchone()
        return row["key_hex"] if row else None
