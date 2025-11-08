"""Minimal test endpoint to diagnose API issues."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db_session
from app.graph.research_graph import ResearchGraph
from app.security.dependencies import get_secret_store_dependency
from app.security.secret_store import SecretStore

router = APIRouter(prefix="/test", tags=["test"])


@router.get("/simple")
async def test_simple():
    """Simplest possible endpoint."""
    return {"status": "ok", "message": "Simple endpoint works"}


@router.get("/with-db")
async def test_with_db(session: AsyncSession = Depends(get_db_session)):
    """Test with database dependency."""
    return {"status": "ok", "message": "Database dependency works"}


@router.get("/with-graph")
async def test_with_graph(
    session: AsyncSession = Depends(get_db_session),
    secret_store: SecretStore = Depends(get_secret_store_dependency),
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



