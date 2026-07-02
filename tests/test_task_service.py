"""Integration-style tests for the task orchestration service."""

from app.core.database import init_database, session_scope
from app.models.agent import Agent
from app.services.bootstrap import bootstrap_builtin_tools
from app.services.tasks import TaskService
from app.schemas.task import TaskCreateRequest


def test_task_service_runs_mock_task_to_terminal_state() -> None:
    """Submitting a task should drive it to a terminal state with the mock provider."""
    init_database()
    session = session_scope()
    try:
        bootstrap_builtin_tools(session)
        agent = Agent(
            name="mock-agent",
            version="v1",
            system_prompt="You are a mock agent.",
            model_provider="mock",
            model_name="mock",
            enabled=True,
        )
        session.add(agent)
        session.commit()

        service = TaskService(session)
        task = service.submit(
            TaskCreateRequest(
                agent_id=agent.id,
                prompt="hello MVP",
                allowed_scopes=[],
            )
        )
        assert task.state == "succeeded"
        assert task.terminal_summary is not None
    finally:
        session.close()
