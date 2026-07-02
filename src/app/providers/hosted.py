"""Hosted model adapter for OpenAI-compatible chat endpoints."""

import json
from urllib import error, request

from app.providers.base import ModelProvider, ModelProviderError, ModelRequest, ModelResponse


class OpenAICompatibleProvider(ModelProvider):
    """Minimal hosted provider adapter that speaks the OpenAI-compatible chat API."""

    def __init__(self, *, base_url: str, api_key: str, model_name: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name

    def generate(self, request_payload: ModelRequest) -> ModelResponse:
        """Translate a normalized request into a hosted chat completion call."""
        payload = {
            "model": self._model_name,
            "messages": self._build_messages(request_payload),
        }
        if request_payload.temperature is not None:
            payload["temperature"] = request_payload.temperature
        if request_payload.max_output_tokens is not None:
            payload["max_tokens"] = request_payload.max_output_tokens

        raw_response = self._post_json("/chat/completions", payload)
        try:
            choice = raw_response["choices"][0]
            message = choice["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelProviderError("Hosted provider response is missing completion data.") from exc

        return ModelResponse(
            output_text=message.get("content") or "",
            tool_calls=message.get("tool_calls") or [],
            stop_reason=choice.get("finish_reason"),
            usage=raw_response.get("usage") or {},
            raw_provider_response=raw_response,
        )

    def _build_messages(self, request_payload: ModelRequest) -> list[dict]:
        """Combine the system prompt and conversation history into provider format."""
        messages: list[dict] = []
        if request_payload.system_prompt:
            messages.append({"role": "system", "content": request_payload.system_prompt})
        messages.extend(request_payload.messages)
        return messages

    def _post_json(self, path: str, payload: dict) -> dict:
        """Perform the HTTP request and normalize transport failures."""
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        http_request = request.Request(
            url=f"{self._base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ModelProviderError(f"Hosted provider returned HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise ModelProviderError(f"Hosted provider request failed: {exc.reason}") from exc
