from app.core.settings import Settings
from app.providers.base import ModelProvider
from app.providers.hosted import OpenAICompatibleProvider
from app.providers.mock import MockModelProvider


def build_model_provider(settings: Settings) -> ModelProvider:
    if settings.hosted_model_provider == "mock":
        return MockModelProvider()
    if settings.hosted_model_provider == "openai_compatible":
        return OpenAICompatibleProvider(
            base_url=settings.hosted_model_base_url,
            api_key=settings.hosted_model_api_key,
            model_name=settings.hosted_model_name,
        )
    raise ValueError(f"Unsupported hosted model provider: {settings.hosted_model_provider}")
