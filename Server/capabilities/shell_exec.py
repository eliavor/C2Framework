"""
Capability: shell_exec
Executes an arbitrary shell command and returns combined stdout/stderr.
Params: {"command": "<shell command string>"}
"""

import subprocess

from capabilities.base import Capability


class ShellExec(Capability):
    name = "shell_exec"
    description = "Execute a shell command and return its output"

    def execute(self, params: dict) -> str:
        command = params.get("command", "").strip()
        if not command:
            return "ERROR: no command provided"
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = proc.stdout + proc.stderr
            return output.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return "ERROR: command timed out"
        except Exception as exc:
            return f"ERROR: {exc}"
