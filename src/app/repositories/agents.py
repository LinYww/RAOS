"""Persistence operations for agent entities."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Agent


class AgentRepository:
    """Read and write agent rows using the current SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, agent: Agent) -> Agent:
        """Persist a new agent row."""
        self._session.add(agent)
        self._session.flush()
        return agent

    def list(self) -> list[Agent]:
        """Return agents ordered newest-first for operator listing screens."""
        return list(self._session.scalars(select(Agent).order_by(Agent.created_at.desc())))

    def get(self, agent_id: str) -> Agent | None:
        """Fetch a single agent by primary key."""
        return self._session.get(Agent, agent_id)
