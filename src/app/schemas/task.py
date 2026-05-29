from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import FailureReasonCode, TaskEventType, TaskLifecycleState


class ORMResponseModel(BaseModel):
    model_config = {"from_attributes": True}


class TaskMessage(BaseModel):
    role: str
    content: str


class TaskCreateRequest(BaseModel):
    agent_id: UUID
    prompt: str | None = None
    messages: list[TaskMessage] = Field(default_factory=list)
    input: dict = Field(default_factory=dict)
    allowed_scopes: list[str] = Field(default_factory=list)
    max_steps: int = Field(default=32, ge=1, le=256)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    trigger_source: str = Field(default="api", min_length=1, max_length=100)
    priority: int = 0


class TaskRetryRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class TaskResumeRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class TaskDetailResponse(ORMResponseModel):
    id: UUID | str
    agent_id: UUID | str
    state: TaskLifecycleState
    input: dict
    trigger_source: str
    priority: int
    failure_reason: FailureReasonCode | None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskDetailResponse]


class TaskEventResponse(ORMResponseModel):
    id: UUID | str
    task_id: UUID | str
    task_attempt_id: UUID | str | None = None
    sequence_number: int
    event_type: TaskEventType
    payload: dict
    created_at: datetime


class TaskEventListResponse(BaseModel):
    task_id: UUID | str
    items: list[TaskEventResponse]


class TaskActionResponse(BaseModel):
    task_id: UUID | str
    accepted: bool
    action: str
    reason: str | None = None
