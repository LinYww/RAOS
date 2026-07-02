"""Normalized model-provider request and response contracts."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class ModelRequest:
    """Provider-agnostic prompt payload consumed by runtime adapters."""

    messages: list[dict]
    system_prompt: str
    tools: list[dict] = field(default_factory=list)
    temperature: float | None = None
    max_output_tokens: int | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class ModelResponse:
    """Provider-agnostic completion payload returned to the runtime."""

    output_text: str
    tool_calls: list[dict] = field(default_factory=list)
    stop_reason: str | None = None
    usage: dict = field(default_factory=dict)
    raw_provider_response: dict = field(default_factory=dict)


class ModelProvider:
    """Interface implemented by all model backends."""

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Produce a normalized model response for one runtime step."""
        raise NotImplementedError


class ModelProviderError(RuntimeError):
    """Raised when a provider cannot complete a normalized model request."""
