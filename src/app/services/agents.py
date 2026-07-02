"""Application service for managing agent definitions."""

from app.models.agent import Agent
from app.repositories.agents import AgentRepository
from app.schemas.agent import AgentCreateRequest


class AgentService:
    """Orchestrate agent creation and lookup operations."""

    def __init__(self, repository: AgentRepository) -> None:
        self._repository = repository

    def create(self, payload: AgentCreateRequest) -> Agent:
        """Create an agent domain object from an API request payload."""
        agent = Agent(
            name=payload.name,
            version=payload.version,
            system_prompt=payload.system_prompt,
            model_provider=payload.model_provider,
            model_name=payload.model_name,
            enabled=payload.enabled,
        )
        return self._repository.create(agent)

    def list(self) -> list[Agent]:
        """Return all registered agents."""
        return self._repository.list()

    def get(self, agent_id: str) -> Agent | None:
        """Fetch a single agent by identifier."""
        return self._repository.get(agent_id)
