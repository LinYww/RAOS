"""Smoke tests that verify the application boots with core wiring intact."""

from app.api.app import create_app
from app.models.agent import Agent
from app.models.checkpoint import Checkpoint
from app.models.task import Task, TaskAttempt, TaskEvent
from app.models.tool import ToolDefinition, ToolInvocation
from app.workers.celery_app import celery_app


def test_fastapi_app_bootstraps() -> None:
    """FastAPI app factory should produce the configured application shell."""
    app = create_app()
    assert app.title == "RA_OS Agent Runtime"


def test_celery_app_bootstraps() -> None:
    """Celery worker configuration should be importable during bootstrap."""
    assert celery_app.main == "ra_os"


def test_core_entities_are_importable() -> None:
    """Core ORM entities should stay importable from their module paths."""
    assert Agent.__tablename__ == "agents"
    assert Task.__tablename__ == "tasks"
    assert TaskAttempt.__tablename__ == "task_attempts"
    assert TaskEvent.__tablename__ == "task_events"
    assert ToolDefinition.__tablename__ == "tool_definitions"
    assert ToolInvocation.__tablename__ == "tool_invocations"
    assert Checkpoint.__tablename__ == "checkpoints"
