"""ORM models for tasks, task attempts, and task events."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import FailureReasonCode, TaskEventType, TaskLifecycleState


class Task(Base):
    """Top-level task row visible to operators and APIs."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    state: Mapped[TaskLifecycleState] = mapped_column(
        String(40), nullable=False, default=TaskLifecycleState.CREATED
    )
    trigger_source: Mapped[str] = mapped_column(String(100), nullable=False, default="api")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    terminal_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[FailureReasonCode | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class TaskAttempt(Base):
    """One execution attempt belonging to a task."""

    __tablename__ = "task_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    state: Mapped[TaskLifecycleState] = mapped_column(
        String(40), nullable=False, default=TaskLifecycleState.CREATED
    )
    step_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=32)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    failure_reason: Mapped[FailureReasonCode | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class TaskEvent(Base):
    """Immutable event row describing task lifecycle activity."""

    __tablename__ = "task_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    task_attempt_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("task_attempts.id"), nullable=True, index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[TaskEventType] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
