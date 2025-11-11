"""Chat query and export endpoints."""

from __future__ import annotations

import hashlib
import json
from typing import Any, AsyncIterator, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.redis import get_redis
from app.db.dependencies import get_db_session
from app.graph.research_graph import ResearchGraph
from app.graph.types import GraphState
from app.schemas.chat import (
    ChatExportRequest,
    ChatRequest,
    ChatResponse,
    Citation,
    EvaluationSummary,
    QuickChatResponse,
    StreamEvent,
)
from app.security.dependencies import get_secret_store_dependency
from app.security.secret_store import SecretStore
from app.services.exporter import render_json, render_markdown, render_pdf

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def _format_response(state: GraphState) -> ChatResponse:
    try:
        evaluation_raw = state.get("evaluation") or state.get("compiler_evaluation") or {}
        citations_payload = state.get("citations") or []
        
        # Priority: enriched_answer > compiled_answer > answer
        # Agent 4 enrichment should always be used if available
        answer = (
            state.get("enriched_answer")   # ← Agent 4 output (highest priority)
            or state.get("compiled_answer")  # ← Agent 3 output (fallback)
            or state.get("answer", "")       # ← Raw answer (final fallback)
        )
        
        # Handle different evaluation formats
        # Compiler evaluator returns: {technical_preservation, psw_structure, ...}
        # Quality evaluator returns: {coverage_score, citation_density, ...}
        if "coverage_score" in evaluation_raw:
            # Standard quality evaluator format
            evaluation = EvaluationSummary.model_validate(evaluation_raw)
        else:
            # Compiler evaluator format or empty - create compatible format
            # Wrap compiler scores in nested dict structure for criteria field
            criteria_dict = {}
            for key, value in evaluation_raw.items():
                if key not in ["total_score", "passed", "feedback"]:
                    criteria_dict[key] = {"score": value, "weight": 1.0}
            
            evaluation = EvaluationSummary(
                total_score=evaluation_raw.get("total_score", 0.0),
                passed=evaluation_raw.get("passed", False),
                coverage_score=0.0,  # Not applicable for compiler
                citation_density=0.0,  # Not applicable for compiler
                exec_ok=True,  # Assume true for compiler
                scope_ok=True,  # Assume true for compiler
                criteria=criteria_dict,  # Wrap compiler eval in nested dict
                feedback=evaluation_raw.get("feedback", []),
            )
        
        return ChatResponse(
            answer=answer,
            citations=[Citation.model_validate(item) for item in citations_payload],
            evaluation=evaluation,
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
                coverage_score=0.0,
                citation_density=0.0,
                exec_ok=False,
                scope_ok=False,
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
        
        response = _format_response(result)
        
        # Store Q&A pair if high quality (async, don't block response)
        try:
            from app.services.qa_storage import store_qa_if_high_quality
            
            quality_score = response.evaluation.total_score
            if quality_score >= 85.0:  # Only attempt storage for high-quality answers
                # Fire and forget - don't await
                import asyncio
                asyncio.create_task(
                    store_qa_if_high_quality(
                        session=session,
                        question=request.question,
                        answer=response.answer,
                        quality_score=quality_score,
                        mode="generate",
                        citations=[c.model_dump() for c in response.citations],
                    )
                )
                logger.debug("qa_storage.task_created", score=quality_score)
        except Exception as storage_error:
            # Don't fail the request if storage fails
            logger.warning("qa_storage.task_failed", error=str(storage_error))
        
        return Response(
            content=response.model_dump_json(),
            media_type="application/json",
        )
    except Exception as e:
        logger.error("chat_query.error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat query failed: {str(e)}"
        )


@router.post("/quick-qa", response_model=QuickChatResponse, status_code=status.HTTP_200_OK)
async def quick_qa(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db_session),
    secret_store: SecretStore = Depends(get_secret_store_dependency),
) -> QuickChatResponse:
    """
    Quick Q&A endpoint for chat mode.
    
    Strategy:
    1. RAG-first: Retrieve more documents (20 vs 15)
    2. Check if RAG is sufficient (≥10 docs with good similarity)
    3. If RAG sufficient: Generate answer from RAG only
    4. If RAG insufficient: Fallback to Tavily + RAG
    5. Maintain conversation context (last 10 messages)
    6. No quality evaluation (fast response)
    """
    try:
        from app.core.config import get_settings
        from app.vectorstore.pgvector_store import PGVectorStore
        from app.clients.embeddings import get_embedding_client
        from app.graph.tavily_research import TavilyResearchClient
        from app.providers.factory import get_chat_model
        from app.services.teaching_modes import get_teaching_mode_prompt, get_teaching_mode_config
        from langchain.schema import HumanMessage, SystemMessage, AIMessage

        settings = get_settings()
        logger.info("quick_qa.start", question=request.question[:50], teaching_mode=request.teaching_mode)

        # Prepare cache lookups (optional)
        cache_client = None
        cache_key = None
        history_limit = settings.chat_mode_history_limit
        recent_history = request.history[-history_limit:] if len(request.history) > history_limit else request.history

        if settings.enable_response_cache:
            cache_client = get_redis()
            if cache_client is not None:
                history_snapshot = [turn.model_dump() for turn in recent_history]
                key_material = "|".join(
                    [
                        request.question.strip().lower(),
                        json.dumps(history_snapshot, sort_keys=True),
                        request.provider,
                        (request.model or settings.openai_chat_model),
                        request.teaching_mode,
                    ]
                )
                cache_key = f"chat:qa:{hashlib.sha256(key_material.encode('utf-8')).hexdigest()}"
                cached_raw = await cache_client.get(cache_key)
                if cached_raw:
                    try:
                        if isinstance(cached_raw, bytes):
                            cached_raw = cached_raw.decode("utf-8")
                        cached_payload = json.loads(cached_raw)
                        logger.info("quick_qa.cache_hit", cache_key=cache_key)
                        return QuickChatResponse(**cached_payload)
                    except json.JSONDecodeError as cache_error:
                        logger.warning("quick_qa.cache_decode_failed", error=str(cache_error))

        # 1. RAG Retrieval (prioritize knowledge base first)
        embedding_client = get_embedding_client()
        vector_store = PGVectorStore(session=session)

        embeddings = await embedding_client.embed_documents([request.question])
        question_embedding = embeddings[0] if embeddings else []

        rag_docs = await vector_store.similarity_search(
            embedding=question_embedding,
            limit=settings.chat_mode_rag_limit,
            max_distance=settings.chat_mode_similarity_threshold,
        )

        logger.info("quick_qa.rag_retrieved", count=len(rag_docs))

        # Select top documents for prompt context
        rag_prompt_docs = rag_docs[: settings.chat_mode_rag_context_limit]

        # 2. Check if RAG is sufficient; fallback to Tavily only if needed
        rag_sufficient = len(rag_docs) >= settings.chat_mode_min_docs
        web_results = []

        if not rag_sufficient and settings.tavily_api_key and settings.chat_mode_tavily_limit > 0:
            logger.info("quick_qa.tavily_fallback", rag_count=len(rag_docs))
            try:
                tavily_client = TavilyResearchClient(api_key=settings.tavily_api_key)
                web_results = await tavily_client.search_prioritized(
                    query=request.question,
                    depth="quick",
                    max_results=settings.chat_mode_tavily_limit,
                )
                logger.info("quick_qa.tavily_retrieved", count=len(web_results))
            except Exception as tavily_error:
                logger.warning("quick_qa.tavily_failed", error=str(tavily_error))

        # 3. Build context from sources with truncation
        context_parts = []
        chunk_limit = settings.chat_mode_chunk_char_limit

        for i, doc in enumerate(rag_prompt_docs, 1):
            content = doc.content if hasattr(doc, "content") else str(doc)
            trimmed_content = content[:chunk_limit]
            if len(content) > chunk_limit:
                trimmed_content = f"{trimmed_content.rstrip()}..."
            context_parts.append(f"[Source {i} - RAG Document]\n{trimmed_content}\n")

        for i, result in enumerate(web_results, len(rag_prompt_docs) + 1):
            content = ""
            if isinstance(result, dict):
                content = result.get("content") or result.get("summary") or result.get("snippet") or ""
            else:
                content = str(result)
            trimmed_content = content[:chunk_limit]
            if len(content) > chunk_limit:
                trimmed_content = f"{trimmed_content.rstrip()}..."
            context_parts.append(f"[Source {i} - Web]\n{trimmed_content}\n")

        context = "\n".join(context_parts)

        messages = []

        # Get teaching mode configuration
        mode_config = get_teaching_mode_config(request.teaching_mode)
        system_prompt = get_teaching_mode_prompt(request.teaching_mode)

        logger.info(
            "quick_qa.teaching_mode",
            mode=request.teaching_mode,
            temperature=mode_config["temperature"],
            description=mode_config["description"],
        )

        messages.append(SystemMessage(content=system_prompt))

        # Add conversation history
        for turn in recent_history:
            if turn.role == "user":
                messages.append(HumanMessage(content=turn.content))
            else:
                messages.append(AIMessage(content=turn.content))

        # Add current question with context
        user_message = f"""Question: {request.question}

Available Sources:
{context}

Please answer the question using the provided sources. Be concise and practical."""

        messages.append(HumanMessage(content=user_message))

        # 4. Generate answer with teaching mode temperature
        model_name = request.model or settings.openai_chat_model
        teaching_temperature = mode_config["temperature"]

        llm = await get_chat_model(
            provider=request.provider,
            model=model_name,
            temperature=teaching_temperature,
            secret_store=secret_store,
            secret_token=request.secret_token,
        )

        logger.info(
            "quick_qa.generating",
            model=model_name,
            temperature=teaching_temperature,
            teaching_mode=request.teaching_mode,
        )
        response = await llm.ainvoke(messages)
        answer = response.content

        sources_in_prompt = len(rag_prompt_docs) + len(web_results)

        logger.info(
            "quick_qa.success",
            answer_length=len(answer),
            sources=sources_in_prompt,
            rag_only=rag_sufficient and not web_results,
        )

        quick_response = QuickChatResponse(
            answer=answer,
            sources_used=sources_in_prompt,
            rag_only=rag_sufficient and not web_results,
        )

        if cache_client is not None and cache_key:
            try:
                await cache_client.set(
                    cache_key,
                    quick_response.model_dump_json(),
                    ex=settings.response_cache_ttl_seconds,
                )
                logger.info("quick_qa.cache_store", cache_key=cache_key, ttl=settings.response_cache_ttl_seconds)
            except Exception as cache_store_error:
                logger.warning("quick_qa.cache_store_failed", error=str(cache_store_error))

        return quick_response

    except Exception as e:
        logger.error("quick_qa.error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick Q&A failed: {str(e)}",
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

