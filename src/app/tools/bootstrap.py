"""Bootstrap helpers for the built-in tool registry and gateway."""

from functools import lru_cache

from app.tools.builtin import http_fetch_tool, read_file_tool, shell_exec_tool
from app.tools.contracts import ToolDefinitionContract
from app.tools.gateway import ToolGateway
from app.tools.registry import ToolRegistry


@lru_cache
def get_tool_registry() -> ToolRegistry:
    """Build and cache the registry containing all built-in tools."""
    registry = ToolRegistry()
    registry.register(
        ToolDefinitionContract(
            name="file.read",
            description="Read a UTF-8 text file from the current workspace.",
            permission_scope="workspace.read",
            input_schema={
                "type": "object",
                "required": ["path"],
                "properties": {
                    "path": {"type": "string"},
                    "max_chars": {"type": "integer"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["path", "content", "truncated"],
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "truncated": {"type": "boolean"},
                },
            },
            audit_fields={"category": "file"},
        ),
        read_file_tool,
    )
    registry.register(
        ToolDefinitionContract(
            name="shell.exec",
            description="Run a shell command using explicit argument tokens.",
            permission_scope="shell.exec",
            input_schema={
                "type": "object",
                "required": ["command"],
                "properties": {
                    "command": {"type": "array"},
                    "timeout_seconds": {"type": "integer"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["exit_code", "stdout", "stderr"],
                "properties": {
                    "exit_code": {"type": "integer"},
                    "stdout": {"type": "string"},
                    "stderr": {"type": "string"},
                },
            },
            audit_fields={"category": "shell"},
        ),
        shell_exec_tool,
    )
    registry.register(
        ToolDefinitionContract(
            name="http.fetch",
            description="Fetch an HTTP resource through a GET request.",
            permission_scope="http.fetch",
            input_schema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {"type": "string"},
                    "timeout_seconds": {"type": "integer"},
                    "max_chars": {"type": "integer"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["status_code", "body"],
                "properties": {
                    "status_code": {"type": "integer"},
                    "body": {"type": "string"},
                },
            },
            audit_fields={"category": "http"},
        ),
        http_fetch_tool,
    )
    return registry


@lru_cache
def get_tool_gateway() -> ToolGateway:
    """Build and cache the gateway that fronts the built-in registry."""
    return ToolGateway(get_tool_registry())
