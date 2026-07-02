"""Typed contracts shared across tool registration and invocation."""

from dataclasses import dataclass

from pydantic import BaseModel, Field


class ToolDefinitionContract(BaseModel):
    """Validated description of a tool's callable surface and policy."""

    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1)
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    permission_scope: str = Field(min_length=1, max_length=120)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    audit_fields: dict = Field(default_factory=dict)


@dataclass(slots=True)
class ToolExecutionContext:
    """Runtime context passed to a tool invocation."""

    task_id: str
    attempt_id: str
    allowed_scopes: set[str]
    audit_context: dict


@dataclass(slots=True)
class ToolInvocationResult:
    """Normalized tool result captured in events and audit logs."""

    payload: dict
    audit_fields: dict
