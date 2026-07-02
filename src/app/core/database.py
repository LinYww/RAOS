"""Database engine, metadata, and session-factory helpers."""

from functools import lru_cache

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.settings import Settings, get_settings


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all ORM models with consistent naming conventions."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def _engine_options(settings: Settings) -> dict:
    """Return SQLAlchemy engine options derived from the configured backend."""
    if settings.database_url.startswith("sqlite"):
        options = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in settings.database_url:
            options["poolclass"] = StaticPool
        return options
    return {}


@lru_cache
def get_engine() -> Engine:
    """Build and cache the process-wide SQLAlchemy engine."""
    settings = get_settings()
    return create_engine(settings.database_url, future=True, **_engine_options(settings))


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Build and cache the session factory bound to the shared engine."""
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)


def session_scope() -> Session:
    """Create a new database session for a single unit of work."""
    return get_session_factory()()


def init_database() -> None:
    """Import model metadata and create missing tables."""
    from app.models import agent, checkpoint, task, tool  # noqa: F401

    Base.metadata.create_all(bind=get_engine())
