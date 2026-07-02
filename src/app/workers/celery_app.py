"""Celery integration for asynchronous runtime execution."""

from celery import Celery

from app.core.settings import get_settings
from app.runtime.types import RuntimeExecutionInput
from app.services.runtime import build_runtime

settings = get_settings()

celery_app = Celery(
    "ra_os",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.task_default_queue = "agent-runtime"
celery_app.conf.task_always_eager = settings.celery_task_always_eager
celery_app.conf.task_store_eager_result = settings.celery_task_store_eager_result


@celery_app.task(name="runtime.execute_task")
def execute_task(payload: dict) -> dict:
    """Run a serialized runtime payload through the configured worker runtime."""
    runtime = build_runtime(settings)
    result = runtime.run(RuntimeExecutionInput(**payload))
    return {
        "state": result.state.value,
        "failure_reason": result.failure_reason.value if result.failure_reason else None,
        "step_count": result.step_count,
        "output_text": result.output_text,
        "event_count": len(result.events),
        "checkpoint": result.checkpoint,
    }
