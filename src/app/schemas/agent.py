"""Pydantic schemas used by the agent-management API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AgentResponseModel(BaseModel):
    """Base response model configured for ORM object serialization."""

    model_config = {"from_attributes": True}


class AgentCreateRequest(BaseModel):
    """Payload accepted when registering a new agent."""

    name: str = Field(min_length=1, max_length=200)
    version: str = Field(default="v1", min_length=1, max_length=50)
    system_prompt: str = Field(min_length=1)
    model_provider: str = Field(min_length=1, max_length=100)
    model_name: str = Field(min_length=1, max_length=100)
    enabled: bool = True


class AgentDetailResponse(AgentResponseModel):
    """Detailed representation of an agent returned by the API."""

    id: UUID
    name: str
    version: str
    system_prompt: str
    model_provider: str
    model_name: str
    enabled: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AgentListResponse(BaseModel):
    """Collection wrapper for agent list endpoints."""

    items: list[AgentDetailResponse]
