"""Health and readiness endpoints."""

from fastapi import APIRouter

from app.schemas.system import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    """Return basic liveness information."""

    return HealthResponse()

