from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.checkpoint import Checkpoint
from app.models.task import Task, TaskAttempt, TaskEvent


class TaskRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_task(self, task: Task) -> Task:
        self._session.add(task)
        self._session.flush()
        return task

    def create_attempt(self, attempt: TaskAttempt) -> TaskAttempt:
        self._session.add(attempt)
        self._session.flush()
        return attempt

    def add_event(self, event: TaskEvent) -> TaskEvent:
        self._session.add(event)
        self._session.flush()
        return event

    def upsert_checkpoint(self, *, attempt_id: str, step_index: int, snapshot: dict, pending_state: dict) -> Checkpoint:
        checkpoint = self.latest_checkpoint(attempt_id)
        if checkpoint is None:
            checkpoint = Checkpoint(
                task_attempt_id=attempt_id,
                step_index=step_index,
                snapshot=snapshot,
                pending_state=pending_state,
            )
            self._session.add(checkpoint)
        else:
            checkpoint.step_index = step_index
            checkpoint.snapshot = snapshot
            checkpoint.pending_state = pending_state
        self._session.flush()
        return checkpoint

    def latest_checkpoint(self, attempt_id: str) -> Checkpoint | None:
        query = (
            select(Checkpoint)
            .where(Checkpoint.task_attempt_id == attempt_id)
            .order_by(Checkpoint.created_at.desc())
        )
        return self._session.scalars(query).first()

    def get_task(self, task_id: str) -> Task | None:
        return self._session.get(Task, task_id)

    def get_attempt(self, attempt_id: str) -> TaskAttempt | None:
        return self._session.get(TaskAttempt, attempt_id)

    def latest_attempt_for_task(self, task_id: str) -> TaskAttempt | None:
        query = (
            select(TaskAttempt)
            .where(TaskAttempt.task_id == task_id)
            .order_by(TaskAttempt.attempt_number.desc(), TaskAttempt.created_at.desc())
        )
        return self._session.scalars(query).first()

    def list_tasks(self, *, state: str | None = None) -> list[Task]:
        query = select(Task).order_by(Task.updated_at.desc(), Task.created_at.desc())
        if state:
            query = query.where(Task.state == state)
        return list(self._session.scalars(query))

    def list_events(self, task_id: str) -> list[TaskEvent]:
        query = (
            select(TaskEvent)
            .where(TaskEvent.task_id == task_id)
            .order_by(TaskEvent.sequence_number.asc(), TaskEvent.created_at.asc())
        )
        return list(self._session.scalars(query))

    def next_attempt_number(self, task_id: str) -> int:
        query = select(func.max(TaskAttempt.attempt_number)).where(TaskAttempt.task_id == task_id)
        current = self._session.scalar(query)
        return (current or 0) + 1

    def next_event_sequence(self, task_id: str) -> int:
        query = select(func.max(TaskEvent.sequence_number)).where(TaskEvent.task_id == task_id)
        current = self._session.scalar(query)
        return (current or 0) + 1
