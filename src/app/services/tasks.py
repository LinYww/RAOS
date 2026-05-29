from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import TaskEventType, TaskLifecycleState
from app.models.task import Task, TaskAttempt, TaskEvent
from app.models.tool import ToolInvocation
from app.repositories.agents import AgentRepository
from app.repositories.tasks import TaskRepository
from app.repositories.tools import ToolRepository
from app.runtime.transitions import cancel_task as cancel_transition
from app.runtime.transitions import pause_task as pause_transition
from app.runtime.transitions import resume_task as resume_transition
from app.runtime.types import RuntimeExecutionInput
from app.schemas.task import TaskCreateRequest, TaskResumeRequest, TaskRetryRequest
from app.services.runtime import build_runtime
from app.tools.bootstrap import get_tool_gateway
from app.tools.contracts import ToolExecutionContext
from app.tools.exceptions import ToolValidationError
from app.tools.gateway import ToolCall, ToolExecutionRecord


class TaskService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._tasks = TaskRepository(session)
        self._agents = AgentRepository(session)
        self._tools = ToolRepository(session)

    def submit(self, payload: TaskCreateRequest) -> Task:
        agent = self._agents.get(str(payload.agent_id))
        if agent is None:
            raise ValueError("Agent not found.")

        task = self._tasks.create_task(
            Task(
                agent_id=str(payload.agent_id),
                input=payload.model_dump(mode="json"),
                trigger_source=payload.trigger_source,
                priority=payload.priority,
                state=TaskLifecycleState.CREATED.value,
            )
        )
        attempt = self._tasks.create_attempt(
            TaskAttempt(
                task_id=task.id,
                attempt_number=1,
                max_steps=payload.max_steps,
                timeout_seconds=payload.timeout_seconds,
                state=TaskLifecycleState.CREATED.value,
            )
        )
        self._append_event(task.id, attempt.id, TaskEventType.CREATED, {"state": TaskLifecycleState.CREATED.value})
        self._session.commit()
        self.execute_attempt(task.id, attempt.id)
        return self._tasks.get_task(task.id) or task

    def execute_attempt(self, task_id: str, attempt_id: str) -> Task:
        task = self._tasks.get_task(task_id)
        attempt = self._tasks.get_attempt(attempt_id)
        if task is None or attempt is None:
            raise ValueError("Task attempt not found.")
        agent = self._agents.get(task.agent_id)
        if agent is None:
            raise ValueError("Agent not found for task.")

        payload = task.input
        runtime = build_runtime()
        runtime_input = RuntimeExecutionInput(
            task_id=task.id,
            attempt_id=attempt.id,
            agent_id=agent.id,
            system_prompt=agent.system_prompt,
            messages=_normalize_messages(payload),
            max_steps=attempt.max_steps,
            timeout_seconds=attempt.timeout_seconds,
            metadata={
                "allowed_scopes": payload.get("allowed_scopes", []),
                "tools": get_tool_gateway().describe_tools(),
            },
        )

        # The runtime emits its own lifecycle events, but the persistent task row
        # must be updated eagerly so external readers observe a running attempt.
        task.state = TaskLifecycleState.RUNNING.value
        task.updated_at = datetime.now(UTC)
        attempt.state = TaskLifecycleState.RUNNING.value
        attempt.started_at = attempt.started_at or datetime.now(UTC)
        self._append_event(task.id, attempt.id, TaskEventType.STATE_CHANGED, {"state": TaskLifecycleState.RUNNING.value})
        self._session.commit()

        result = runtime.run(runtime_input, tool_executor=self._execute_tool_call)

        task.state = result.state.value
        task.failure_reason = result.failure_reason.value if result.failure_reason else None
        task.terminal_summary = result.output_text or task.terminal_summary
        task.updated_at = datetime.now(UTC)
        attempt.state = result.state.value
        attempt.step_count = result.step_count
        attempt.failure_reason = result.failure_reason.value if result.failure_reason else None
        if result.state in {
            TaskLifecycleState.SUCCEEDED,
            TaskLifecycleState.FAILED,
            TaskLifecycleState.CANCELLED,
        }:
            attempt.finished_at = datetime.now(UTC)

        step_index = result.checkpoint.get("checkpoint_metadata", {}).get("step_index", result.step_count)
        # Only non-core checkpoint fields become pending state; the canonical
        # transcript and metadata stay inside the snapshot payload itself.
        pending_state = {
            key: value
            for key, value in result.checkpoint.items()
            if key not in {"task_id", "attempt_id", "agent_id", "messages", "metadata", "checkpoint_metadata"}
        }
        self._tasks.upsert_checkpoint(
            attempt_id=attempt.id,
            step_index=step_index,
            snapshot=result.checkpoint,
            pending_state=pending_state,
        )
        for event in result.events:
            self._append_event(task.id, attempt.id, TaskEventType(event.event_type), event.payload)
        self._session.commit()
        return task

    def list(self, *, state: str | None = None) -> list[Task]:
        return self._tasks.list_tasks(state=state)

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get_task(task_id)

    def events(self, task_id: str) -> list[TaskEvent]:
        return self._tasks.list_events(task_id)

    def pause(self, task_id: str) -> Task:
        return self._apply_transition(task_id, action="pause")

    def resume(self, task_id: str, payload: TaskResumeRequest | None = None) -> Task:
        task = self._apply_transition(task_id, action="resume", reason=payload.reason if payload else None)
        latest_attempt = self._tasks.latest_attempt_for_task(task_id)
        if latest_attempt:
            self.execute_attempt(task_id, latest_attempt.id)
        refreshed = self._tasks.get_task(task_id)
        return refreshed or task

    def cancel(self, task_id: str) -> Task:
        return self._apply_transition(task_id, action="cancel")

    def retry(self, task_id: str, payload: TaskRetryRequest) -> Task:
        task = self._tasks.get_task(task_id)
        if task is None:
            raise ValueError("Task not found.")
        latest_attempt = self._tasks.latest_attempt_for_task(task_id)
        next_attempt = self._tasks.create_attempt(
            TaskAttempt(
                task_id=task.id,
                attempt_number=self._tasks.next_attempt_number(task.id),
                max_steps=latest_attempt.max_steps if latest_attempt else 32,
                timeout_seconds=latest_attempt.timeout_seconds if latest_attempt else 300,
                state=TaskLifecycleState.CREATED.value,
            )
        )
        task.state = TaskLifecycleState.CREATED.value
        task.failure_reason = None
        self._append_event(
            task.id,
            next_attempt.id,
            TaskEventType.OPERATOR_ACTION,
            {"action": "retry", "reason": payload.reason},
        )
        self._session.commit()
        self.execute_attempt(task.id, next_attempt.id)
        refreshed = self._tasks.get_task(task.id)
        return refreshed or task

    def _apply_transition(self, task_id: str, *, action: str, reason: str | None = None) -> Task:
        task = self._tasks.get_task(task_id)
        latest_attempt = self._tasks.latest_attempt_for_task(task_id)
        if task is None or latest_attempt is None:
            raise ValueError("Task not found.")
        checkpoint = self._tasks.latest_checkpoint(latest_attempt.id)
        snapshot = checkpoint.snapshot if checkpoint else {}
        current_state = TaskLifecycleState(task.state)
        if action == "pause":
            result = pause_transition(current_state=current_state, checkpoint=snapshot)
        elif action == "resume":
            result = resume_transition(current_state=current_state, checkpoint=snapshot)
        elif action == "cancel":
            result = cancel_transition(current_state=current_state, checkpoint=snapshot)
        else:
            raise ValueError(f"Unsupported action '{action}'.")

        task.state = result.state.value
        task.updated_at = datetime.now(UTC)
        if result.failure_reason:
            task.failure_reason = result.failure_reason.value
        latest_attempt.state = result.state.value
        # Keep the latest checkpoint aligned with operator actions so a later resume
        # or audit sees the exact control-plane mutation that was applied.
        self._tasks.upsert_checkpoint(
            attempt_id=latest_attempt.id,
            step_index=snapshot.get("checkpoint_metadata", {}).get("step_index", 0),
            snapshot=result.checkpoint,
            pending_state={k: v for k, v in result.checkpoint.items() if k not in {"messages", "checkpoint_metadata"}},
        )
        payload_data = dict(result.event.payload)
        if reason:
            payload_data["reason"] = reason
        self._append_event(task.id, latest_attempt.id, TaskEventType.OPERATOR_ACTION, payload_data)
        self._session.commit()
        return task

    def _execute_tool_call(self, execution_input: RuntimeExecutionInput, tool_call: ToolCall) -> ToolExecutionRecord:
        gateway = get_tool_gateway()
        context = ToolExecutionContext(
            task_id=execution_input.task_id,
            attempt_id=execution_input.attempt_id,
            allowed_scopes=set(execution_input.metadata.get("allowed_scopes", [])),
            audit_context={},
        )
        definition = self._tools.get_by_name(tool_call.name)
        if definition is None:
            raise ToolValidationError(f"Tool '{tool_call.name}' is not registered.")
        record = gateway.invoke(tool_call, context)
        invocation_status = "completed"
        invocation = self._tools.create_invocation(
            ToolInvocation(
                tool_definition_id=definition.id,
                task_attempt_id=execution_input.attempt_id,
                status=invocation_status,
                request_payload=record.request_payload,
                response_payload=record.response_payload,
            )
        )
        self._session.commit()
        return record

    def _append_event(self, task_id: str, attempt_id: str | None, event_type: TaskEventType, payload: dict) -> TaskEvent:
        event = TaskEvent(
            task_id=task_id,
            task_attempt_id=attempt_id,
            sequence_number=self._tasks.next_event_sequence(task_id),
            event_type=event_type.value,
            payload=payload,
        )
        return self._tasks.add_event(event)


def _normalize_messages(payload: dict) -> list[dict]:
    if payload.get("messages"):
        return payload["messages"]
    prompt = payload.get("prompt")
    if prompt:
        return [{"role": "user", "content": prompt}]
    # Fallback keeps ad-hoc payloads debuggable during bootstrap by ensuring the
    # runtime always receives at least one user message.
    return [{"role": "user", "content": str(payload.get("input", payload))}]
