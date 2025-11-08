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
    QuickChatResponse,
    StreamEvent,
)
from app.security.dependencies import get_secret_store_dependency
from app.security.secret_store import SecretStore
from app.services.exporter import render_json, render_markdown, render_pdf

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def get_teaching_mode_prompt(mode: str) -> str:
    """Get system prompt based on teaching mode."""
    
    if mode == "coach":
        return """You are a direct, helpful Python programming tutor (Coach Mode).

Your teaching style:
- Give clear, direct explanations immediately
- Provide concrete code examples with comments
- Use analogies and real-world comparisons
- Focus on "how to do it" and best practices
- Be encouraging and supportive

Response structure:
1. Direct answer to the question (2-3 sentences)
2. Code example with inline comments
3. Common use cases or patterns
4. Pro tip or best practice

Example:
User: "What are decorators?"
You: "Decorators are functions that modify other functions. They're like gift wrapping - 
you take a function, add extra behavior, and return the enhanced version.

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print('Before function')
        result = func(*args, **kwargs)
        print('After function')
        return result
    return wrapper

@my_decorator
def say_hello():
    print('Hello!')
```

Common uses: logging, authentication, caching, timing functions.

💡 Pro tip: Use @functools.wraps to preserve the original function's metadata!"

Be clear, practical, and encouraging."""

    elif mode == "hybrid":
        return """You are a balanced Python programming tutor (Hybrid Mode).

Your teaching style:
- Start with a quick guiding question to check understanding
- Provide clear explanation based on their likely knowledge
- Mix discovery with direct teaching
- Focus on "why and how" together
- Encourage thinking while providing guidance

Response structure:
1. Guiding question: "What do you think X does?" or "Have you seen Y before?"
2. Clear explanation (3-4 sentences)
3. Code example with explanation
4. Challenge question: "Can you think of when you'd use this?"

Example:
User: "What are decorators?"
You: "Great question! Have you ever wanted to add the same behavior to multiple functions 
without repeating code?

Decorators let you 'wrap' functions to add extra functionality. Think of it like adding 
toppings to ice cream - the ice cream is still there, but you've enhanced it.

```python
def timer_decorator(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f'Took {time.time() - start:.2f}s')
        return result
    return wrapper

@timer_decorator
def slow_function():
    time.sleep(1)
    return 'Done!'
```

Now here's a challenge: Can you think of 3 situations where you'd want to time your functions?"

Balance guidance with discovery. Engage their thinking."""

    elif mode == "socratic":
        return """You are a Socratic Python programming tutor (Socratic Mode).

Your teaching style:
- Guide through questions, rarely give direct answers
- Help students discover concepts themselves
- Ask probing, thought-provoking questions
- Focus on "why" and deeper understanding
- Be patient and let them think

Response structure:
1. Clarifying question: "What do you already know about X?"
2. Series of guiding questions that build understanding
3. Minimal hints, not answers
4. Follow-up: "How would you test that idea?"

Example:
User: "What are decorators?"
You: "Interesting question! Let's explore this together.

First, what do you know about functions in Python? Can they:
- Take other functions as arguments?
- Return functions?
- Be assigned to variables?

Think about this: If you wanted to add logging to 10 different functions, what approaches 
could you take?

Here's a puzzle: What do you think this code does?
```python
def outer(func):
    def inner():
        print('Before')
        func()
        print('After')
    return inner
```

Take a moment to trace through it. What gets returned? When does each print happen?

Once you've thought about it, try running it with a simple function. What did you discover?"

Be patient. Guide, don't tell. Let them discover."""

    else:
        # Default fallback
        return """You are a helpful Python programming tutor.

Provide clear, accurate answers with code examples when appropriate.
Be encouraging and supportive of the learner."""


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
        
        # Store high-quality Q&A pairs in vector database for self-improving RAG
        response_data = _format_response(result)
        quality_score = response_data.evaluation.total_score
        
        if quality_score >= 85.0:  # Only store high-quality answers
            from app.services.qa_storage import store_qa_if_high_quality
            
            stored = await store_qa_if_high_quality(
                session=session,
                question=request.question,
                answer=response_data.answer,
                quality_score=quality_score,
                min_quality_threshold=85.0,
            )
            
            if stored:
                logger.info(
                    "chat_query.qa_stored",
                    question=request.question[:50],
                    quality_score=quality_score,
                )
        
        return Response(
            content=response_data.model_dump_json(),
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


@router.post("/quick-qa", response_model=QuickChatResponse, status_code=status.HTTP_200_OK)
async def quick_qa(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db_session),
    secret_store: SecretStore = Depends(get_secret_store_dependency),
) -> QuickChatResponse:
    """
    Quick Q&A endpoint for AXIS AI Chat with 3 teaching modes.
    
    Teaching Modes:
    - coach: Direct explanations with examples (default)
    - hybrid: Balanced questions + explanations
    - socratic: Guided discovery through questions
    
    Strategy:
    1. RAG-first: Retrieve documents from knowledge base
    2. Check if RAG is sufficient (≥10 docs)
    3. If insufficient: Fallback to Tavily + RAG
    4. Apply teaching mode prompt
    5. Maintain conversation context (last 10 messages)
    6. No quality evaluation (fast response)
    """
    try:
        from app.core.config import get_settings
        from app.vectorstore.pgvector_store import PGVectorStore
        from app.clients.embeddings import get_embedding_client
        from app.graph.tavily_research import TavilyResearchClient
        from app.providers.factory import get_chat_model
        from langchain.schema import HumanMessage, SystemMessage, AIMessage
        
        settings = get_settings()
        teaching_mode = request.teaching_mode or "coach"
        
        logger.info("quick_qa.start", question=request.question[:50], mode=teaching_mode)
        
        # 1. RAG Retrieval (higher limit for chat mode)
        embedding_client = get_embedding_client()
        vector_store = PGVectorStore(session=session)
        
        # Generate embedding for the question
        embeddings = await embedding_client.embed_documents([request.question])
        question_embedding = embeddings[0] if embeddings else []
        
        rag_docs = await vector_store.similarity_search(
            embedding=question_embedding,
            limit=settings.chat_mode_rag_limit,
            max_distance=settings.chat_mode_similarity_threshold,
        )
        
        logger.info("quick_qa.rag_retrieved", count=len(rag_docs))
        
        # 2. Check if RAG is sufficient
        rag_sufficient = len(rag_docs) >= settings.chat_mode_min_docs
        web_results = []
        
        if not rag_sufficient:
            # 3. Fallback to Tavily
            logger.info("quick_qa.tavily_fallback", rag_count=len(rag_docs))
            if settings.tavily_api_key:
                try:
                    tavily_client = TavilyResearchClient(api_key=settings.tavily_api_key)
                    web_results = await tavily_client.search_prioritized(
                        query=request.question,
                        depth="quick",
                        max_results=5,
                    )
                    logger.info("quick_qa.tavily_retrieved", count=len(web_results))
                except Exception as e:
                    logger.warning("quick_qa.tavily_failed", error=str(e))
        
        # 4. Build context from sources
        context_parts = []
        
        # Add RAG documents
        for i, doc in enumerate(rag_docs, 1):
            content = doc.content if hasattr(doc, 'content') else str(doc)
            context_parts.append(f"[Source {i} - RAG Document]\n{content}\n")
        
        # Add web results if used
        for i, result in enumerate(web_results, len(rag_docs) + 1):
            content = result.get('content', '') if isinstance(result, dict) else str(result)
            context_parts.append(f"[Source {i} - Web]\n{content}\n")
        
        context = "\n".join(context_parts)
        
        # 5. Build conversation history (last 10 messages)
        history_limit = settings.chat_mode_history_limit
        recent_history = request.history[-history_limit:] if len(request.history) > history_limit else request.history
        
        messages = []
        
        # Get teaching mode-specific system prompt
        teaching_prompt = get_teaching_mode_prompt(teaching_mode)
        
        # Combine with context
        full_system_prompt = f"""{teaching_prompt}

Available Sources:
{context if context else "No specific sources available. Use your general Python knowledge."}

Remember to maintain your teaching style ({teaching_mode} mode) while using these sources to ensure accuracy."""
        
        messages.append(SystemMessage(content=full_system_prompt))
        
        # Add conversation history
        for turn in recent_history:
            if turn.role == "user":
                messages.append(HumanMessage(content=turn.content))
            else:
                messages.append(AIMessage(content=turn.content))
        
        # Add current question
        messages.append(HumanMessage(content=request.question))
        
        # 6. Generate answer
        model_name = request.model or settings.openai_chat_model
        llm = await get_chat_model(
            provider=request.provider,
            model=model_name,
            temperature=settings.chat_mode_temperature,
            secret_store=secret_store,
            secret_token=request.secret_token,
        )
        
        logger.info("quick_qa.generating", model=model_name, mode=teaching_mode, temperature=settings.chat_mode_temperature)
        response = await llm.ainvoke(messages)
        answer = response.content
        
        logger.info("quick_qa.success", answer_length=len(answer), sources=len(rag_docs) + len(web_results), mode=teaching_mode)
        
        # Store chat Q&A pairs in vector database (no quality filter for chat mode)
        from app.services.qa_storage import store_chat_qa_pair
        
        stored = await store_chat_qa_pair(
            session=session,
            question=request.question,
            answer=answer,
            teaching_mode=teaching_mode,
            sources_used=len(rag_docs) + len(web_results),
        )
        
        if stored:
            logger.info(
                "quick_qa.qa_stored",
                question=request.question[:50],
                teaching_mode=teaching_mode,
            )
        
        return QuickChatResponse(
            answer=answer,
            sources_used=len(rag_docs) + len(web_results),
            rag_only=rag_sufficient,
        )
        
    except Exception as e:
        logger.error("quick_qa.error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick Q&A failed: {str(e)}"
        )

