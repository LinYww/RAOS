"""Shared enum types used across persistence, runtime, and API layers."""

from enum import Enum


class TaskLifecycleState(str, Enum):
    """Canonical lifecycle states a task can occupy."""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_TOOL = "waiting_tool"
    WAITING_USER = "waiting_user"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FailureReasonCode(str, Enum):
    """Normalized terminal and suspension failure codes."""

    STEP_LIMIT_EXCEEDED = "step_limit_exceeded"
    TIMEOUT_EXCEEDED = "timeout_exceeded"
    TOOL_VALIDATION_FAILED = "tool_validation_failed"
    TOOL_PERMISSION_DENIED = "tool_permission_denied"
    MODEL_PROVIDER_ERROR = "model_provider_error"
    OPERATOR_CANCELLED = "operator_cancelled"
    UNKNOWN = "unknown"


class TaskEventType(str, Enum):
    """Structured event types emitted during task execution."""

    CREATED = "created"
    STATE_CHANGED = "state_changed"
    MODEL_REQUESTED = "model_requested"
    MODEL_RESPONDED = "model_responded"
    TOOL_REQUESTED = "tool_requested"
    TOOL_COMPLETED = "tool_completed"
    OPERATOR_ACTION = "operator_action"
    TERMINAL = "terminal"
