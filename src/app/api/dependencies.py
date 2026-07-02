"""Dependency helpers shared across API routers."""

from collections.abc import Generator

from app.core.database import session_scope
from app.core.settings import Settings, get_settings
from app.repositories.agents import AgentRepository
from app.services.agents import AgentService
from app.services.tasks import TaskService


def get_app_settings() -> Settings:
    """Expose cached settings through FastAPI dependency injection."""
    return get_settings()


def get_db_session() -> Generator:
    """Yield a request-scoped database session and always close it."""
    session = session_scope()
    try:
        yield session
    finally:
        session.close()


def build_agent_service(session) -> AgentService:
    """Construct the agent service for the current database session."""
    return AgentService(AgentRepository(session))


def build_task_service(session) -> TaskService:
    """Construct the task service for the current database session."""
    return TaskService(session)
