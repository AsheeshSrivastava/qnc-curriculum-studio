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
    
    # Sequential Pipeline fields (Agents 1-2)
    synthesis_output: str | None  # Output from Agent 1: Research & Synthesis
    structured_output: str | None  # Output from Agent 2: Structure Transformer
    gate_1_result: dict[str, Any] | None  # Quality Gate 1 results
    gate_2_result: dict[str, Any] | None  # Quality Gate 2 results
    synthesis_retry_count: int  # Retry counter for Agent 1
    structure_retry_count: int  # Retry counter for Agent 2
    
    # Technical Compiler fields (Agent 3)
    compiled_answer: str | None  # Output from Technical Compiler
    compiler_evaluation: dict[str, Any] | None  # Quality Gate 3 results
    compiler_retry_count: int  # Retry counter for compiler

