from app.core.settings import Settings, get_settings
from app.providers.factory import build_model_provider
from app.runtime.engine import SingleAgentRuntime


def build_runtime(settings: Settings | None = None) -> SingleAgentRuntime:
    settings = settings or get_settings()
    provider = build_model_provider(settings)
    return SingleAgentRuntime(provider=provider)
