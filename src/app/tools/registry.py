from collections.abc import Callable

from app.tools.contracts import ToolDefinitionContract, ToolExecutionContext, ToolInvocationResult
from app.tools.exceptions import ToolValidationError

ToolCallable = Callable[[dict, ToolExecutionContext], ToolInvocationResult]


class ToolRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, ToolDefinitionContract] = {}
        self._handlers: dict[str, ToolCallable] = {}

    def register(self, definition: ToolDefinitionContract, handler: ToolCallable) -> None:
        if not definition.input_schema or not definition.output_schema:
            raise ToolValidationError("Tool definition requires both input_schema and output_schema.")
        if not definition.permission_scope:
            raise ToolValidationError("Tool definition requires a permission scope.")
        self._definitions[definition.name] = definition
        self._handlers[definition.name] = handler

    def definition(self, tool_name: str) -> ToolDefinitionContract:
        if tool_name not in self._definitions:
            raise ToolValidationError(f"Unknown tool '{tool_name}'.")
        return self._definitions[tool_name]

    def handler(self, tool_name: str) -> ToolCallable:
        if tool_name not in self._handlers:
            raise ToolValidationError(f"Unknown tool '{tool_name}'.")
        return self._handlers[tool_name]

    def definitions(self) -> list[ToolDefinitionContract]:
        return list(self._definitions.values())
