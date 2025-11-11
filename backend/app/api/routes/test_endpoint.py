"""Minimal test endpoint to diagnose API issues."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.dependencies import get_db_session
from app.graph.research_graph import ResearchGraph
from app.security.dependencies import get_secret_store_dependency
from app.security.secret_store import SecretStore

router = APIRouter(prefix="/test", tags=["test"])


def check_test_endpoints_enabled():
    """Raise 404 if test endpoints are disabled in production."""
    settings = get_settings()
    if settings.app_env == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test endpoints are disabled in production",
        )


@router.get("/simple")
async def test_simple(_: None = Depends(check_test_endpoints_enabled)):
    """Simplest possible endpoint."""
    return {"status": "ok", "message": "Simple endpoint works"}


@router.get("/with-db")
async def test_with_db(
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(check_test_endpoints_enabled),
):
    """Test with database dependency."""
    return {"status": "ok", "message": "Database dependency works"}


@router.get("/with-graph")
async def test_with_graph(
    session: AsyncSession = Depends(get_db_session),
    secret_store: SecretStore = Depends(get_secret_store_dependency),
    _: None = Depends(check_test_endpoints_enabled),
):
    """Test with graph creation."""
    try:
        graph = ResearchGraph(
            session=session,
            secret_store=secret_store,
            provider="openai",
            secret_token=None,
        )
        return {"status": "ok", "message": "Graph creation works"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/with-run")
async def test_with_run(
    session: AsyncSession = Depends(get_db_session),
    secret_store: SecretStore = Depends(get_secret_store_dependency),
    _: None = Depends(check_test_endpoints_enabled),
):
    """Test with actual graph run."""
    try:
        graph = ResearchGraph(
            session=session,
            secret_store=secret_store,
            provider="openai",
            secret_token=None,
        )
        result = await graph.run(question="test", history=[])
        return {
            "status": "ok",
            "message": "Graph run works",
            "answer_length": len(result.get("answer", "")),
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "type": type(e).__name__}



