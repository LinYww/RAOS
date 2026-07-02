"""Local model provider used for deterministic development and tests."""

from app.providers.base import ModelProvider, ModelRequest, ModelResponse


class MockModelProvider(ModelProvider):
    """Local provider used to keep the MVP runnable without external credentials."""

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Return canned behavior based on simple message prefixes."""
        last_message = request.messages[-1] if request.messages else {"role": "user", "content": ""}
        content = last_message.get("content", "")

        if last_message.get("role") == "tool":
            return ModelResponse(
                output_text=f"Tool completed successfully. Result: {content}",
                stop_reason="completed",
            )

        if content.startswith("tool:file.read "):
            path = content.removeprefix("tool:file.read ").strip()
            return ModelResponse(
                output_text="Requesting file tool",
                stop_reason="tool_calls",
                tool_calls=[{"name": "file.read", "arguments": {"path": path}}],
            )

        if content.startswith("tool:shell.exec "):
            command = content.removeprefix("tool:shell.exec ").strip().split()
            return ModelResponse(
                output_text="Requesting shell tool",
                stop_reason="tool_calls",
                tool_calls=[{"name": "shell.exec", "arguments": {"command": command}}],
            )

        if content.startswith("tool:http.fetch "):
            url = content.removeprefix("tool:http.fetch ").strip()
            return ModelResponse(
                output_text="Requesting http tool",
                stop_reason="tool_calls",
                tool_calls=[{"name": "http.fetch", "arguments": {"url": url}}],
            )

        if "waiting_user" in content:
            return ModelResponse(output_text="Need user input before continuing.", stop_reason="waiting_user")

        return ModelResponse(output_text=f"Mock agent completed: {content}", stop_reason="completed")
