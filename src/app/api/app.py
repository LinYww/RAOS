"""FastAPI application factory and startup lifecycle hooks."""

from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import FastAPI

from app.api.routers.agents import router as agents_router
from app.api.routers.health import router as health_router
from app.api.routers.tasks import router as tasks_router
from app.core.database import init_database, session_scope
from app.core.settings import get_settings
from app.services.bootstrap import bootstrap_builtin_tools


@contextmanager
def app_lifespan(_: FastAPI) -> Iterator[None]:
    """Initialize durable resources and seed built-in tool definitions."""
    init_database()
    session = session_scope()
    try:
        bootstrap_builtin_tools(session)
        session.commit()
        yield
    finally:
        session.close()


def create_app() -> FastAPI:
    """Build the HTTP application using the current settings snapshot."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=app_lifespan,
    )
    app.include_router(health_router)
    app.include_router(agents_router, prefix=settings.api_prefix)
    app.include_router(tasks_router, prefix=settings.api_prefix)

    return app
