"""Task-management endpoints for the operator control plane."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import build_task_service, get_db_session
from app.schemas.task import (
    TaskActionResponse,
    TaskCreateRequest,
    TaskDetailResponse,
    TaskEventListResponse,
    TaskListResponse,
    TaskEventResponse,
    TaskResumeRequest,
    TaskRetryRequest,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskDetailResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreateRequest, session=Depends(get_db_session)) -> TaskDetailResponse:
    """Create a task and execute its first attempt immediately."""
    try:
        task = build_task_service(session).submit(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TaskDetailResponse.model_validate(task)


@router.get("", response_model=TaskListResponse)
def list_tasks(
    state: str | None = Query(default=None),
    session=Depends(get_db_session),
) -> TaskListResponse:
    """List tasks, optionally filtered by lifecycle state."""
    items = build_task_service(session).list(state=state)
    return TaskListResponse(items=[TaskDetailResponse.model_validate(item) for item in items])


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: str, session=Depends(get_db_session)) -> TaskDetailResponse:
    """Return the current persisted view of a task."""
    task = build_task_service(session).get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return TaskDetailResponse.model_validate(task)


@router.get("/{task_id}/events", response_model=TaskEventListResponse)
def get_task_events(task_id: str, session=Depends(get_db_session)) -> TaskEventListResponse:
    """Return the ordered event stream for a task."""
    service = build_task_service(session)
    task = service.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    events = service.events(task_id)
    return TaskEventListResponse(
        task_id=task_id,
        items=[TaskEventResponse.model_validate(item) for item in events],
    )


@router.post("/{task_id}/cancel", response_model=TaskActionResponse)
def cancel_task(task_id: str, session=Depends(get_db_session)) -> TaskActionResponse:
    """Request task cancellation through the runtime transition layer."""
    try:
        build_task_service(session).cancel(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TaskActionResponse(task_id=task_id, accepted=True, action="cancel")


@router.post("/{task_id}/resume", response_model=TaskActionResponse)
def resume_task(task_id: str, payload: TaskResumeRequest, session=Depends(get_db_session)) -> TaskActionResponse:
    """Resume an operator-paused task and enqueue a fresh execution pass."""
    try:
        build_task_service(session).resume(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TaskActionResponse(task_id=task_id, accepted=True, action="resume", reason=payload.reason)


@router.post("/{task_id}/retry", response_model=TaskActionResponse)
def retry_task(task_id: str, payload: TaskRetryRequest, session=Depends(get_db_session)) -> TaskActionResponse:
    """Start a new attempt for an existing task."""
    try:
        build_task_service(session).retry(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TaskActionResponse(task_id=task_id, accepted=True, action="retry", reason=payload.reason)


@router.post("/{task_id}/pause", response_model=TaskActionResponse)
def pause_task(task_id: str, session=Depends(get_db_session)) -> TaskActionResponse:
    """Pause a running task at the control-plane level."""
    try:
        build_task_service(session).pause(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TaskActionResponse(task_id=task_id, accepted=True, action="pause")
