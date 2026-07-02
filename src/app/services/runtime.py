"""Factories for assembling runtime objects from application settings."""

from app.core.settings import Settings, get_settings
from app.providers.factory import build_model_provider
from app.runtime.engine import SingleAgentRuntime


def build_runtime(settings: Settings | None = None) -> SingleAgentRuntime:
    """Create a runtime wired to the configured model provider."""
    settings = settings or get_settings()
    provider = build_model_provider(settings)
    return SingleAgentRuntime(provider=provider)
