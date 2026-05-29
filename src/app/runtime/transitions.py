from dataclasses import dataclass

from app.models.enums import FailureReasonCode, TaskEventType, TaskLifecycleState
from app.runtime.types import RuntimeEventRecord


@dataclass(slots=True)
class RuntimeTransitionResult:
    state: TaskLifecycleState
    checkpoint: dict
    event: RuntimeEventRecord
    failure_reason: FailureReasonCode | None = None


def pause_task(*, current_state: TaskLifecycleState, checkpoint: dict) -> RuntimeTransitionResult:
    _ensure_state(
        action="pause",
        current_state=current_state,
        allowed_states={
            TaskLifecycleState.CREATED,
            TaskLifecycleState.QUEUED,
            TaskLifecycleState.RUNNING,
            TaskLifecycleState.WAITING_TOOL,
        },
    )
    next_checkpoint = {
        **checkpoint,
        # Resume relies on this marker to distinguish an operator pause from a model-
        # initiated WAITING_USER turn.
        "pause_reason": "operator_pause",
        "resume_from_state": current_state.value,
    }
    return RuntimeTransitionResult(
        state=TaskLifecycleState.WAITING_USER,
        checkpoint=next_checkpoint,
        event=_operator_event("pause", from_state=current_state, to_state=TaskLifecycleState.WAITING_USER),
    )


def resume_task(*, current_state: TaskLifecycleState, checkpoint: dict) -> RuntimeTransitionResult:
    _ensure_state(
        action="resume",
        current_state=current_state,
        allowed_states={TaskLifecycleState.WAITING_USER},
    )
    resume_from_state = checkpoint.get("resume_from_state", TaskLifecycleState.RUNNING.value)
    # Clear the active pause marker but keep a breadcrumb for later audits/debugging.
    next_checkpoint = {k: v for k, v in checkpoint.items() if k != "pause_reason"}
    next_checkpoint["resumed_from_state"] = resume_from_state
    return RuntimeTransitionResult(
        state=TaskLifecycleState.QUEUED,
        checkpoint=next_checkpoint,
        event=_operator_event("resume", from_state=current_state, to_state=TaskLifecycleState.QUEUED),
    )


def cancel_task(*, current_state: TaskLifecycleState, checkpoint: dict) -> RuntimeTransitionResult:
    _ensure_state(
        action="cancel",
        current_state=current_state,
        allowed_states={
            TaskLifecycleState.CREATED,
            TaskLifecycleState.QUEUED,
            TaskLifecycleState.RUNNING,
            TaskLifecycleState.WAITING_TOOL,
            TaskLifecycleState.WAITING_USER,
        },
    )
    next_checkpoint = {
        **checkpoint,
        "cancelled_from_state": current_state.value,
        "cancel_reason": FailureReasonCode.OPERATOR_CANCELLED.value,
    }
    return RuntimeTransitionResult(
        state=TaskLifecycleState.CANCELLED,
        failure_reason=FailureReasonCode.OPERATOR_CANCELLED,
        checkpoint=next_checkpoint,
        event=_operator_event("cancel", from_state=current_state, to_state=TaskLifecycleState.CANCELLED),
    )


def _ensure_state(
    *,
    action: str,
    current_state: TaskLifecycleState,
    allowed_states: set[TaskLifecycleState],
) -> None:
    if current_state not in allowed_states:
        raise ValueError(f"Cannot {action} task from state {current_state.value}.")


def _operator_event(
    action: str,
    *,
    from_state: TaskLifecycleState,
    to_state: TaskLifecycleState,
) -> RuntimeEventRecord:
    return RuntimeEventRecord(
        sequence_number=1,
        event_type=TaskEventType.OPERATOR_ACTION.value,
        payload={
            "action": action,
            "from_state": from_state.value,
            "to_state": to_state.value,
        },
    )
