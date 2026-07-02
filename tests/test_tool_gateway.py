"""Tests for tool authorization, validation, and execution dispatch."""

from app.tools.bootstrap import get_tool_gateway
from app.tools.contracts import ToolExecutionContext
from app.tools.exceptions import ToolPermissionError, ToolValidationError
from app.tools.gateway import ToolCall


def make_context(*, scopes: list[str]) -> ToolExecutionContext:
    """Build a minimal tool-execution context with the requested scopes."""
    return ToolExecutionContext(
        task_id="task-1",
        attempt_id="attempt-1",
        allowed_scopes=set(scopes),
        audit_context={},
    )


def test_gateway_rejects_unauthorized_tool_invocation() -> None:
    """Missing permission scopes should block tool execution."""
    gateway = get_tool_gateway()
    try:
        gateway.invoke(ToolCall(name="file.read", arguments={"path": "README.md"}), make_context(scopes=[]))
    except ToolPermissionError:
        assert True
        return
    raise AssertionError("Expected ToolPermissionError for missing scope.")


def test_gateway_rejects_invalid_tool_input() -> None:
    """Schema validation should reject malformed tool arguments."""
    gateway = get_tool_gateway()
    try:
        gateway.invoke(ToolCall(name="file.read", arguments={}), make_context(scopes=["workspace.read"]))
    except ToolValidationError:
        assert True
        return
    raise AssertionError("Expected ToolValidationError for invalid input.")


def test_gateway_executes_file_read_tool() -> None:
    """Authorized and valid tool calls should execute successfully."""
    gateway = get_tool_gateway()
    result = gateway.invoke(
        ToolCall(name="file.read", arguments={"path": "README.md"}),
        make_context(scopes=["workspace.read"]),
    )
    assert result.tool_name == "file.read"
    assert "RA_OS" in result.response_payload["content"]
