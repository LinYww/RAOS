"""Liveness and readiness endpoints for orchestration systems."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live() -> dict[str, str]:
    """Report that the process is running."""
    return {"status": "ok"}


@router.get("/health/ready")
def ready() -> dict[str, str]:
    """Report that the application has finished bootstrapping."""
    return {"status": "ready"}
