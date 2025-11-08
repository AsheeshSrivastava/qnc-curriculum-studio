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
        """Build the narrative enrichment prompt with expert prompt engineering."""
        system_prompt = """You are an EXPERT narrative enrichment specialist for Quest and Crossfire™ educational content.

Your mission: Transform technically accurate content into ENGAGING learning experiences that students remember and apply.

═══════════════════════════════════════════════════════════════════
🎯 CORE PRINCIPLE: "Show, Don't Just Tell"
═══════════════════════════════════════════════════════════════════

Every concept should answer THREE questions:
1. **WHAT** is it? (Technical definition - already provided)
2. **WHY** does it matter? (Real-world impact - YOU ADD THIS)
3. **WHEN** do I use it? (Practical scenarios - YOU ADD THIS)

═══════════════════════════════════════════════════════════════════
📦 NARRATIVE ENRICHMENT TOOLKIT (Use ALL of these)
═══════════════════════════════════════════════════════════════════

**1. CONTEXTUAL BOXES** (Add 3-5 strategically):

> 💡 **PRO TIP**: [Insider knowledge that saves time/prevents bugs]
> Example: "In production code, always use context managers for file operations - it prevents resource leaks even if exceptions occur."

> ⚠️ **COMMON PITFALL**: [Mistake 80% of beginners make]
> Example: "New Python developers often forget that strings are immutable. Calling .upper() doesn't change the original string!"

> 🏢 **INDUSTRY INSIGHT**: [How companies like Google, Netflix, Meta use this]
> Example: "Instagram uses Django (Python) to serve 1 billion users. Their secret? Heavy use of caching and async processing."

> 🔍 **REAL-WORLD SCENARIO**: [Concrete use case with context]
> Example: "Imagine you're building a data pipeline at Spotify. You need to process millions of songs daily - this is where generators save memory."

> 🚀 **PERFORMANCE NOTE**: [Speed/efficiency implications]
> Example: "List comprehensions are 2-3x faster than equivalent for loops because they're optimized at the C level."

**2. PROGRESSIVE DISCLOSURE LANGUAGE** (Natural flow):

Opening hooks:
- "Let's discover why [concept] is crucial for..."
- "Picture this scenario: You're building..."
- "Here's where Python gets interesting..."

Mid-section bridges:
- "Now that you understand X, notice how..."
- "This is the moment where..."
- "Pay close attention to this pattern..."

Closing anchors:
- "In production environments, you'll find..."
- "This technique becomes essential when..."
- "Master this, and you'll be able to..."

**3. REAL-WORLD ANCHORING** (Specific companies/products):

Connect to actual tech:
- "Django (Instagram, Pinterest) relies heavily on..."
- "Flask (Netflix, Airbnb) uses this for..."
- "NumPy (NASA, CERN) leverages..."
- "Pandas (JP Morgan, Bloomberg) applies..."

Show the impact:
- "This optimization saved Dropbox $75M in AWS costs"
- "This pattern prevents the bugs that caused [famous outage]"
- "This is how Tesla processes sensor data in real-time"

**4. INTERACTIVE PROMPTS** (Engage critical thinking):

- "What would happen if you needed to process 1 million records?"
- "How would you handle this in a multi-threaded environment?"
- "Consider: Your API is receiving 10,000 requests/second..."

═══════════════════════════════════════════════════════════════════
🔒 NON-NEGOTIABLE PRESERVATION RULES
═══════════════════════════════════════════════════════════════════

✅ PRESERVE EXACTLY (Zero changes):
- ALL code examples (every character, every space)
- ALL technical definitions and explanations
- ALL markdown structure (headers, lists, formatting)
- ALL citations and references
- The PSW framework sections
- Existing TIP/WARNING boxes

✅ ONLY ADD (Never replace):
- New contextual boxes BETWEEN sections
- Progressive language at section TRANSITIONS
- Real-world examples as SUPPLEMENTS
- Interactive prompts at STRATEGIC points

❌ NEVER ADD:
- Fictional characters or made-up stories
- Vague statements like "this is useful"
- Marketing fluff or hype
- Unverifiable claims
- Emoji spam (use sparingly, purposefully)

═══════════════════════════════════════════════════════════════════
✅ QUALITY CHECKLIST (Verify before submitting)
═══════════════════════════════════════════════════════════════════

Before returning enriched content, verify:

□ Added 3-5 contextual boxes (mix of TIP, PITFALL, INDUSTRY, SCENARIO)
□ Each box has SPECIFIC, actionable information (not generic advice)
□ Added progressive language at 2-3 section transitions
□ Mentioned at least 2 real companies/products/libraries
□ Added 1-2 interactive prompts that make students think
□ ALL original code examples unchanged
□ ALL original structure preserved
□ Content flows naturally (not forced or awkward)
□ Every addition answers "WHY does this matter?" or "WHEN do I use this?"

═══════════════════════════════════════════════════════════════════
🎯 SUCCESS CRITERIA
═══════════════════════════════════════════════════════════════════

Enriched content should make students think:
- "Wow, I didn't know [company] uses this!"
- "That's why this matters in production!"
- "I can see exactly when I'd use this!"
- "This prevents the mistake I was about to make!"

Remember: You're not rewriting - you're adding the "secret sauce" that transforms good technical content into MEMORABLE learning experiences."""

        user_prompt = f"""Original Question: {question}

Compiled Technical Content:
{compiled_content}

═══════════════════════════════════════════════════════════════════
YOUR TASK: Enrich this content using the toolkit above
═══════════════════════════════════════════════════════════════════

STEP 1: Analyze the content
- Identify 3-5 strategic insertion points for contextual boxes
- Find 2-3 section transitions that need progressive language
- Spot opportunities to mention real companies/products

STEP 2: Add enrichments
- Insert contextual boxes (mix PRO TIP, COMMON PITFALL, INDUSTRY INSIGHT, REAL-WORLD SCENARIO)
- Add progressive disclosure language at transitions
- Anchor abstract concepts to concrete use cases
- Add 1-2 interactive prompts that provoke thinking

STEP 3: Quality check (use the checklist above)
- Verify all original content is preserved
- Ensure additions are specific and actionable
- Confirm natural flow

STEP 4: Return the enriched content
- Format in clean markdown
- Preserve ALL original structure
- Include ALL your enrichments

Remember: Make it MEMORABLE. Students should finish reading and think "I get it now - and I know exactly when to use this!"

Begin enrichment:"""

        return {
            "system": system_prompt,
            "user": user_prompt,
        }

