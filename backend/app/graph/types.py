"""State definitions for LangGraph orchestration."""

from __future__ import annotations

from typing import Any, TypedDict


class GraphState(TypedDict, total=False):
    question: str
    history: list[dict[str, str]]
    provider: str
    documents: list[dict[str, Any]]
    web_results: list[dict[str, Any]]
    answer: str
    citations: list[dict[str, Any]]
    evaluation: dict[str, Any]
    retry_count: int
    revision_feedback: list[str]
    
    # Multi-agent pipeline fields
    complexity: str  # simple | standard | critical
    scenario: str  # Micro-scenario from Agent 1
    story_content: str  # Narrative from Agent 2
    narrative_evaluation: dict[str, Any]  # Quality Gate 2 results
    aethelgard_evaluation: dict[str, Any]  # Quality Gate 3 results
    technical_baseline_score: float  # For quality preservation check
    story_retry_count: int  # Retry counter for story regeneration
    polish_retry_count: int  # Retry counter for polish regeneration
    
    enriched_answer: str | None  # Final enriched version (optional)
    enrichment_applied: bool  # Track if enrichment was applied
    enrichment_aborted: bool  # Track if enrichment was aborted
    abort_reason: str | None  # Reason for abort
    
    # Technical Compiler fields
    compiled_answer: str | None  # Output from Technical Compiler
    compiler_evaluation: dict[str, Any] | None  # Quality Gate 2 results
    compiler_retry_count: int  # Retry counter for compiler

