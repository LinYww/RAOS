import subprocess
from pathlib import Path
from urllib import request

from app.tools.contracts import ToolExecutionContext, ToolInvocationResult
from app.tools.exceptions import ToolExecutionError


def read_file_tool(arguments: dict, context: ToolExecutionContext) -> ToolInvocationResult:
    workspace_root = Path.cwd().resolve()
    target = (workspace_root / arguments["path"]).resolve()
    # Resolve against cwd and then re-check ancestry to block path traversal via
    # segments such as ".." or absolute-looking user input.
    if workspace_root not in target.parents and target != workspace_root:
        raise ToolExecutionError("Requested file path is outside the workspace root.")
    content = target.read_text(encoding="utf-8")
    max_chars = arguments.get("max_chars", 4000)
    truncated = len(content) > max_chars
    return ToolInvocationResult(
        payload={
            "path": str(target),
            "content": content[:max_chars],
            "truncated": truncated,
        },
        audit_fields={"tool": "file.read", "path": str(target)},
    )


def shell_exec_tool(arguments: dict, context: ToolExecutionContext) -> ToolInvocationResult:
    command = arguments["command"]
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        raise ToolExecutionError("Shell command must be a list of strings.")
    timeout_seconds = arguments.get("timeout_seconds", 15)
    # Explicit argv tokens avoid shell interpolation and keep the audit trail
    # stable across Windows and POSIX environments.
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        cwd=Path.cwd(),
        check=False,
    )
    return ToolInvocationResult(
        payload={
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
        audit_fields={"tool": "shell.exec", "command": command},
    )


def http_fetch_tool(arguments: dict, context: ToolExecutionContext) -> ToolInvocationResult:
    req = request.Request(arguments["url"], method="GET")
    with request.urlopen(req, timeout=arguments.get("timeout_seconds", 15)) as response:
        body = response.read().decode("utf-8", errors="replace")
        return ToolInvocationResult(
            payload={
                "status_code": response.status,
                # Cap response size so checkpoints and task events do not balloon on
                # large HTML pages or binary-ish endpoints.
                "body": body[: arguments.get("max_chars", 4000)],
            },
            audit_fields={"tool": "http.fetch", "url": arguments["url"]},
        )
