"""Chain-of-Thought storyteller for narrative transformation."""

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

COT_PROMPT_SIMPLE = """You are rewriting technical content as a clear, concise explanation.

COMPLEXITY: SIMPLE
Keep it direct and straightforward. No elaborate story needed.

AETHELGARD PRINCIPLES:
- Honest, reflective, clear
- One concrete example
- Preserve ALL citations [doc-X], [web-X]

Technical Answer:
{technical_answer}

Citations:
{citations}

Scenario (if any):
{scenario}

Rewrite as a clear, concise explanation. Preserve ALL citations. Include ONE concrete example.
"""

COT_PROMPT_STANDARD = """You are rewriting technical content as an engaging learning narrative.

COMPLEXITY: STANDARD
Use the scenario to show before/after. Include ONE "aha moment" (the micro fix that unlocks clarity).

AETHELGARD PRINCIPLES:
- Micro fixes, macro impact
- Honest, reflective, clear
- Show character's realization
- Preserve ALL citations [doc-X], [web-X]

CRITICAL REQUIREMENT - CITATION PRESERVATION:
You MUST preserve EVERY SINGLE citation from the technical answer.
- If technical answer has [doc-1], your narrative MUST have [doc-1]
- If technical answer has [web-3], your narrative MUST have [web-3]
- Attach citations to the SAME facts they were attached to originally
- NEVER remove or skip citations
- NEVER change citation IDs

CRITICAL REQUIREMENT - TECHNICAL TERMS:
You MUST preserve ALL technical terms in backticks from the technical answer.
- If technical answer has `conda`, your narrative MUST have `conda`
- If technical answer has `pip install`, your narrative MUST have `pip install`
- Keep code examples EXACTLY as they appear

Scenario:
{scenario}

Technical Answer:
{technical_answer}

Citations (YOU MUST USE ALL OF THESE):
{citations}

STRUCTURE:
1. Start with the scenario problem
2. Show the character's struggle or confusion
3. Introduce the micro-fix (the key insight) WITH CITATIONS
4. Explain how it works WITH ALL TECHNICAL TERMS and CITATIONS
5. Highlight the "aha moment" - why this small fix creates big clarity
6. End with practical application

Rewrite as narrative. CHECK: Did you include EVERY citation? Did you preserve ALL technical terms?
"""

COT_PROMPT_CRITICAL = """You are rewriting technical content as a deep learning narrative with Chain-of-Thought reasoning.

COMPLEXITY: CRITICAL
Show step-by-step thinking. Multiple progressive insights. Character discovers sub-concepts naturally.

AETHELGARD PRINCIPLES:
- Micro fixes, macro impact
- Honest, reflective, clear
- Show reasoning, not just results
- Preserve ALL citations [doc-X], [web-X]

CRITICAL REQUIREMENT - CITATION PRESERVATION:
You MUST preserve EVERY SINGLE citation from the technical answer.
- If technical answer has [doc-1], your narrative MUST have [doc-1]
- If technical answer has [web-3], your narrative MUST have [web-3]
- Attach citations to the SAME facts they were attached to originally
- NEVER remove or skip citations
- NEVER change citation IDs

CRITICAL REQUIREMENT - TECHNICAL TERMS:
You MUST preserve ALL technical terms in backticks from the technical answer.
- If technical answer has `conda`, your narrative MUST have `conda`
- If technical answer has `pip install`, your narrative MUST have `pip install`
- Keep code examples EXACTLY as they appear

CHAIN-OF-THOUGHT REQUIREMENTS:
- Show character's thought process step-by-step
- Use reasoning indicators: "first", "then", "realized", "because", "therefore"
- Build understanding progressively (simple → intermediate → advanced)
- Multiple "aha moments" (each builds on the last)
- Connect to bigger picture at the end

Scenario:
{scenario}

Technical Answer:
{technical_answer}

Citations (YOU MUST USE ALL OF THESE):
{citations}

STRUCTURE:
1. Start with the layered problem from scenario
2. Show character's initial attempt and confusion
3. FIRST INSIGHT: Character discovers first piece WITH CITATIONS and TECHNICAL TERMS
4. SECOND INSIGHT: This leads to deeper understanding WITH CITATIONS
5. FINAL INSIGHT: Everything clicks - the micro-fix that unlocks macro clarity WITH CITATIONS
6. Reflection on the bigger picture
7. Practical implications

Use Chain-of-Thought reasoning. CHECK: Did you include EVERY citation? Did you preserve ALL technical terms and code?
"""


class CoTStoryteller:
    """
    Transforms technical content into narrative using Chain-of-Thought reasoning.
    
    Adapts storytelling approach based on complexity:
    - Simple: Direct explanation with example
    - Standard: Before/after narrative with one aha moment
    - Critical: Progressive discovery with multiple insights (CoT)
    """
    
    def __init__(self) -> None:
        settings = get_settings()
        self.model = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.openai_api_key,
            temperature=0.5,  # Balanced creativity and consistency
        )
        self.logger = get_logger(__name__)
    
    async def create_story(
        self,
        technical_answer: str,
        scenario: str,
        citations: list[dict],
        complexity: str,
    ) -> str:
        """
        Transform technical content into narrative.
        
        Args:
            technical_answer: The technical content
            scenario: The micro-scenario (or "SKIP")
            citations: List of citations to preserve
            complexity: simple | standard | critical
            
        Returns:
            Story-driven narrative with preserved citations
        """
        try:
            # Format citations for prompt
            citations_str = "\n".join(
                [f"[{c.get('id', '')}] {c.get('source', 'N/A')}" for c in citations]
            )
            
            # Select prompt based on complexity
            if complexity == "simple":
                prompt_template = COT_PROMPT_SIMPLE
            elif complexity == "standard":
                prompt_template = COT_PROMPT_STANDARD
            else:  # critical
                prompt_template = COT_PROMPT_CRITICAL
            
            prompt = ChatPromptTemplate.from_template(prompt_template)
            messages = prompt.format_messages(
                technical_answer=technical_answer,
                scenario=scenario if scenario != "SKIP" else "No specific scenario",
                citations=citations_str,
            )
            
            response = await self.model.ainvoke(messages)
            story = response.content.strip()
            
            # Verify citations were preserved
            citation_ids = [c.get("id", "") for c in citations]
            missing_citations = [
                cid for cid in citation_ids if cid and f"[{cid}]" not in story
            ]
            
            if missing_citations:
                self.logger.warning(
                    "cot.storyteller.missing_citations",
                    complexity=complexity,
                    missing=missing_citations,
                )
            
            self.logger.info(
                "cot.storyteller.complete",
                complexity=complexity,
                story_length=len(story),
                citations_preserved=len(citation_ids) - len(missing_citations),
            )
            
            return story
            
        except Exception as e:
            self.logger.error(
                "cot.storyteller.error",
                complexity=complexity,
                error=str(e),
                exc_info=True,
            )
            # Return technical answer on error to maintain quality
            return technical_answer

