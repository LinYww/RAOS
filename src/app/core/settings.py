from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RA_OS Agent Runtime"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str = Field(default="sqlite+pysqlite:///:memory:")
    celery_broker_url: str = Field(default="memory://")
    celery_result_backend: str = Field(default="cache+memory://")
    celery_task_always_eager: bool = True
    celery_task_store_eager_result: bool = True
    runtime_default_max_steps: int = Field(default=32, ge=1)
    runtime_default_timeout_seconds: int = Field(default=300, ge=1)
    hosted_model_provider: str = "mock"
    hosted_model_base_url: str = "https://api.openai.com/v1"
    hosted_model_api_key: str = ""
    hosted_model_name: str = "gpt-4.1-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RA_OS_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
