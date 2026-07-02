"""Authorization and validation gateway for runtime tool calls."""

from dataclasses import dataclass

from app.tools.contracts import ToolExecutionContext
from app.tools.exceptions import ToolPermissionError
from app.tools.registry import ToolRegistry
from app.tools.schema import validate_payload


@dataclass(slots=True)
class ToolCall:
    """Tool request emitted by the model layer."""

    name: str
    arguments: dict


@dataclass(slots=True)
class ToolExecutionRecord:
    """Persistable record of a completed tool invocation."""

    tool_name: str
    request_payload: dict
    response_payload: dict
    audit_fields: dict


class ToolGateway:
    """Validate, authorize, and dispatch tool calls through the registry."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def describe_tools(self) -> list[dict]:
        """Expose model-facing tool metadata in a provider-neutral shape."""
        return [
            {
                "name": item.name,
                "description": item.description,
                "input_schema": item.input_schema,
                "output_schema": item.output_schema,
                "permission_scope": item.permission_scope,
            }
            for item in self._registry.definitions()
        ]

    def invoke(self, tool_call: ToolCall, context: ToolExecutionContext) -> ToolExecutionRecord:
        """Execute a single tool call after scope and schema checks pass."""
        definition = self._registry.definition(tool_call.name)
        if definition.permission_scope not in context.allowed_scopes:
            raise ToolPermissionError(
                f"Tool '{tool_call.name}' requires scope '{definition.permission_scope}'."
            )
        # Validate both sides of the tool contract so provider responses cannot
        # silently persist malformed payloads into task history.
        validate_payload(definition.input_schema, tool_call.arguments, label="tool input")
        result = self._registry.handler(tool_call.name)(tool_call.arguments, context)
        validate_payload(definition.output_schema, result.payload, label="tool output")
        return ToolExecutionRecord(
            tool_name=tool_call.name,
            request_payload=tool_call.arguments,
            response_payload=result.payload,
            audit_fields=result.audit_fields,
        )
