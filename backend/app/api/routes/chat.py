"""Chat query and export endpoints."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.dependencies import get_db_session
from app.graph.research_graph import ResearchGraph
from app.graph.types import GraphState
from app.schemas.chat import (
    ChatExportRequest,
    ChatRequest,
    ChatResponse,
    Citation,
    EvaluationSummary,
    StreamEvent,
)
from app.security.dependencies import get_secret_store_dependency
from app.security.secret_store import SecretStore
from app.services.exporter import render_json, render_markdown, render_pdf

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def _format_response(state: GraphState) -> ChatResponse:
    try:
        evaluation = state.get("evaluation") or {}
        citations_payload = state.get("citations") or []
        
        # Priority: compiled_answer > enriched_answer > answer
        answer = (
            state.get("compiled_answer") 
            or state.get("enriched_answer") 
            or state.get("answer", "")
        )
        
        return ChatResponse(
            answer=answer,
            citations=[Citation.model_validate(item) for item in citations_payload],
            evaluation=EvaluationSummary.model_validate(evaluation),
        )
    except Exception as e:
        logger.error("format_response.error", error=str(e), exc_info=True)
        # Return minimal valid response
        return ChatResponse(
            answer=state.get("answer", "Error formatting response"),
            citations=[],
            evaluation=EvaluationSummary(
                total_score=0.0,
                passed=False,
                criteria={},
                feedback=[f"Error: {str(e)}"]
            ),
        )


def _stream_event(event_type: str, payload: Dict[str, Any]) -> str:
    event = StreamEvent(type=event_type, payload=payload)
    return f"data: {event.model_dump_json()}\n\n"


@router.post("/query", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_query(
    request: ChatRequest,
    stream: bool = Query(False),
    session: AsyncSession = Depends(get_db_session),
    secret_store: SecretStore = Depends(get_secret_store_dependency),
) -> Response:
    try:
        logger.info("chat_query.start", question=request.question[:50], provider=request.provider)
        graph = ResearchGraph(
            session=session,
            secret_store=secret_store,
            provider=request.provider,
            secret_token=request.secret_token,
        )
        logger.info("chat_query.graph_created")
    except Exception as e:
        logger.error("chat_query.graph_creation_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create graph: {str(e)}"
        )

    if stream:
        async def event_generator() -> AsyncIterator[bytes]:
            yield _stream_event("status", {"message": "Processing"}).encode("utf-8")

            initial_state: GraphState = {
                "question": request.question,
                "history": [turn.model_dump() for turn in request.history],
                "provider": request.provider,
                "retry_count": 0,
            }

            final_state: GraphState | None = None

            async for event in graph.graph.astream_events(initial_state, version="v1"):
                if event["event"] == "on_node_end":
                    node = event["name"]
                    state = event["state"]
                    if node == "research":
                        # Research node combines RAG + Tavily
                        yield _stream_event("documents", {"documents": state.get("documents", [])}).encode("utf-8")
                        yield _stream_event("web_results", {"web_results": state.get("web_results", [])}).encode("utf-8")
                    elif node == "generate":
                        yield _stream_event(
                            "answer",
                            {
                                "answer": state.get("answer", ""),
                                "citations": state.get("citations", []),
                            },
                        ).encode("utf-8")
                    elif node == "evaluate_quality":
                        yield _stream_event("evaluation", {"evaluation": state.get("evaluation", {})}).encode("utf-8")
                    elif node == "compile_technical":
                        yield _stream_event("status", {"message": "Compiling content..."}).encode("utf-8")
                    elif node == "evaluate_compiler":
                        yield _stream_event("status", {"message": "Evaluating compilation..."}).encode("utf-8")
                if event["event"] == "on_chain_end":
                    final_state = event["state"]

            if final_state is None:
                final_state = await graph.graph.ainvoke(initial_state)

            response_payload = _format_response(final_state).model_dump()
            yield _stream_event("done", response_payload).encode("utf-8")

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    try:
        result = await graph.run(
            question=request.question,
            history=[turn.model_dump() for turn in request.history],
        )
        return Response(
            content=_format_response(result).model_dump_json(),
            media_type="application/json",
        )
    except Exception as e:
        logger.error("chat_query.error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat query failed: {str(e)}"
        )


@router.post("/export")
async def export_response(payload: ChatExportRequest) -> Response:
    filename_base = "research-response"
    if payload.format == "markdown":
        content = render_markdown(payload.answer, payload.citations, payload.evaluation)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.md"'},
        )

    if payload.format == "json":
        content = render_json(payload.answer, payload.citations, payload.evaluation)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.json"'},  # noqa: E501
        )

    if payload.format == "pdf":
        content = render_pdf(payload.answer, payload.citations, payload.evaluation)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'},
        )

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported export format.")

