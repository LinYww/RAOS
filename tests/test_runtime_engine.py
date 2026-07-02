"""Tests covering the single-agent runtime loop."""

from app.models.enums import FailureReasonCode, TaskLifecycleState
from app.providers.base import ModelProvider, ModelProviderError, ModelRequest, ModelResponse
from app.runtime.engine import SingleAgentRuntime
from app.runtime.types import RuntimeExecutionInput


class StaticProvider(ModelProvider):
    """Provider test double that returns a predefined response sequence."""

    def __init__(self, responses: list[ModelResponse]) -> None:
        self._responses = responses

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Return the next canned response."""
        return self._responses.pop(0)


class ErrorProvider(ModelProvider):
    """Provider test double that always raises a provider error."""

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Simulate a transport or provider-side failure."""
        raise ModelProviderError("provider unavailable")


def make_input(max_steps: int = 4, timeout_seconds: int = 30) -> RuntimeExecutionInput:
    """Build a minimal runtime input used across runtime tests."""
    return RuntimeExecutionInput(
        task_id="task-1",
        attempt_id="attempt-1",
        agent_id="agent-1",
        system_prompt="You are the runtime agent.",
        messages=[{"role": "user", "content": "say hello"}],
        max_steps=max_steps,
        timeout_seconds=timeout_seconds,
        metadata={},
    )


def test_runtime_succeeds_on_terminal_provider_response() -> None:
    """A terminal provider response should mark the task attempt successful."""
    runtime = SingleAgentRuntime(
        StaticProvider([ModelResponse(output_text="hello", stop_reason="completed")])
    )
    result = runtime.run(make_input())
    assert result.state == TaskLifecycleState.SUCCEEDED
    assert result.step_count == 1
    assert result.failure_reason is None
    assert result.output_text == "hello"


def test_runtime_waits_for_tool_calls() -> None:
    """Tool calls should suspend execution when no executor is supplied."""
    runtime = SingleAgentRuntime(
        StaticProvider(
            [
                ModelResponse(
                    output_text="need a tool",
                    stop_reason="tool_calls",
                    tool_calls=[{"name": "file.read", "arguments": {"path": "README.md"}}],
                )
            ]
        )
    )
    result = runtime.run(make_input())
    assert result.state == TaskLifecycleState.WAITING_TOOL
    assert result.step_count == 1
    assert result.checkpoint["pending_tool_calls"][0]["name"] == "file.read"


def test_runtime_fails_when_provider_errors() -> None:
    """Provider exceptions should surface as normalized runtime failures."""
    runtime = SingleAgentRuntime(ErrorProvider())
    result = runtime.run(make_input())
    assert result.state == TaskLifecycleState.FAILED
    assert result.failure_reason == FailureReasonCode.MODEL_PROVIDER_ERROR


def test_runtime_enforces_step_limit() -> None:
    """The runtime should fail attempts that exceed the configured step limit."""
    runtime = SingleAgentRuntime(
        StaticProvider(
            [
                ModelResponse(output_text="", stop_reason="loop"),
                ModelResponse(output_text="", stop_reason="loop"),
            ]
        )
    )
    result = runtime.run(make_input(max_steps=1))
    assert result.state == TaskLifecycleState.FAILED
    assert result.failure_reason == FailureReasonCode.STEP_LIMIT_EXCEEDED
