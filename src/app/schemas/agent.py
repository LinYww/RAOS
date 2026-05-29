from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AgentResponseModel(BaseModel):
    model_config = {"from_attributes": True}


class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    version: str = Field(default="v1", min_length=1, max_length=50)
    system_prompt: str = Field(min_length=1)
    model_provider: str = Field(min_length=1, max_length=100)
    model_name: str = Field(min_length=1, max_length=100)
    enabled: bool = True


class AgentDetailResponse(AgentResponseModel):
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
    items: list[AgentDetailResponse]
