"""Custom exceptions raised by the tool subsystem."""

class ToolValidationError(ValueError):
    """Raised when a tool definition or payload violates the declared contract."""


class ToolPermissionError(PermissionError):
    """Raised when a tool call is outside the caller's approved scopes."""


class ToolExecutionError(RuntimeError):
    """Raised when tool execution fails after validation and authorization."""
