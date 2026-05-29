class ToolValidationError(ValueError):
    """Raised when a tool definition or tool invocation payload is invalid."""


class ToolPermissionError(PermissionError):
    """Raised when a tool invocation is not authorized."""


class ToolExecutionError(RuntimeError):
    """Raised when tool execution fails after validation and authorization."""
