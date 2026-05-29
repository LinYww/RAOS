from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.models.enums import FailureReasonCode, TaskLifecycleState


@dataclass(slots=True)
class RuntimeCheckpointMetadata:
    step_index: int
    max_steps: int
    timeout_seconds: int


@dataclass(slots=True)
class RuntimeResult:
    state: TaskLifecycleState
    failure_reason: FailureReasonCode | None = None


@dataclass(slots=True)
class RuntimeExecutionInput:
    task_id: str
    attempt_id: str
    agent_id: str
    system_prompt: str
    messages: list[dict]
    max_steps: int
    timeout_seconds: int
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class RuntimeEventRecord:
    sequence_number: int
    event_type: str
    payload: dict
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class RuntimeExecutionOutput:
    state: TaskLifecycleState
    failure_reason: FailureReasonCode | None
    step_count: int
    output_text: str
    events: list[RuntimeEventRecord]
    checkpoint: dict
