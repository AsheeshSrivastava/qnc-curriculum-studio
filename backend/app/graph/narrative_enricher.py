"""Aethelgard Polish agent - Final brand voice and RAG optimization."""

from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

AETHELGARD_POLISH_PROMPT = """You are the final editor for Aethelgard Academy content.

BRAND VOICE:
- Honest: Tell the truth, even if it's "this is confusing at first"
- Reflective: Encourage thinking, not just doing
- Clear: Micro fixes that create macro clarity

YOUR TASKS:
1. Ensure "micro fix, macro impact" moments are clear and memorable
2. Add ONE reflection question that connects to learner's experience
3. Inject keywords naturally for semantic search (don't force)
4. Structure for RAG retrieval (clear sections, scannable)
5. Maintain conversational but professional tone
6. Add metadata section with keywords and quick answer

KEYWORD INTEGRATION (for chatbot RAG):
Weave in naturally:
- Technical terms from the answer
- Common beginner questions/problems
- Related concepts
- Problem symptoms (what learners search for)

Example:
Instead of: "This solves the problem"
Write: "This solves the 'ModuleNotFoundError' that beginners often hit"

OUTPUT STRUCTURE:
```
# [Topic Title]

**Keywords:** [comma-separated keywords for semantic search]

**Quick Answer (for chatbot):** [1-2 sentence direct answer]

---

[Main narrative content with preserved citations]

**The Micro Fix:**
[Highlight the key insight - small change, big impact]

**Reflection:**
[ONE thought-provoking question tied to learner's experience]

---

**Related Concepts:** [comma-separated related topics]
```

Story Content to Polish:
{story_content}

Citations (preserve ALL):
{citations}

Apply Aethelgard polish with brand voice, keywords, and RAG structure.
"""


class NarrativeEnricher:
    """
    Final polish agent for Aethelgard Academy brand voice and RAG optimization.
    
    This is Agent 3 in the pipeline:
    - Agent 1: Scenario Architect (creates micro-scenario)
    - Agent 2: CoT Storyteller (narrative with reasoning)
    - Agent 3: Aethelgard Polish (brand voice + keywords + RAG structure)
    """
    
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        
        if not settings.google_api_key:
            logger.warning("narrative_enricher.init.no_key", msg="GOOGLE_API_KEY not configured")
            self.model = None
            return
        
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=settings.google_api_key,
            temperature=settings.narrative_temperature,  # Use configured temperature (0.7)
            max_output_tokens=2048,
        )
        
        logger.info("narrative_enricher.init.success", model="gemini-1.5-pro")
    
    async def enrich(
        self,
        story_content: str,
        citations: list[dict],
    ) -> str:
        """
        Apply Aethelgard brand polish and RAG optimization.
        
        Args:
            story_content: Narrative from CoT Storyteller
            citations: Citation list to preserve
            
        Returns:
            Final polished content with brand voice and RAG structure
        """
        if not self.model:
            logger.warning("narrative_enricher.enrich.no_model")
            return story_content  # Return unpolished if no model
        
        try:
            # Format citations
            citations_str = "\n".join(
                [f"[{c.get('id', '')}] {c.get('source', 'N/A')}" for c in citations]
            )
            
            prompt = ChatPromptTemplate.from_template(AETHELGARD_POLISH_PROMPT)
            messages = prompt.format_messages(
                story_content=story_content,
                citations=citations_str,
            )
            
            response = await self.model.ainvoke(messages)
            polished = response.content.strip()
            
            logger.info(
                "narrative_enricher.enrich.complete",
                original_length=len(story_content),
                polished_length=len(polished),
            )
            
            return polished
            
        except Exception as e:
            logger.error(
                "narrative_enricher.enrich.error",
                error=str(e),
                exc_info=True,
            )
            # Return original story on error
            return story_content
