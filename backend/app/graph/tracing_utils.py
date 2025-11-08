"""LangSmith tracing utilities for research pipeline metrics."""

from functools import wraps
from typing import Any, Callable

from langsmith import traceable

from app.core.logging import get_logger

logger = get_logger(__name__)


def trace_research_step(step_name: str):
    """
    Decorator to trace research pipeline steps in LangSmith.
    
    Captures:
    - Step name and duration
    - Input/output sizes
    - Research mode
    - Document/web result counts
    - Quality scores
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @traceable(
            name=f"research_pipeline.{step_name}",
            run_type="chain",
            tags=["research-engine", step_name],
        )
        async def wrapper(*args, **kwargs):
            # Extract state if available
            state = kwargs.get("state") or (args[1] if len(args) > 1 else None)
            
            # Log input metadata
            metadata = {}
            if state:
                metadata["question_length"] = len(state.get("question", ""))
                metadata["research_mode"] = getattr(args[0], "research_mode", "standard")
                metadata["retry_count"] = state.get("retry_count", 0)
                
                if "documents" in state:
                    metadata["rag_docs_count"] = len(state.get("documents", []))
                if "web_results" in state:
                    metadata["web_results_count"] = len(state.get("web_results", []))
                if "evaluation" in state:
                    eval_data = state.get("evaluation", {})
                    metadata["quality_score"] = eval_data.get("total_score", 0)
                    metadata["quality_passed"] = eval_data.get("passed", False)
            
            logger.info(f"trace.{step_name}.start", **metadata)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Log output metadata
            if isinstance(result, dict):
                output_metadata = {}
                if "documents" in result:
                    output_metadata["rag_docs_count"] = len(result.get("documents", []))
                if "web_results" in result:
                    output_metadata["web_results_count"] = len(result.get("web_results", []))
                if "answer" in result:
                    output_metadata["answer_length"] = len(result.get("answer", ""))
                if "enriched_answer" in result:
                    output_metadata["enriched_answer_length"] = len(result.get("enriched_answer", ""))
                if "evaluation" in result:
                    eval_data = result.get("evaluation", {})
                    output_metadata["quality_score"] = eval_data.get("total_score", 0)
                
                logger.info(f"trace.{step_name}.complete", **output_metadata)
            
            return result
        
        return wrapper
    return decorator


def add_research_metadata(state: dict[str, Any]) -> dict[str, Any]:
    """
    Extract research pipeline metadata for LangSmith tracking.
    
    Returns a dict of metrics to be logged with each trace.
    """
    metadata = {
        "question": state.get("question", "")[:100],  # Truncate for readability
        "provider": state.get("provider", "unknown"),
        "retry_count": state.get("retry_count", 0),
    }
    
    # RAG metrics
    documents = state.get("documents", [])
    if documents:
        metadata["rag_docs_count"] = len(documents)
        metadata["rag_top_score"] = documents[0].get("score", 0) if documents else 0
        metadata["rag_avg_score"] = sum(d.get("score", 0) for d in documents) / len(documents) if documents else 0
    
    # Tavily metrics
    web_results = state.get("web_results", [])
    if web_results:
        metadata["tavily_results_count"] = len(web_results)
        # Count by tier
        tier_counts = {}
        for result in web_results:
            tier = result.get("priority_tier", "unknown")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        metadata["tavily_tier_distribution"] = tier_counts
    
    # Quality metrics
    evaluation = state.get("evaluation", {})
    if evaluation:
        metadata["quality_score"] = evaluation.get("total_score", 0)
        metadata["quality_passed"] = evaluation.get("passed", False)
        metadata["coverage_score"] = evaluation.get("coverage_score", 0)
        metadata["citation_density"] = evaluation.get("citation_density", 0)
    
    # Answer metrics
    if "answer" in state:
        metadata["answer_length"] = len(state.get("answer", ""))
        metadata["answer_word_count"] = len(state.get("answer", "").split())
    
    # Enrichment metrics
    if "enriched_answer" in state:
        metadata["enriched_answer_length"] = len(state.get("enriched_answer", ""))
        metadata["enrichment_applied"] = state.get("enrichment_applied", False)
    
    return metadata



