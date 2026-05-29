from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Agent


class AgentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, agent: Agent) -> Agent:
        self._session.add(agent)
        self._session.flush()
        return agent

    def list(self) -> list[Agent]:
        return list(self._session.scalars(select(Agent).order_by(Agent.created_at.desc())))

    def get(self, agent_id: str) -> Agent | None:
        return self._session.get(Agent, agent_id)
