from collections.abc import Generator

from app.core.database import session_scope
from app.core.settings import Settings, get_settings
from app.repositories.agents import AgentRepository
from app.services.agents import AgentService
from app.services.tasks import TaskService


def get_app_settings() -> Settings:
    return get_settings()


def get_db_session() -> Generator:
    session = session_scope()
    try:
        yield session
    finally:
        session.close()


def build_agent_service(session) -> AgentService:
    return AgentService(AgentRepository(session))


def build_task_service(session) -> TaskService:
    return TaskService(session)
