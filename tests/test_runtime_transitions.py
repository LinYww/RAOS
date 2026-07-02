"""Tests for operator-driven runtime state transitions."""

from app.models.enums import FailureReasonCode, TaskLifecycleState
from app.runtime.transitions import cancel_task, pause_task, resume_task


def make_checkpoint() -> dict:
    """Build a representative checkpoint payload for transition tests."""
    return {
        "task_id": "task-1",
        "attempt_id": "attempt-1",
        "checkpoint_metadata": {"step_index": 2, "max_steps": 8, "timeout_seconds": 60},
    }


def test_pause_moves_running_task_to_waiting_user() -> None:
    """Pausing should move an active task into a user-waiting state."""
    result = pause_task(current_state=TaskLifecycleState.RUNNING, checkpoint=make_checkpoint())
    assert result.state == TaskLifecycleState.WAITING_USER
    assert result.checkpoint["pause_reason"] == "operator_pause"
    assert result.checkpoint["resume_from_state"] == TaskLifecycleState.RUNNING.value


def test_resume_moves_waiting_user_task_back_to_queue() -> None:
    """Resuming should clear the pause marker and requeue the task."""
    paused = pause_task(current_state=TaskLifecycleState.RUNNING, checkpoint=make_checkpoint())
    result = resume_task(current_state=paused.state, checkpoint=paused.checkpoint)
    assert result.state == TaskLifecycleState.QUEUED
    assert result.checkpoint["resumed_from_state"] == TaskLifecycleState.RUNNING.value


def test_cancel_marks_task_cancelled_and_preserves_checkpoint() -> None:
    """Cancellation should preserve the source state for auditing."""
    result = cancel_task(current_state=TaskLifecycleState.WAITING_TOOL, checkpoint=make_checkpoint())
    assert result.state == TaskLifecycleState.CANCELLED
    assert result.failure_reason == FailureReasonCode.OPERATOR_CANCELLED
    assert result.checkpoint["cancelled_from_state"] == TaskLifecycleState.WAITING_TOOL.value
