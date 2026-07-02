"""In-memory registry for tool definitions and their handlers."""

from collections.abc import Callable

from app.tools.contracts import ToolDefinitionContract, ToolExecutionContext, ToolInvocationResult
from app.tools.exceptions import ToolValidationError

ToolCallable = Callable[[dict, ToolExecutionContext], ToolInvocationResult]


class ToolRegistry:
    """Store tool metadata alongside executable callables."""

    def __init__(self) -> None:
        self._definitions: dict[str, ToolDefinitionContract] = {}
        self._handlers: dict[str, ToolCallable] = {}

    def register(self, definition: ToolDefinitionContract, handler: ToolCallable) -> None:
        """Register a tool definition and its runtime handler."""
        if not definition.input_schema or not definition.output_schema:
            raise ToolValidationError("Tool definition requires both input_schema and output_schema.")
        if not definition.permission_scope:
            raise ToolValidationError("Tool definition requires a permission scope.")
        self._definitions[definition.name] = definition
        self._handlers[definition.name] = handler

    def definition(self, tool_name: str) -> ToolDefinitionContract:
        """Return a registered tool definition or raise for unknown names."""
        if tool_name not in self._definitions:
            raise ToolValidationError(f"Unknown tool '{tool_name}'.")
        return self._definitions[tool_name]

    def handler(self, tool_name: str) -> ToolCallable:
        """Return the executable callable for a registered tool."""
        if tool_name not in self._handlers:
            raise ToolValidationError(f"Unknown tool '{tool_name}'.")
        return self._handlers[tool_name]

    def definitions(self) -> list[ToolDefinitionContract]:
        """Return all registered tool definitions in insertion order."""
        return list(self._definitions.values())
