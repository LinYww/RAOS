from dataclasses import dataclass

from pydantic import BaseModel, Field


class ToolDefinitionContract(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1)
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    permission_scope: str = Field(min_length=1, max_length=120)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    audit_fields: dict = Field(default_factory=dict)


@dataclass(slots=True)
class ToolExecutionContext:
    task_id: str
    attempt_id: str
    allowed_scopes: set[str]
    audit_context: dict


@dataclass(slots=True)
class ToolInvocationResult:
    payload: dict
    audit_fields: dict
