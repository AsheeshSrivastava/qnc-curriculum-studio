"""LangGraph orchestration for research assistant."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession
from tavily import TavilyClient

from app.clients.embeddings import get_embedding_client
from app.core.config import get_settings
from app.core.logging import get_logger
from app.graph.types import GraphState
from app.providers.base import ProviderName
from app.providers.factory import get_chat_model
from app.quality.evaluator import QualityEvaluator
from app.security.secret_store import SecretStore
from app.vectorstore.pgvector_store import PGVectorStore
from app.graph.narrative_enricher import NarrativeEnricher
from app.graph.question_classifier import QuestionClassifier
from app.graph.tavily_research import TavilyResearchClient
from app.graph.complexity_classifier import ComplexityClassifier
from app.graph.scenario_architect import ScenarioArchitect
from app.graph.cot_storyteller import CoTStoryteller
from app.graph.technical_compiler import TechnicalCompiler
from app.graph.research_synthesis_agent import ResearchSynthesisAgent
from app.graph.structure_transformer_agent import StructureTransformerAgent
from app.graph.quality_gates import QualityGates
from app.graph.narrative_enrichment_v2 import NarrativeEnrichmentAgent
from app.quality.narrative_evaluator import NarrativeQualityEvaluator
from app.quality.aethelgard_evaluator import AethelgardQualityEvaluator
from app.quality.compiler_evaluator import CompilerQualityEvaluator

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a research-grade AI assistant specializing in Python programming for curriculum development.

MISSION: Create comprehensive, curriculum-grade technical content that synthesizes multiple sources into a coherent learning experience.

QUALITY TARGET: 85+ points (will be compiled/refined later)

=== ⚠️ NON-NEGOTIABLE REQUIREMENTS (AUTOMATIC FAILURE IF MISSING) ===

1. **CODE BLOCKS**: You MUST include 3-5 Python code examples in ```python blocks
   - If you submit without code blocks, you FAIL automatically
   - Each block must be runnable and include comments
   
2. **MARKDOWN FORMATTING**: You MUST use proper markdown structure
   - Use ## for main sections
   - Use ### for subsections
   - Add blank lines between paragraphs
   - NO walls of text!

3. **STRUCTURE**: Follow the exact template provided below
   - Copy the markdown structure
   - Fill in the content
   - Keep the headers

=== CRITICAL: MULTI-SOURCE SYNTHESIS ===

You will receive 15-25 sources (RAG documents + web results). Your job is to:

1. **IDENTIFY CORE THEMES**: What are the 3-5 main concepts across ALL sources?
2. **CROSS-REFERENCE**: When multiple sources discuss the same concept, synthesize them
3. **PRIORITIZE**: Official docs > Academic > Community content
4. **BUILD PROGRESSIVELY**: Start simple, add complexity, show advanced usage
5. **PRESERVE EVERY CITATION**: Each source must be cited at least once

=== CITATION DISCIPLINE (20 points - CRITICAL) ===

**RULE 1: CITE IMMEDIATELY**
Attach [doc-X] or [web-X] RIGHT AFTER the claim it supports:
✅ GOOD: "List comprehensions provide a concise syntax [doc-1] for creating lists [doc-3]."
❌ BAD: "List comprehensions provide a concise syntax for creating lists. [doc-1][doc-3]"

**RULE 2: USE ALL SOURCES**
- If you receive 23 sources, use ALL 23
- Each [doc-X] and [web-X] must appear at least once
- Spread citations throughout (not clustered)
- Aim for 1.5 citations per 150 words

**RULE 3: MULTI-SOURCE CLAIMS**
When synthesizing multiple sources on the same point:
"List comprehensions are faster than loops [doc-1][doc-5] and more Pythonic [web-2][doc-8]."

=== TECHNICAL CORRECTNESS (15 points) ===

**CODE BLOCKS**: Include 3-5 runnable examples
```python
# Simple example with output
numbers = [x**2 for x in range(5)]
# Output: [0, 1, 4, 9, 16]
```

**TECHNICAL TERMS**: Use backticks for all Python keywords
- `list`, `for`, `in`, `if`, `def`, `class`, `import`, `lambda`, etc.
- `comprehension`, `generator`, `iterator`, `iterable`

**PROGRESSIVE EXAMPLES**:
1. Basic: Simple list comprehension
2. Intermediate: With conditional
3. Advanced: Nested or with functions

=== SYNTHESIS FRAMEWORK ===

**STEP 1: SCAN ALL SOURCES (Mental Model)**
- What's the core concept?
- What variations/perspectives exist?
- What's the progression (simple → advanced)?

**STEP 2: OUTLINE BEFORE WRITING**
- Foundation (what it is)
- Mechanics (how it works)
- Variations (different forms)
- Comparisons (vs alternatives)
- Production use (real-world)

**STEP 3: WRITE WITH CITATIONS**
Every paragraph should have 2-4 citations from different sources.

=== MANDATORY RESPONSE TEMPLATE (COPY THIS STRUCTURE EXACTLY) ===

## Understanding [Concept Name]

[Opening paragraph: Define the concept clearly. Cite official docs.]

[Second paragraph: Explain why it matters in real projects. Cite multiple sources.]

### Basic Syntax

```python
# Simplest possible example with comments
# Show the core concept in 3-5 lines
[code here]
# Output: [expected result]
```

[Explanation paragraph: How does this code work? Cite syntax sources.]

## How It Works

[Paragraph: Internal mechanics. Cite technical sources.]

[Paragraph: Syntax variations. Show 2-3 different forms. Cite examples.]

### Intermediate Example

```python
# More realistic example with conditional or function
# 5-10 lines showing practical usage
[code here]
```

[Explanation: What's different from basic? When to use this? Cite tutorials.]

## Advanced Usage

[Paragraph: Advanced patterns. Cite community sources.]

### Advanced Example

```python
# Complex real-world scenario
# 10-15 lines with nested structures or edge cases
[code here]
```

[Paragraph: Edge cases and gotchas. Cite discussions.]

## Comparisons & Best Practices

[Paragraph: vs alternative approaches. Cite performance sources.]

[Paragraph: When to use vs not use. Cite best practices and style guides.]

## Real-World Applications

[Paragraph: Industry usage patterns. Cite real projects or case studies.]

[Closing paragraph: Summary of key takeaways.]

=== ⚠️ PRE-SUBMISSION VERIFICATION (COUNT BEFORE SUBMITTING) ===

STOP! Before you submit, COUNT these in your response:

1. **Code blocks** (```python): _____ (MUST be 3-5)
   - If < 3, ADD MORE CODE EXAMPLES NOW
   
2. **Markdown headers** (##, ###): _____ (MUST be 5-8)
   - If < 5, you're missing sections
   
3. **Paragraphs with blank lines**: _____ (MUST be 8-15)
   - If text is one big block, ADD LINE BREAKS
   
4. **Citations** ([doc-X], [web-X]): _____ (MUST be 15-25)
   - If < 15, you didn't use all sources
   
5. **Technical terms in backticks**: _____ (MUST be 10-20)
   - Examples: `list`, `for`, `comprehension`, `lambda`

6. **Learner-centered phrases**: _____ (MUST be 3-5)
   - Examples: "Let's explore", "You'll discover", "Consider"

If ANY count is below minimum, REVISE before submitting.

Additional checks:
□ Progressive complexity (simple → intermediate → advanced)
□ No fictional scenarios or storytelling
□ 8-28 words per sentence (check 3 random sentences)
□ Respectful, inclusive tone

=== PEOPLE-FIRST LANGUAGE ===

Use learner-centered framing:
- "Let's explore how..."
- "You'll discover that..."
- "Consider what happens when..."
- "This enables you to..."

Avoid:
- "Obviously", "simply", "just", "trivial"
- Negative judgment about learning struggles

=== FINAL REMINDER ===

Your output will be compiled into PSW format later. Focus on:
1. **TECHNICAL ACCURACY** - Every fact must be correct and cited
2. **COMPREHENSIVE SYNTHESIS** - Use ALL sources, show ALL perspectives
3. **PROGRESSIVE LEARNING** - Build from simple to advanced
4. **CITATION DISCIPLINE** - Attach [doc-X] to EVERY claim

Target: 85+ points. Quality over speed."""


class ResearchGraph:
    """Build and execute a LangGraph pipeline for answering Python research queries."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        secret_store: SecretStore,
        provider: ProviderName,
        secret_token: Optional[str],
        research_mode: Optional[str] = None,
    ) -> None:
        self.session = session
        self.secret_store = secret_store
        self.provider = provider
        self.secret_token = secret_token
        self.settings = get_settings()
        self.research_mode = research_mode or self.settings.research_mode
        self.embedding_client = get_embedding_client()
        self.vector_store = PGVectorStore(session)
        
        # Use prioritized Tavily research client
        self.tavily_research = (
            TavilyResearchClient(api_key=self.settings.tavily_api_key)
            if self.settings.tavily_api_key
            else None
        )
        
        self.quality_evaluator = QualityEvaluator()
        
        # Sequential Pipeline components (Agents 1-2)
        if self.settings.enable_sequential_pipeline:
            self.synthesis_agent = ResearchSynthesisAgent()
            self.structure_agent = StructureTransformerAgent()
            self.quality_gates = QualityGates()
        
        # Technical Compiler components (Agent 3)
        if self.settings.enable_technical_compiler:
            self.technical_compiler = TechnicalCompiler()
            self.compiler_evaluator = CompilerQualityEvaluator()
        else:
            self.technical_compiler = None
            self.compiler_evaluator = None
        
        # Narrative Enrichment Agent (Agent 4)
        if self.settings.enable_narrative_enrichment:
            logger.info("research_graph.init.agent_4_enabled", enable_narrative_enrichment=True)
            self.narrative_enrichment_agent = NarrativeEnrichmentAgent(
                secret_store=self.secret_store,
                provider=self.provider,
                secret_token=self.secret_token,
            )
            logger.info("research_graph.init.agent_4_initialized")
        else:
            logger.warning("research_graph.init.agent_4_disabled", enable_narrative_enrichment=False)
            self.narrative_enrichment_agent = None
        
        # Multi-agent pipeline components
        if self.settings.enable_multi_agent_pipeline:
            self.complexity_classifier = ComplexityClassifier()
            self.scenario_architect = ScenarioArchitect()
            self.cot_storyteller = CoTStoryteller()
            self.narrative_evaluator = NarrativeQualityEvaluator()
            self.aethelgard_evaluator = AethelgardQualityEvaluator()
            self.narrative_enricher = NarrativeEnricher()  # Aethelgard polish agent
        else:
            # Legacy single-agent enrichment
            self.complexity_classifier = None
            self.scenario_architect = None
            self.cot_storyteller = None
            self.narrative_evaluator = None
            self.aethelgard_evaluator = None
            self.narrative_enricher = (
                NarrativeEnricher()
                if self.settings.enable_narrative_enrichment
                else None
            )
        
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(GraphState)
        graph.add_node("research", self._parallel_research)
        
        # ========================================
        # NEW: SEQUENTIAL PIPELINE (Agents 1-2-3)
        # ========================================
        if self.settings.enable_sequential_pipeline:
            # Agent 1: Research & Synthesis
            graph.add_node("agent_1_synthesize", self._agent_1_synthesize)
            
            # Agent 2: Structure Transformer
            graph.add_node("agent_2_structure", self._agent_2_structure)
            
            # Agent 3: Technical Compiler (existing)
            if self.technical_compiler:
                graph.add_node("prepare_compiler", self._prepare_for_compiler)
                graph.add_node("compile_technical", self._compile_technical)
                graph.add_node("evaluate_compiler", self._evaluate_compiler)
                graph.add_node("recompile", self._recompile)
            
            # Agent 4: Narrative Enrichment (NEW)
            if self.settings.enable_narrative_enrichment:
                logger.info("research_graph.build.adding_agent_4_node")
                graph.add_node("agent_4_enrich", self._agent_4_enrich)
                logger.info("research_graph.build.agent_4_node_added")
            
            # Pipeline flow
            graph.set_entry_point("research")
            graph.add_edge("research", "agent_1_synthesize")
            
            # Quality Gate 1: Agent 1 output
            graph.add_conditional_edges(
                "agent_1_synthesize",
                self._gate_1_decision,
                {
                    "agent_2": "agent_2_structure",
                    "retry_agent_1": "agent_1_synthesize",
                },
            )
            
            # Quality Gate 2: Agent 2 output
            if self.technical_compiler:
                graph.add_conditional_edges(
                    "agent_2_structure",
                    self._gate_2_decision,
                    {
                        "compiler": "prepare_compiler",
                        "retry_agent_2": "agent_2_structure",
                    },
                )
                
                # Compiler pipeline (Agent 3)
                graph.add_edge("prepare_compiler", "compile_technical")
                graph.add_edge("compile_technical", "evaluate_compiler")
                
                # Quality Gate 3: Compiler evaluation
                if self.settings.enable_narrative_enrichment:
                    # If Agent 4 enabled, go to enrichment after compiler passes
                    logger.info("research_graph.build.routing_compiler_to_agent_4")
                    graph.add_conditional_edges(
                        "evaluate_compiler",
                        self._compiler_decision,
                        {"recompile": "recompile", "done": "agent_4_enrich"},
                    )
                    graph.add_edge("recompile", "evaluate_compiler")
                    graph.add_edge("agent_4_enrich", END)
                    logger.info("research_graph.build.agent_4_routing_complete")
                else:
                    # No Agent 4, end after compiler
                    graph.add_conditional_edges(
                        "evaluate_compiler",
                        self._compiler_decision,
                        {"recompile": "recompile", "done": END},
                    )
                    graph.add_edge("recompile", "evaluate_compiler")
            else:
                # No compiler, end after Agent 2
                graph.add_conditional_edges(
                    "agent_2_structure",
                    self._gate_2_decision,
                    {
                        "compiler": END,
                        "retry_agent_2": "agent_2_structure",
                    },
                )
        
        # ========================================
        # LEGACY: Multi-agent narrative pipeline
        # ========================================
        elif self.settings.enable_multi_agent_pipeline and self.complexity_classifier:
            # New 4-agent quality-first pipeline
            graph.add_node("classify_complexity", self._classify_complexity)
            graph.add_node("generate", self._generate_answer)
            graph.add_node("evaluate_quality", self._evaluate_answer)
            graph.add_node("rewrite_content", self._rewrite_answer)
            graph.add_node("create_scenario", self._create_scenario)
            graph.add_node("create_story", self._create_story)
            graph.add_node("evaluate_narrative", self._evaluate_narrative)
            graph.add_node("regenerate_story", self._regenerate_story)
            graph.add_node("apply_polish", self._apply_polish)
            graph.add_node("evaluate_aethelgard", self._evaluate_aethelgard)
            graph.add_node("repolish", self._repolish)
            
            # Pipeline flow
            graph.set_entry_point("research")
            graph.add_edge("research", "classify_complexity")
            graph.add_edge("classify_complexity", "generate")
            graph.add_edge("generate", "evaluate_quality")
            
            # Quality Gate 1: Technical evaluation
            graph.add_conditional_edges(
                "evaluate_quality",
                self._evaluation_decision,
                {"rewrite": "rewrite_content", "done": "create_scenario"},
            )
            graph.add_edge("rewrite_content", "evaluate_quality")
            
            # Agent 1: Scenario architect
            graph.add_edge("create_scenario", "create_story")
            
            # Agent 2: CoT storyteller
            graph.add_edge("create_story", "evaluate_narrative")
            
            # Quality Gate 2: Narrative evaluation
            graph.add_conditional_edges(
                "evaluate_narrative",
                self._narrative_decision,
                {
                    "regenerate": "regenerate_story",
                    "continue": "apply_polish",
                    "abort": END,
                },
            )
            graph.add_edge("regenerate_story", "evaluate_narrative")
            
            # Agent 3: Aethelgard polish
            graph.add_edge("apply_polish", "evaluate_aethelgard")
            
            # Quality Gate 3: Aethelgard evaluation
            graph.add_conditional_edges(
                "evaluate_aethelgard",
                self._aethelgard_decision,
                {
                    "repolish": "repolish",
                    "done": END,
                    "abort": END,
                },
            )
            graph.add_edge("repolish", "evaluate_aethelgard")
            
        # ========================================
        # LEGACY: Simple quality-first pipeline
        # ========================================
        else:
            # Quality-first pipeline with optional Technical Compiler
            graph.add_node("generate", self._generate_answer)
            graph.add_node("evaluate_quality", self._evaluate_answer)
            graph.add_node("rewrite_content", self._rewrite_answer)
            
            # Add Technical Compiler nodes if enabled
            if self.technical_compiler:
                graph.add_node("compile_technical", self._compile_technical)
                graph.add_node("evaluate_compiler", self._evaluate_compiler)
                graph.add_node("recompile", self._recompile)
            
            # Add legacy narrative enrichment if enabled (deprecated)
            if self.narrative_enricher:
                graph.add_node("enrich_narrative", self._enrich_narrative_legacy)
            
            graph.set_entry_point("research")
            graph.add_edge("research", "generate")
            graph.add_edge("generate", "evaluate_quality")
            
            # Quality Gate 1: Technical evaluation (95+ or retry up to 5x)
            if self.technical_compiler:
                # After quality gate 1, go to compiler
                graph.add_conditional_edges(
                    "evaluate_quality",
                    self._evaluation_decision,
                    {"rewrite": "rewrite_content", "done": "compile_technical"},
                )
                graph.add_edge("rewrite_content", "evaluate_quality")
                
                # Compiler pipeline
                graph.add_edge("compile_technical", "evaluate_compiler")
                
                # Quality Gate 2: Compiler evaluation (95+)
                graph.add_conditional_edges(
                    "evaluate_compiler",
                    self._compiler_decision,
                    {"recompile": "recompile", "done": END},
                )
                graph.add_edge("recompile", "evaluate_compiler")
            elif self.narrative_enricher:
                # Legacy enrichment path
                graph.add_conditional_edges(
                    "evaluate_quality",
                    self._evaluation_decision_with_enrichment,
                    {"rewrite": "rewrite_content", "enrich": "enrich_narrative", "done": END},
                )
                graph.add_edge("enrich_narrative", END)
                graph.add_edge("rewrite_content", "evaluate_quality")
            else:
                # Simple path: just technical generation and evaluation
                graph.add_conditional_edges(
                    "evaluate_quality",
                    self._evaluation_decision,
                    {"rewrite": "rewrite_content", "done": END},
                )
                graph.add_edge("rewrite_content", "evaluate_quality")

        return graph.compile()

    async def run(
        self,
        *,
        question: str,
        history: Optional[list[dict[str, str]]] = None,
    ) -> GraphState:
        initial_state: GraphState = {
            "question": question,
            "history": history or [],
            "provider": self.provider,
            "retry_count": 0,
            "synthesis_retry_count": 0,
            "structure_retry_count": 0,
        }
        return await self.graph.ainvoke(initial_state)

    async def _parallel_research(self, state: GraphState) -> GraphState:
        """
        Execute RAG retrieval and Tavily search in parallel for comprehensive research.
        
        Research depth determines retrieval limits:
        - quick: 10 docs, tier_1 only
        - standard: 15 docs, tier_1+2
        - deep: 20 docs, all tiers
        """
        question = state["question"]
        logger.info("graph.research.start", question=question, mode=self.research_mode)

        # Determine retrieval depth based on research mode
        depth_config = {
            "quick": {"rag_limit": 10, "tavily_results": 5},
            "standard": {"rag_limit": 15, "tavily_results": 5},  # Reduced from 8 to 5 for cost optimization
            "deep": {"rag_limit": 20, "tavily_results": 10},
        }
        config = depth_config.get(self.research_mode, depth_config["standard"])

        # Run RAG and Tavily in parallel
        rag_task = self._retrieve_documents_internal(question, config["rag_limit"])
        
        if self.settings.always_use_tavily and self.tavily_research:
            tavily_task = self._web_search_internal(question, config["tavily_results"])
            documents, web_results = await asyncio.gather(rag_task, tavily_task)
        else:
            documents = await rag_task
            web_results = []

        logger.info(
            "graph.research.complete",
            rag_docs=len(documents),
            web_results=len(web_results),
            mode=self.research_mode,
        )

        return {**state, "documents": documents, "web_results": web_results}

    async def _retrieve_documents_internal(
        self, question: str, limit: int
    ) -> list[dict[str, Any]]:
        """Internal RAG retrieval with configurable depth."""
        logger.info("graph.rag.start", question=question[:50], limit=limit)

        embeddings = await self.embedding_client.embed_documents([question])
        query_vector = embeddings[0]

        results = await self.vector_store.similarity_search(
            query_vector,
            limit=limit,
            max_distance=self.settings.retrieval_max_distance,
        )

        documents = [
            {
                "id": f"doc-{idx+1}",
                "document_id": str(item.document_id),
                "content": item.content,
                "score": float(item.score),
                "chunk_index": item.chunk_index,
                "metadata": item.metadata,
                "document_metadata": item.document_metadata,
                "document_title": item.document_title,
                "source_type": item.source_type,
                "source_uri": item.source_uri,
            }
            for idx, item in enumerate(results)
        ]

        logger.info("graph.rag.complete", count=len(documents))
        return documents

    def _should_web_search(self, state: GraphState) -> str:
        """Decide whether to trigger web search fallback.
        
        Strategy: Prioritize RAG. Only use web search if:
        1. No documents found at all, OR
        2. Very few documents (<2) AND poor quality (score > 0.5)
        
        This reduces latency by avoiding unnecessary web searches and LLM calls.
        """
        documents = state.get("documents", []) or []

        # If we have no documents at all, try web search
        if len(documents) == 0:
            logger.info("graph.decision.web_search", reason="no_documents")
            return "web_search"

        # If we have very few documents AND they're low quality, try web search
        if len(documents) < 2:
            top_score = documents[0]["score"]
            if top_score > 0.5:  # More conservative threshold
                logger.info("graph.decision.web_search", reason="low_quality", score=top_score)
                return "web_search"

        # Otherwise, use RAG documents (even if not perfect)
        logger.info("graph.decision.answer", doc_count=len(documents), top_score=documents[0]["score"])
        return "answer"

    async def _web_search_internal(
        self, question: str, max_results: int
    ) -> list[dict[str, Any]]:
        """Internal Tavily search with prioritized domains."""
        if not self.tavily_research:
            logger.warning("graph.tavily.disabled", reason="missing_tavily_key")
            return []

        logger.info("graph.tavily.start", question=question[:50], max_results=max_results)
        try:
            results = await self.tavily_research.search_prioritized(
                query=question,
                depth=self.research_mode,
                max_results=max_results,
            )
            
            # Format results with priority tier metadata
            web_results: list[dict[str, Any]] = []
            for idx, item in enumerate(results, start=1):
                web_results.append(
                    {
                        "id": f"web-{idx}",
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "summary": item.get("content") or item.get("snippet") or item.get("summary"),
                        "priority_tier": item.get("priority_tier", "tier_3"),
                        "tier_rank": item.get("tier_rank", 3),
                    }
                )

            logger.info("graph.tavily.complete", count=len(web_results))
            return web_results
            
        except Exception as e:
            logger.error("graph.tavily.error", error=str(e), exc_info=True)
            return []

    async def _generate_answer(self, state: GraphState) -> GraphState:
        question = state["question"]
        documents = state.get("documents", []) or []
        web_results = state.get("web_results", []) or []
        history = state.get("history", []) or []
        revision_feedback = state.get("revision_feedback", [])

        # Get model with technical temperature for deterministic, factual output
        model = await get_chat_model(
            self.provider,
            secret_store=self.secret_store,
            secret_token=self.secret_token,
        )
        
        # Configure temperature for research-grade output
        model.temperature = self.settings.technical_temperature

        documents_context, doc_citations = self._format_documents(documents)
        web_context, web_citations = self._format_web_results(web_results)
        citations = doc_citations + web_citations

        revision_suffix = ""
        if revision_feedback:
            bullet_list = "\n".join(f"- {item}" for item in revision_feedback)
            revision_suffix = (
                "\n\nPlease revise the answer to resolve the following quality issues:\n"
                f"{bullet_list}"
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                *[HumanMessage(content=entry["content"]) for entry in history],
                HumanMessage(
                    content=(
                        f"Question: {question}\n\n"
                        f"Document context:\n{documents_context or 'None'}\n\n"
                        f"Web context:\n{web_context or 'None'}"
                        f"{revision_suffix}"
                    )
                ),
            ]
        )

        messages = prompt.format_prompt().to_messages()
        
        logger.info(
            "graph.generate.start",
            temperature=model.temperature,
            rag_docs=len(documents),
            web_results=len(web_results),
            research_mode=self.research_mode,
        )
        
        response = await model.ainvoke(messages)
        answer = response.content if hasattr(response, 'content') else str(response)

        logger.info("graph.answer.complete", provider=self.provider)
        next_state = {**state, "answer": answer, "citations": citations}
        next_state.pop("revision_feedback", None)
        next_state.pop("evaluation", None)
        return next_state
    
    # ========================================
    # SEQUENTIAL PIPELINE METHODS (Agents 1-2)
    # ========================================
    
    async def _agent_1_synthesize(self, state: GraphState) -> GraphState:
        """
        Agent 1: Research & Synthesis
        
        Takes RAG + Tavily sources and generates technical content.
        """
        if not self.settings.enable_sequential_pipeline:
            # Fall back to old generation method
            return await self._generate_answer(state)
        
        question = state["question"]
        documents = state.get("documents", []) or []
        web_results = state.get("web_results", []) or []
        
        # Format sources for synthesis
        documents_context, doc_citations = self._format_documents(documents)
        web_context, web_citations = self._format_web_results(web_results)
        citations = doc_citations + web_citations
        
        sources_context = f"""
=== RAG DOCUMENTS ({len(documents)}) ===

{documents_context or 'None'}

=== WEB RESULTS ({len(web_results)}) ===

{web_context or 'None'}
"""
        
        logger.info(
            "agent_1.start",
            question=question[:100],
            rag_docs=len(documents),
            web_results=len(web_results),
        )
        
        # Run Agent 1
        synthesis = await self.synthesis_agent.synthesize(
            question=question,
            sources_context=sources_context,
        )
        
        # Run Quality Gate 1
        gate_result = self.quality_gates.gate_1_technical(synthesis)
        
        logger.info(
            "agent_1.complete",
            passed=gate_result.passed,
            metrics=gate_result.metrics,
        )
        
        # Increment retry counter for next attempt (if gate fails)
        current_retry = state.get("synthesis_retry_count", 0)
        next_retry = current_retry + 1 if not gate_result.passed else current_retry
        
        return {
            **state,
            "synthesis_output": synthesis,
            "citations": citations,
            "gate_1_result": {
                "passed": gate_result.passed,
                "message": gate_result.message,
                "metrics": gate_result.metrics,
            },
            "synthesis_retry_count": next_retry,
        }
    
    def _gate_1_decision(self, state: GraphState) -> str:
        """Decide whether to proceed to Agent 2 or retry Agent 1."""
        gate_result = state.get("gate_1_result", {})
        
        if gate_result.get("passed"):
            return "agent_2"
        
        retry_count = state.get("synthesis_retry_count", 0)
        if retry_count >= 2:
            logger.warning(
                "agent_1.max_retries",
                retry_count=retry_count,
                message="Proceeding despite gate failure",
            )
            return "agent_2"
        
        logger.info(
            "agent_1.retry",
            retry_count=retry_count + 1,
            reason=gate_result.get("message"),
        )
        return "retry_agent_1"
    
    async def _agent_2_structure(self, state: GraphState) -> GraphState:
        """
        Agent 2: Structure Transformer
        
        Takes technical synthesis and adds markdown structure.
        """
        synthesis = state.get("synthesis_output", "")
        
        if not synthesis:
            logger.error("agent_2.no_input", message="No synthesis output from Agent 1")
            return state
        
        logger.info(
            "agent_2.start",
            input_length=len(synthesis),
        )
        
        # Run Agent 2
        structured = await self.structure_agent.transform(
            technical_content=synthesis,
        )
        
        # Run Quality Gate 2
        gate_result = self.quality_gates.gate_2_structure(structured)
        
        logger.info(
            "agent_2.complete",
            passed=gate_result.passed,
            metrics=gate_result.metrics,
        )
        
        # Increment retry counter for next attempt (if gate fails)
        current_retry = state.get("structure_retry_count", 0)
        next_retry = current_retry + 1 if not gate_result.passed else current_retry
        
        return {
            **state,
            "structured_output": structured,
            "gate_2_result": {
                "passed": gate_result.passed,
                "message": gate_result.message,
                "metrics": gate_result.metrics,
            },
            "structure_retry_count": next_retry,
        }
    
    def _gate_2_decision(self, state: GraphState) -> str:
        """Decide whether to proceed to Agent 3 (compiler) or retry Agent 2."""
        gate_result = state.get("gate_2_result", {})
        
        if gate_result.get("passed"):
            return "compiler"
        
        retry_count = state.get("structure_retry_count", 0)
        if retry_count >= 2:
            logger.warning(
                "agent_2.max_retries",
                retry_count=retry_count,
                message="Proceeding despite gate failure",
            )
            return "compiler"
        
        logger.info(
            "agent_2.retry",
            retry_count=retry_count + 1,
            reason=gate_result.get("message"),
        )
        return "retry_agent_2"
    
    async def _prepare_for_compiler(self, state: GraphState) -> GraphState:
        """
        Prepare structured output for Technical Compiler (Agent 3).
        
        If sequential pipeline is enabled, use structured_output as the answer.
        Otherwise, use the existing answer from _generate_answer.
        """
        if self.settings.enable_sequential_pipeline:
            structured = state.get("structured_output", "")
            if structured:
                logger.info(
                    "pipeline.prepare_compiler",
                    using="structured_output",
                    length=len(structured),
                )
                return {**state, "answer": structured}
        
        # Fall back to existing answer
        logger.info(
            "pipeline.prepare_compiler",
            using="existing_answer",
        )
        return state

    async def _evaluate_answer(self, state: GraphState) -> GraphState:
        answer = state.get("answer", "")
        documents = state.get("documents", []) or []
        citations = state.get("citations", []) or []

        report = self.quality_evaluator.evaluate(
            question=state["question"],
            answer=answer,
            documents=documents,
            citations=citations,
        ).to_dict()

        logger.info(
            "graph.evaluate.complete",
            passed=report["passed"],
            total_score=report["total_score"],
        )
        return {**state, "evaluation": report}

    def _evaluation_decision(self, state: GraphState) -> str:
        evaluation = state.get("evaluation") or {}
        if not evaluation or evaluation.get("passed"):
            return "done"

        retry_count = state.get("retry_count", 0)
        if retry_count >= 5:  # Allow up to 5 retries for 95+ quality
            return "done"

        if not evaluation.get("feedback"):
            return "done"

        return "rewrite"

    async def _rewrite_answer(self, state: GraphState) -> GraphState:
        evaluation = state.get("evaluation") or {}
        feedback = evaluation.get("feedback", [])
        retry_count = state.get("retry_count", 0) + 1
        updated_state = {**state, "revision_feedback": feedback, "retry_count": retry_count}
        rewritten_state = await self._generate_answer(updated_state)
        rewritten_state.pop("evaluation", None)
        return rewritten_state

    def _format_documents(self, documents: list[dict[str, Any]]):
        if not documents:
            return "", []

        formatted_chunks: list[str] = []
        citations: list[dict[str, Any]] = []

        for idx, doc in enumerate(documents, start=1):
            citation_id = f"doc-{idx}"
            title = doc.get("document_title") or "Uploaded Document"
            source = doc.get("source_uri") or title
            excerpt = doc.get("content", "")[:1200]

            formatted_chunks.append(
                f"[{citation_id}] {title}\nScore: {doc.get('score'):.4f}\n{excerpt}"
            )
            citations.append(
                {
                    "id": citation_id,
                    "source": source,
                    "type": "document",
                    "score": doc.get("score"),
                    "metadata": {
                        "document_id": doc.get("document_id"),
                        "chunk_index": doc.get("chunk_index"),
                    },
                }
            )

        return "\n\n".join(formatted_chunks), citations

    def _format_web_results(self, results: list[dict[str, Any]]):
        if not results:
            return "", []

        formatted: list[str] = []
        citations: list[dict[str, Any]] = []

        for item in results:
            formatted.append(
                f"[{item['id']}] {item.get('title')}\nURL: {item.get('url')}\n{item.get('summary')}"
            )
            citations.append(
                {
                    "id": item["id"],
                    "source": item.get("url"),
                    "type": "web",
                }
            )

        return "\n\n".join(formatted), citations

    def _evaluation_decision_with_enrichment(self, state: GraphState) -> str:
        """Decide next step after evaluation: rewrite, enrich, or done.
        
        Decision logic:
        1. If evaluation failed and retry_count < 5: rewrite
        2. If evaluation passed and should_enrich: enrich
        3. Otherwise: done
        """
        evaluation = state.get("evaluation") or {}
        
        # Check if we need to rewrite (quality too low)
        if not evaluation or not evaluation.get("passed"):
            retry_count = state.get("retry_count", 0)
            if retry_count >= 5:  # Allow up to 5 retries for 95+ quality
                # Max retries reached, check if we should enrich anyway
                if self._should_enrich_answer(state):
                    return "enrich"
                return "done"
            
            if evaluation.get("feedback"):
                return "rewrite"
        
        # Quality passed, check if we should enrich
        if self._should_enrich_answer(state):
            return "enrich"
        
        return "done"

    def _should_enrich_answer(self, state: GraphState) -> bool:
        """Determine if answer should receive narrative enrichment.
        
        Uses question classifier and quality score to decide.
        """
        if not self.narrative_enricher:
            return False
        
        question = state.get("question", "")
        evaluation = state.get("evaluation") or {}
        quality_score = evaluation.get("total_score", 0.0)
        
        return QuestionClassifier.should_enrich(
            question=question,
            quality_score=quality_score,
            quality_threshold=self.settings.enrichment_quality_threshold,
        )

    async def _enrich_narrative(self, state: GraphState) -> GraphState:
        """Apply narrative enrichment to transform technical answer into engaging learning experience.
        
        This is the final step - enrichment failures gracefully return original answer.
        """
        if not self.narrative_enricher:
            logger.warning("graph.enrich.disabled", reason="no_enricher")
            return {**state, "enrichment_applied": False}
        
        answer = state.get("answer", "")
        citations = state.get("citations", []) or []
        evaluation = state.get("evaluation") or {}
        quality_score = evaluation.get("total_score")
        
        logger.info(
            "graph.enrich.start",
            question=state.get("question", "")[:50],
            answer_length=len(answer),
            quality_score=quality_score,
        )
        
        try:
            enriched = await self.narrative_enricher.enrich(
                technical_answer=answer,
                citations=citations,
                quality_score=quality_score,
            )
            
            if enriched:
                logger.info(
                    "graph.enrich.success",
                    original_length=len(answer),
                    enriched_length=len(enriched),
                )
                return {
                    **state,
                    "enriched_answer": enriched,
                    "enrichment_applied": True,
                }
            else:
                logger.warning("graph.enrich.failed", reason="enricher_returned_none")
                return {**state, "enrichment_applied": False}
                
        except Exception as e:
            logger.error(
                "graph.enrich.error",
                error=str(e),
                exc_info=True,
            )
            # Graceful degradation - return original answer
            return {**state, "enrichment_applied": False}
    
    # ========== Multi-Agent Pipeline Methods ==========
    
    async def _classify_complexity(self, state: GraphState) -> GraphState:
        """Classify question complexity (simple/standard/critical)."""
        if not self.complexity_classifier:
            return {**state, "complexity": "standard"}
        
        question = state["question"]
        complexity = await self.complexity_classifier.classify(question)
        
        logger.info("graph.complexity.classified", question=question[:50], complexity=complexity)
        return {**state, "complexity": complexity}
    
    async def _create_scenario(self, state: GraphState) -> GraphState:
        """Agent 1: Create micro-scenario."""
        if not self.scenario_architect:
            return {**state, "scenario": "SKIP"}
        
        technical_answer = state.get("answer", "")
        complexity = state.get("complexity", "standard")
        evaluation = state.get("evaluation") or {}
        
        # Store baseline score for quality preservation check
        technical_baseline_score = evaluation.get("total_score", 0.0)
        
        scenario = await self.scenario_architect.create_scenario(
            technical_answer=technical_answer,
            complexity=complexity,
        )
        
        logger.info("graph.scenario.created", complexity=complexity, skipped=(scenario == "SKIP"))
        return {
            **state,
            "scenario": scenario,
            "technical_baseline_score": technical_baseline_score,
            "story_retry_count": 0,
            "polish_retry_count": 0,
        }
    
    async def _create_story(self, state: GraphState) -> GraphState:
        """Agent 2: Create narrative with Chain-of-Thought reasoning."""
        if not self.cot_storyteller:
            return {**state, "story_content": state.get("answer", "")}
        
        technical_answer = state.get("answer", "")
        scenario = state.get("scenario", "SKIP")
        citations = state.get("citations", []) or []
        complexity = state.get("complexity", "standard")
        
        story = await self.cot_storyteller.create_story(
            technical_answer=technical_answer,
            scenario=scenario,
            citations=citations,
            complexity=complexity,
        )
        
        logger.info("graph.story.created", complexity=complexity, story_length=len(story))
        return {**state, "story_content": story}
    
    async def _evaluate_narrative(self, state: GraphState) -> GraphState:
        """Quality Gate 2: Evaluate narrative quality."""
        if not self.narrative_evaluator:
            return {**state, "narrative_evaluation": {"passed": True, "total_score": 100.0}}
        
        story_content = state.get("story_content", "")
        technical_answer = state.get("answer", "")
        citations = state.get("citations", []) or []
        complexity = state.get("complexity", "standard")
        
        evaluation = self.narrative_evaluator.evaluate(
            narrative_content=story_content,
            technical_answer=technical_answer,
            citations=citations,
            complexity=complexity,
        )
        
        logger.info(
            "graph.narrative.evaluated",
            passed=evaluation.passed,
            total_score=evaluation.total_score,
            tech_preservation=evaluation.technical_preservation,
        )
        
        return {**state, "narrative_evaluation": evaluation.to_dict()}
    
    def _narrative_decision(self, state: GraphState) -> str:
        """Decide after Quality Gate 2: regenerate, continue, or abort."""
        narrative_eval = state.get("narrative_evaluation") or {}
        
        # ABORT TRIGGER 1: Technical facts compromised
        tech_preservation = narrative_eval.get("technical_preservation", 0)
        if tech_preservation < 25:  # Hard floor
            logger.error(
                "graph.narrative.abort",
                reason="technical_preservation_failed",
                score=tech_preservation,
            )
            return "abort"
        
        # Check if passed
        if narrative_eval.get("passed"):
            return "continue"
        
        # Check retry count
        retry_count = state.get("story_retry_count", 0)
        if retry_count >= 1:
            # Max retries, continue anyway (technical facts are intact)
            logger.warning("graph.narrative.max_retries", score=narrative_eval.get("total_score"))
            return "continue"
        
        # Retry if we have feedback
        if narrative_eval.get("feedback"):
            return "regenerate"
        
        return "continue"
    
    async def _regenerate_story(self, state: GraphState) -> GraphState:
        """Regenerate story with feedback from narrative evaluation."""
        narrative_eval = state.get("narrative_evaluation") or {}
        feedback = narrative_eval.get("feedback", [])
        retry_count = state.get("story_retry_count", 0) + 1
        
        logger.info("graph.story.regenerate", retry_count=retry_count, feedback_count=len(feedback))
        
        # For now, just increment retry and try again
        # In future, could pass feedback to storyteller
        updated_state = {**state, "story_retry_count": retry_count}
        return await self._create_story(updated_state)
    
    async def _apply_polish(self, state: GraphState) -> GraphState:
        """Agent 3: Apply Aethelgard brand polish and RAG optimization."""
        if not self.narrative_enricher:
            return {**state, "enriched_answer": state.get("story_content", "")}
        
        story_content = state.get("story_content", "")
        citations = state.get("citations", []) or []
        
        polished = await self.narrative_enricher.enrich(
            story_content=story_content,
            citations=citations,
        )
        
        logger.info("graph.polish.applied", polished_length=len(polished))
        return {**state, "enriched_answer": polished}
    
    async def _evaluate_aethelgard(self, state: GraphState) -> GraphState:
        """Quality Gate 3: Evaluate Aethelgard brand quality."""
        if not self.aethelgard_evaluator:
            return {**state, "aethelgard_evaluation": {"passed": True, "total_score": 100.0}}
        
        enriched_answer = state.get("enriched_answer", "")
        technical_baseline_score = state.get("technical_baseline_score", 0.0)
        
        evaluation = self.aethelgard_evaluator.evaluate(
            content=enriched_answer,
            technical_baseline_score=technical_baseline_score,
        )
        
        logger.info(
            "graph.aethelgard.evaluated",
            passed=evaluation.passed,
            total_score=evaluation.total_score,
            brand_voice=evaluation.brand_voice,
        )
        
        return {**state, "aethelgard_evaluation": evaluation.to_dict()}
    
    def _aethelgard_decision(self, state: GraphState) -> str:
        """Decide after Quality Gate 3: repolish, done, or abort."""
        aethelgard_eval = state.get("aethelgard_evaluation") or {}
        technical_baseline_score = state.get("technical_baseline_score", 0.0)
        tolerance = self.settings.quality_degradation_tolerance
        
        # ABORT TRIGGER 2: Quality degraded significantly
        # Re-evaluate final quality to check for degradation
        enriched_answer = state.get("enriched_answer", "")
        final_quality = self.quality_evaluator.evaluate(
            question=state["question"],
            answer=enriched_answer,
            documents=state.get("documents", []) or [],
            citations=state.get("citations", []) or [],
        )
        
        if final_quality.total_score < technical_baseline_score - tolerance:
            logger.error(
                "graph.aethelgard.abort",
                reason="quality_degraded",
                baseline=technical_baseline_score,
                final=final_quality.total_score,
                degradation=technical_baseline_score - final_quality.total_score,
            )
            # Mark as aborted and return technical answer
            state["enrichment_aborted"] = True
            state["abort_reason"] = f"Quality degraded from {technical_baseline_score:.1f} to {final_quality.total_score:.1f}"
            state["enriched_answer"] = state.get("answer", "")  # Use technical answer
            return "abort"
        
        # Check if passed
        if aethelgard_eval.get("passed"):
            state["enrichment_applied"] = True
            return "done"
        
        # Check retry count
        retry_count = state.get("polish_retry_count", 0)
        if retry_count >= 1:
            # Max retries, accept it (quality not degraded)
            logger.warning("graph.aethelgard.max_retries", score=aethelgard_eval.get("total_score"))
            state["enrichment_applied"] = True
            return "done"
        
        # Retry if we have feedback
        if aethelgard_eval.get("feedback"):
            return "repolish"
        
        state["enrichment_applied"] = True
        return "done"
    
    async def _repolish(self, state: GraphState) -> GraphState:
        """Repolish with feedback from Aethelgard evaluation."""
        aethelgard_eval = state.get("aethelgard_evaluation") or {}
        feedback = aethelgard_eval.get("feedback", [])
        retry_count = state.get("polish_retry_count", 0) + 1
        
        logger.info("graph.polish.retry", retry_count=retry_count, feedback_count=len(feedback))
        
        # For now, just increment retry and try again
        # In future, could pass feedback to enricher
        updated_state = {**state, "polish_retry_count": retry_count}
        return await self._apply_polish(updated_state)
    
    async def _enrich_narrative_legacy(self, state: GraphState) -> GraphState:
        """Legacy enrichment method (renamed from _enrich_narrative)."""
        return await self._enrich_narrative(state)
    
    # ========== Technical Compiler Methods ==========
    
    async def _compile_technical(self, state: GraphState) -> GraphState:
        """Compile technical answer into PSW-structured, learnable content."""
        if not self.technical_compiler:
            return state
        
        technical_answer = state.get("answer", "")
        citations = state.get("citations", [])
        
        logger.info("graph.compiler.start", answer_length=len(technical_answer))
        
        compiled = await self.technical_compiler.compile(
            technical_answer=technical_answer,
            citations=citations,
        )
        
        logger.info("graph.compiler.complete", compiled_length=len(compiled))
        
        return {**state, "compiled_answer": compiled, "compiler_retry_count": 0}
    
    async def _evaluate_compiler(self, state: GraphState) -> GraphState:
        """Evaluate compiled content quality (Quality Gate 2)."""
        if not self.compiler_evaluator:
            return state
        
        compiled = state.get("compiled_answer", "")
        technical_baseline = state.get("answer", "")
        
        logger.info("graph.compiler_eval.start")
        
        evaluation = self.compiler_evaluator.evaluate(
            compiled_content=compiled,
            technical_baseline=technical_baseline,
        )
        
        logger.info(
            "graph.compiler_eval.complete",
            passed=evaluation.passed,
            total_score=evaluation.total_score,
            tech_preservation=evaluation.technical_preservation,
        )
        
        return {**state, "compiler_evaluation": evaluation.to_dict()}
    
    def _compiler_decision(self, state: GraphState) -> str:
        """Decide whether to recompile or finish (Quality Gate 2)."""
        eval_data = state.get("compiler_evaluation", {})
        score = eval_data.get("total_score", 0)
        retry_count = state.get("compiler_retry_count", 0)
        
        if score >= self.settings.compiler_quality_threshold:
            logger.info("graph.compiler.passed", score=score)
            return "done"
        elif retry_count < 2:  # Max 2 recompile attempts
            logger.info("graph.compiler.retry", score=score, retry_count=retry_count)
            return "recompile"
        else:
            # Return best attempt after max retries
            logger.warning("graph.compiler.max_retries", score=score)
            return "done"
    
    async def _recompile(self, state: GraphState) -> GraphState:
        """Recompile with feedback from compiler evaluation."""
        if not self.technical_compiler:
            return state
        
        eval_data = state.get("compiler_evaluation", {})
        feedback = eval_data.get("feedback", [])
        retry_count = state.get("compiler_retry_count", 0) + 1
        previous_compilation = state.get("compiled_answer", "")
        
        logger.info("graph.compiler.recompile", retry_count=retry_count, feedback_count=len(feedback))
        
        # Recompile with feedback and previous attempt
        compiled = await self.technical_compiler.compile(
            technical_answer=state.get("answer", ""),
            citations=state.get("citations", []),
            feedback=feedback,
            previous_compilation=previous_compilation,
        )
        
        return {
            **state,
            "compiled_answer": compiled,
            "compiler_retry_count": retry_count,
        }
    
    # ========================================
    # AGENT 4: NARRATIVE ENRICHMENT
    # ========================================
    
    async def _agent_4_enrich(self, state: GraphState) -> GraphState:
        """
        Agent 4: Add engaging narrative enrichment to compiled content.
        
        This is the final polish that transforms technically accurate content
        into memorable learning experiences with real-world context.
        """
        if not self.narrative_enrichment_agent:
            logger.warning("agent_4.disabled")
            return state
        
        compiled_content = state.get("compiled_answer", "")
        question = state.get("question", "")
        
        if not compiled_content:
            logger.warning("agent_4.no_content")
            return state
        
        logger.info("agent_4.start", input_length=len(compiled_content))
        
        try:
            # Enrich the compiled content
            enriched_content = await self.narrative_enrichment_agent.enrich(
                compiled_content=compiled_content,
                question=question,
            )
            
            logger.info(
                "agent_4.success",
                input_length=len(compiled_content),
                output_length=len(enriched_content),
                enrichment_added=len(enriched_content) - len(compiled_content),
            )
            
            return {
                **state,
                "enriched_answer": enriched_content,
                "answer": enriched_content,  # Update final answer
            }
        
        except Exception as e:
            logger.error("agent_4.error", error=str(e), exc_info=True)
            # Return original compiled content if enrichment fails
            return {
                **state,
                "enriched_answer": compiled_content,
                "answer": compiled_content,
            }

