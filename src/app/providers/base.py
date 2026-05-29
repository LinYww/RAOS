from dataclasses import dataclass, field


@dataclass(slots=True)
class ModelRequest:
    messages: list[dict]
    system_prompt: str
    tools: list[dict] = field(default_factory=list)
    temperature: float | None = None
    max_output_tokens: int | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class ModelResponse:
    output_text: str
    tool_calls: list[dict] = field(default_factory=list)
    stop_reason: str | None = None
    usage: dict = field(default_factory=dict)
    raw_provider_response: dict = field(default_factory=dict)


class ModelProvider:
    def generate(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError


class ModelProviderError(RuntimeError):
    """Raised when a provider cannot complete a normalized model request."""
