"""Schemas for chat endpoints."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from app.providers.base import ProviderName


class ChatHistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    provider: ProviderName = Field(default="openai")
    secret_token: Optional[str] = Field(
        default=None,
        description="Opaque token representing a user-supplied provider key.",
    )
    history: list[ChatHistoryTurn] = Field(default_factory=list)
    model: Optional[str] = Field(
        default=None,
        description="Optional model override (e.g., gpt-4o, gpt-4o-mini, o1-preview).",
    )
    mode: Literal["chat", "generate"] = Field(
        default="generate",
        description="Mode: 'chat' for quick Q&A, 'generate' for full pipeline.",
    )


class Citation(BaseModel):
    id: str
    source: Optional[str] = None
    type: Literal["document", "web"]
    score: Optional[float] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationSummary(BaseModel):
    total_score: float
    passed: bool
    coverage_score: float
    citation_density: float
    exec_ok: bool
    scope_ok: bool
    feedback: list[str]
    criteria: dict[str, dict[str, Any]]


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    evaluation: EvaluationSummary


class QuickChatResponse(BaseModel):
    """Simplified response for chat mode (no quality evaluation)."""
    answer: str
    sources_used: int = Field(description="Number of sources used (RAG + Tavily)")
    rag_only: bool = Field(description="Whether answer was generated from RAG only (no Tavily)")


class ExportFormat(str):
    MARKDOWN = "markdown"
    JSON = "json"
    PDF = "pdf"


class ChatExportRequest(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    evaluation: Optional[EvaluationSummary] = None
    format: Literal["markdown", "json", "pdf"] = Field(default="markdown")


class StreamEvent(BaseModel):
    type: Literal["status", "documents", "web_results", "answer", "evaluation", "done"]
    payload: dict[str, Any] = Field(default_factory=dict)




