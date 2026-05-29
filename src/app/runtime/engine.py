from time import monotonic
from dataclasses import asdict

from app.models.enums import FailureReasonCode, TaskEventType, TaskLifecycleState
from app.providers.base import ModelProvider, ModelProviderError, ModelRequest
from app.runtime.types import (
    RuntimeCheckpointMetadata,
    RuntimeEventRecord,
    RuntimeExecutionInput,
    RuntimeExecutionOutput,
)
from app.tools.exceptions import ToolExecutionError, ToolPermissionError, ToolValidationError
from app.tools.gateway import ToolCall


class SingleAgentRuntime:
    """Bounded single-agent execution loop for the MVP runtime."""

    def __init__(self, provider: ModelProvider) -> None:
        self._provider = provider

    def run(self, execution_input: RuntimeExecutionInput, tool_executor=None) -> RuntimeExecutionOutput:
        started_at = monotonic()
        events: list[RuntimeEventRecord] = []
        messages = list(execution_input.messages)
        step_count = 0
        # Checkpoints always carry the full conversational state so the service layer
        # can persist and resume from any operator-visible transition.
        checkpoint = self._checkpoint_payload(execution_input, step_index=0, messages=messages)

        self._append_event(events, TaskEventType.CREATED, {"state": TaskLifecycleState.CREATED})
        self._append_event(events, TaskEventType.STATE_CHANGED, {"state": TaskLifecycleState.QUEUED})
        self._append_event(events, TaskEventType.STATE_CHANGED, {"state": TaskLifecycleState.RUNNING})

        while True:
            if step_count >= execution_input.max_steps:
                return self._terminal_output(
                    events=events,
                    state=TaskLifecycleState.FAILED,
                    failure_reason=FailureReasonCode.STEP_LIMIT_EXCEEDED,
                    step_count=step_count,
                    output_text="",
                    checkpoint=checkpoint,
                )

            if monotonic() - started_at > execution_input.timeout_seconds:
                return self._terminal_output(
                    events=events,
                    state=TaskLifecycleState.FAILED,
                    failure_reason=FailureReasonCode.TIMEOUT_EXCEEDED,
                    step_count=step_count,
                    output_text="",
                    checkpoint=checkpoint,
                )

            step_count += 1
            self._append_event(
                events,
                TaskEventType.MODEL_REQUESTED,
                {"step_index": step_count, "message_count": len(messages)},
            )

            try:
                response = self._provider.generate(
                    ModelRequest(
                        messages=messages,
                        system_prompt=execution_input.system_prompt,
                        tools=execution_input.metadata.get("tools", []),
                        metadata=execution_input.metadata,
                    )
                )
            except ModelProviderError as exc:
                checkpoint = self._checkpoint_payload(execution_input, step_index=step_count, messages=messages)
                return self._terminal_output(
                    events=events,
                    state=TaskLifecycleState.FAILED,
                    failure_reason=FailureReasonCode.MODEL_PROVIDER_ERROR,
                    step_count=step_count,
                    output_text=str(exc),
                    checkpoint=checkpoint,
                )

            messages.append({"role": "assistant", "content": response.output_text})
            checkpoint = self._checkpoint_payload(execution_input, step_index=step_count, messages=messages)
            self._append_event(
                events,
                TaskEventType.MODEL_RESPONDED,
                {
                    "step_index": step_count,
                    "stop_reason": response.stop_reason,
                    "tool_call_count": len(response.tool_calls),
                    "output_text": response.output_text,
                },
            )

            if response.tool_calls:
                if tool_executor is None:
                    # Returning WAITING_TOOL lets a higher-level orchestrator approve or
                    # execute tool calls out of band without losing model output.
                    self._append_event(
                        events,
                        TaskEventType.STATE_CHANGED,
                        {"state": TaskLifecycleState.WAITING_TOOL, "step_index": step_count},
                    )
                    return RuntimeExecutionOutput(
                        state=TaskLifecycleState.WAITING_TOOL,
                        failure_reason=None,
                        step_count=step_count,
                        output_text=response.output_text,
                        events=events,
                        checkpoint=checkpoint | {"pending_tool_calls": response.tool_calls},
                    )

                try:
                    for raw_tool_call in response.tool_calls:
                        tool_name = raw_tool_call.get("name", "")
                        arguments = raw_tool_call.get("arguments", {})
                        if isinstance(arguments, str):
                            # The MVP only accepts structured JSON-like tool inputs.
                            # Stringified arguments are treated as invalid and collapse to
                            # an empty payload so schema validation can reject them.
                            arguments = {}
                        self._append_event(
                            events,
                            TaskEventType.TOOL_REQUESTED,
                            {"step_index": step_count, "tool_name": tool_name},
                        )
                        tool_result = tool_executor(
                            execution_input,
                            ToolCall(name=tool_name, arguments=arguments),
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "name": tool_result.tool_name,
                                "content": str(tool_result.response_payload),
                            }
                        )
                        checkpoint = self._checkpoint_payload(
                            execution_input,
                            step_index=step_count,
                            messages=messages,
                        )
                        self._append_event(
                            events,
                            TaskEventType.TOOL_COMPLETED,
                            {
                                "step_index": step_count,
                                "tool_name": tool_result.tool_name,
                                "response_payload": tool_result.response_payload,
                            },
                        )
                    continue
                except ToolPermissionError:
                    failure_reason = FailureReasonCode.TOOL_PERMISSION_DENIED
                except ToolValidationError:
                    failure_reason = FailureReasonCode.TOOL_VALIDATION_FAILED
                except ToolExecutionError:
                    failure_reason = FailureReasonCode.UNKNOWN

                return self._terminal_output(
                    events=events,
                    state=TaskLifecycleState.FAILED,
                    failure_reason=failure_reason,
                    step_count=step_count,
                    output_text=response.output_text,
                    checkpoint=checkpoint | {"pending_tool_calls": response.tool_calls},
                )

            if response.stop_reason == "waiting_user":
                self._append_event(
                    events,
                    TaskEventType.STATE_CHANGED,
                    {"state": TaskLifecycleState.WAITING_USER, "step_index": step_count},
                )
                return RuntimeExecutionOutput(
                    state=TaskLifecycleState.WAITING_USER,
                    failure_reason=None,
                    step_count=step_count,
                    output_text=response.output_text,
                    events=events,
                    checkpoint=checkpoint,
                )

            if self._is_terminal_stop(response.stop_reason, response.output_text):
                return self._terminal_output(
                    events=events,
                    state=TaskLifecycleState.SUCCEEDED,
                    failure_reason=None,
                    step_count=step_count,
                    output_text=response.output_text,
                    checkpoint=checkpoint,
                )

    def _append_event(self, events: list[RuntimeEventRecord], event_type: TaskEventType, payload: dict) -> None:
        events.append(
            RuntimeEventRecord(
                sequence_number=len(events) + 1,
                event_type=event_type.value,
                payload=payload,
            )
        )

    def _terminal_output(
        self,
        *,
        events: list[RuntimeEventRecord],
        state: TaskLifecycleState,
        failure_reason: FailureReasonCode | None,
        step_count: int,
        output_text: str,
        checkpoint: dict,
    ) -> RuntimeExecutionOutput:
        self._append_event(
            events,
            TaskEventType.TERMINAL,
            {
                "state": state.value,
                "failure_reason": failure_reason.value if failure_reason else None,
                "step_count": step_count,
            },
        )
        return RuntimeExecutionOutput(
            state=state,
            failure_reason=failure_reason,
            step_count=step_count,
            output_text=output_text,
            events=events,
            checkpoint=checkpoint,
        )

    def _checkpoint_payload(
        self,
        execution_input: RuntimeExecutionInput,
        *,
        step_index: int,
        messages: list[dict],
    ) -> dict:
        # The snapshot format is intentionally plain dict data so it can be stored
        # directly in the database and reused by operator transitions.
        checkpoint_metadata = RuntimeCheckpointMetadata(
            step_index=step_index,
            max_steps=execution_input.max_steps,
            timeout_seconds=execution_input.timeout_seconds,
        )
        return {
            "task_id": execution_input.task_id,
            "attempt_id": execution_input.attempt_id,
            "agent_id": execution_input.agent_id,
            "messages": messages,
            "metadata": execution_input.metadata,
            "checkpoint_metadata": asdict(checkpoint_metadata),
        }

    def _is_terminal_stop(self, stop_reason: str | None, output_text: str) -> bool:
        if stop_reason in {None, "stop", "completed"}:
            # Hosted providers are inconsistent here; treat a plain text answer with
            # no further action requested as a successful terminal turn.
            return bool(output_text)
        return stop_reason in {"succeeded", "end_turn"}
