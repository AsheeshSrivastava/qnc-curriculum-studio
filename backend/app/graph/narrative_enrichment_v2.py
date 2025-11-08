"""Agent 4: Narrative Enrichment - Add engaging real-world context."""

from __future__ import annotations

from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.core.logging import get_logger
from app.providers.factory import get_chat_model
from app.security.secret_store import SecretStore

logger = get_logger(__name__)


class NarrativeEnrichmentAgent:
    """
    Agent 4: Narrative Enrichment
    
    Adds engaging real-world context inspired by Python Fundamentals approach.
    
    Strategy:
    - Add contextual boxes (TIP, WARNING, EXAMPLE)
    - Use progressive disclosure language
    - Anchor concepts to real-world use cases
    - Add interactive prompts
    - Preserve ALL technical accuracy and structure
    """

    def __init__(
        self,
        secret_store: SecretStore,
        provider: str = "openai",
        secret_token: str | None = None,
    ):
        """Initialize narrative enrichment agent."""
        self.settings = get_settings()
        self.secret_store = secret_store
        self.provider = provider
        self.secret_token = secret_token

    async def enrich(
        self,
        compiled_content: str,
        question: str,
    ) -> str:
        """
        Add narrative enrichment to compiled technical content.

        Args:
            compiled_content: Output from Technical Compiler (Agent 3)
            question: Original user question for context

        Returns:
            Enriched content with engaging narrative elements
        """
        try:
            logger.info("narrative_enrichment.start")

            # Build prompt
            prompt = self._build_prompt(compiled_content, question)

            # Get LLM
            llm = await get_chat_model(
                provider=self.provider,
                model=self.settings.openai_chat_model,
                temperature=self.settings.narrative_temperature,
                secret_store=self.secret_store,
                secret_token=self.secret_token,
            )

            # Generate enriched content
            messages = [
                SystemMessage(content=prompt["system"]),
                HumanMessage(content=prompt["user"]),
            ]

            response = await llm.ainvoke(messages)
            enriched_content = response.content

            logger.info(
                "narrative_enrichment.success",
                input_length=len(compiled_content),
                output_length=len(enriched_content),
            )

            return enriched_content

        except Exception as e:
            logger.error("narrative_enrichment.error", error=str(e), exc_info=True)
            # Return original content if enrichment fails
            return compiled_content

    def _build_prompt(self, compiled_content: str, question: str) -> dict[str, str]:
        """Build the narrative enrichment prompt."""
        system_prompt = """You are a narrative enrichment specialist for educational content.

Your role is to add engaging, real-world context to technical content WITHOUT changing its structure or accuracy.

NARRATIVE STYLE (inspired by Python Fundamentals):

1. **Contextual Boxes** (use markdown blockquotes):
   > 💡 **TIP**: [helpful insight that makes learning easier]
   > ⚠️ **WARNING**: [common mistake to avoid]
   > 🔍 **REAL-WORLD EXAMPLE**: [actual industry use case]

2. **Progressive Disclosure Language**:
   - Start sections: "Let's explore how...", "Consider what happens when..."
   - Middle sections: "Notice how...", "This is where..."
   - End sections: "In practice, you'll find...", "This approach enables..."

3. **Real-World Anchoring**:
   - Connect abstract concepts to concrete use cases
   - Reference actual industry practices
   - Show production-level examples
   - Mention popular libraries/frameworks that use the concept

4. **Interactive Prompts** (rhetorical questions):
   - "What if you needed to...?"
   - "How would you handle...?"
   - "Consider the scenario where..."

CRITICAL PRESERVATION RULES:

✅ PRESERVE (DO NOT CHANGE):
- ALL technical accuracy
- ALL code examples (keep exactly as-is)
- ALL structure (headers, sections, order)
- ALL citations and references
- The PSW framework structure
- Any existing markdown formatting

❌ DO NOT ADD:
- Fictional characters or stories
- Unnecessary complexity
- Marketing language
- Unrelated tangents

YOUR TASK:
1. Read the compiled content carefully
2. Identify 3-5 strategic places to add narrative elements
3. Add contextual boxes, progressive language, and real-world anchors
4. Ensure the content flows naturally
5. Return the enriched content with ALL original structure intact

Remember: You're enhancing, not rewriting. The technical content is already excellent."""

        user_prompt = f"""Original Question: {question}

Compiled Technical Content:
{compiled_content}

Please enrich this content with engaging narrative elements while preserving ALL technical accuracy and structure.

Focus on:
1. Adding 3-5 contextual boxes (TIP, WARNING, REAL-WORLD EXAMPLE)
2. Using progressive disclosure language in section transitions
3. Anchoring concepts to real-world use cases
4. Adding 2-3 interactive prompts

Return the enriched content in markdown format."""

        return {
            "system": system_prompt,
            "user": user_prompt,
        }

