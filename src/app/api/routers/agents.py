from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import build_agent_service, get_db_session
from app.schemas.agent import AgentCreateRequest, AgentDetailResponse, AgentListResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentDetailResponse, status_code=status.HTTP_201_CREATED)
def register_agent(payload: AgentCreateRequest, session=Depends(get_db_session)) -> AgentDetailResponse:
    agent = build_agent_service(session).create(payload)
    session.commit()
    return AgentDetailResponse.model_validate(agent)


@router.get("", response_model=AgentListResponse)
def list_agents(session=Depends(get_db_session)) -> AgentListResponse:
    items = build_agent_service(session).list()
    return AgentListResponse(items=[AgentDetailResponse.model_validate(item) for item in items])


@router.get("/{agent_id}", response_model=AgentDetailResponse)
def get_agent(agent_id: str, session=Depends(get_db_session)) -> AgentDetailResponse:
    agent = build_agent_service(session).get(agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")
    return AgentDetailResponse.model_validate(agent)
