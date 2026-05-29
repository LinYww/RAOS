from app.providers.base import ModelRequest
from app.providers.mock import MockModelProvider


def test_mock_provider_returns_terminal_text_for_normal_prompt() -> None:
    provider = MockModelProvider()
    response = provider.generate(
        ModelRequest(messages=[{"role": "user", "content": "hello"}], system_prompt="system")
    )
    assert response.stop_reason == "completed"
    assert "Mock agent completed" in response.output_text


def test_mock_provider_generates_tool_call_for_file_prefix() -> None:
    provider = MockModelProvider()
    response = provider.generate(
        ModelRequest(
            messages=[{"role": "user", "content": "tool:file.read README.md"}],
            system_prompt="system",
        )
    )
    assert response.stop_reason == "tool_calls"
    assert response.tool_calls[0]["name"] == "file.read"
