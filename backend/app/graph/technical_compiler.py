"""Technical Compiler Agent for PSW-structured content."""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

COMPILER_PROMPT = """You are a Technical Compiler for Aethelgard Academy. Your ONLY job is to restructure technical content while preserving EVERY SINGLE FACT, CITATION, and CODE BLOCK.

=== CRITICAL: CITATION PRESERVATION ===
YOU WILL BE PENALIZED IF YOU LOSE EVEN ONE CITATION.

Input citations: {citations}

RULE: Every [doc-X] and [web-X] from the technical answer MUST appear in your output.
- Attach citations to the SAME facts they were originally attached to
- If the technical answer has [doc-1], your output MUST have [doc-1]
- If the technical answer has [web-5], your output MUST have [web-5]
- NEVER remove, skip, or change citation IDs
- NEVER consolidate citations (keep them separate)

=== CRITICAL: CODE PRESERVATION ===
- Every ```python code block MUST be preserved EXACTLY as written
- Every technical term in backticks (`term`) MUST be preserved
- NEVER simplify or remove code examples

=== STRUCTURE: SUBTLE PSW (Problem-System-Win) ===

Your output MUST follow this EXACT structure:

**PART 1: PROBLEM FRAMING (2-3 paragraphs)**
Start naturally by framing the challenge or question. Use words like:
- "When working with..."
- "In real projects, developers face..."
- "Consider the challenge of..."
- "Why does [concept] matter?"

Include 1 "Consider..." prompt here.

**PART 2: CORE EXPLANATION (Main body, 4-6 paragraphs)**
Explain how it works technically. MUST include:
- ALL code blocks from technical answer (preserved exactly)
- ALL technical terms in backticks
- ALL citations attached to facts
- 2-3 "Consider..." prompts embedded naturally
- Production-ready examples (not toy code)

**PART 3: IMPACT & BENEFITS (1-2 paragraphs)**
Explain what this enables in practice. Highlight the "small fix, big clarity" moment.
- How does it improve workflows?
- What does it unlock?
- Connect to bigger picture

Include 1 "Consider..." prompt here.

**PART 4: REAL-WORLD EXAMPLES SECTION (REQUIRED)**
You MUST include this EXACT heading:

### Real-World Examples

Then provide 3 concrete examples:

**1. Production Scenario**
[Describe actual industry use case - 2-3 sentences]

**2. Common Development Workflow**
[Describe typical developer workflow - 2-3 sentences]

**3. Advanced Application**
[Describe advanced use with trade-offs - 2-3 sentences]

**PART 5: REFLECTION SECTION (REQUIRED)**
You MUST include this EXACT heading:

### Reflection

Then ask ONE focused question about the micro-fix that creates macro clarity:
"What small change in [concept] creates the biggest impact in [real application]?"

=== CHECKLIST BEFORE SUBMITTING ===
□ All citations from input appear in output
□ All code blocks preserved exactly
□ All technical terms in backticks preserved
□ 4-5 "Consider..." prompts throughout
□ "### Real-World Examples" section with 3 examples
□ "### Reflection" section with 1 question
□ PSW structure (problem → explanation → impact)
□ No fictional characters or creative storytelling
□ Professional, mentor-like tone

=== INPUT ===

Technical Answer:
{technical_answer}

Citations (CHECK EACH ONE):
{citations}

=== YOUR OUTPUT (MUST FOLLOW STRUCTURE ABOVE) ===
"""

RECOMPILE_PROMPT = """You are recompiling technical content based on quality feedback.

=== CRITICAL REMINDER ===
YOU FAILED TO MEET QUALITY STANDARDS. Fix the issues below while preserving EVERY citation and code block.

=== QUALITY FEEDBACK ===
{feedback}

=== ORIGINAL TECHNICAL ANSWER (YOUR SOURCE OF TRUTH) ===
{technical_answer}

=== CITATIONS (MUST ALL APPEAR IN OUTPUT) ===
{citations}

=== YOUR PREVIOUS ATTEMPT (FAILED) ===
{previous_compilation}

=== WHAT YOU MUST FIX ===
Address EVERY feedback point above. Common issues:
1. Missing citations → GO BACK and copy them from technical answer
2. Missing "### Real-World Examples" → ADD IT with 3 examples
3. Missing "### Reflection" → ADD IT with 1 question
4. Missing "Consider..." prompts → ADD 4-5 throughout
5. Missing code blocks → COPY them exactly from technical answer
6. No problem framing → START with "When working with..." or "Consider the challenge of..."
7. No impact section → END with "This enables..." or "This unlocks..."

=== REQUIRED STRUCTURE (COPY THIS) ===

[Problem framing paragraph - start with challenge/question]
Consider... [reflection prompt]

[Core explanation with ALL code blocks, ALL citations, ALL technical terms]
Consider... [reflection prompt]
Consider... [reflection prompt]

[Impact paragraph - "small fix, big clarity" moment]
Consider... [reflection prompt]

### Real-World Examples

**1. Production Scenario**
[2-3 sentences about actual industry use]

**2. Common Development Workflow**
[2-3 sentences about typical workflow]

**3. Advanced Application**
[2-3 sentences about advanced use with trade-offs]

### Reflection

[One focused question: "What small change in X creates the biggest impact in Y?"]

=== CHECKLIST (ALL MUST BE TRUE) ===
□ Every citation from technical answer is in my output
□ Every code block is preserved exactly
□ "### Real-World Examples" heading exists
□ 3 examples under Real-World Examples
□ "### Reflection" heading exists
□ 1 reflection question under Reflection
□ 4-5 "Consider..." prompts throughout
□ Problem → Explanation → Impact flow

=== YOUR RECOMPILED OUTPUT ===
"""


class TechnicalCompiler:
    """
    Compiles technical content into structured, learnable format.
    
    Uses subtle PSW (Problem-System-Win) framework without explicit labels.
    Focuses on "small fixes, big clarity" philosophy.
    """
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = ChatOpenAI(
            model="gpt-4o",
            api_key=self.settings.openai_api_key,
            temperature=self.settings.compiler_temperature,
        )
        self.logger = get_logger(__name__)
    
    async def compile(
        self,
        technical_answer: str,
        citations: list[dict[str, Any]],
        feedback: list[str] | None = None,
        previous_compilation: str | None = None,
    ) -> str:
        """
        Compile technical answer into structured, learnable content.
        
        Args:
            technical_answer: The technically accurate answer
            citations: List of citations to preserve
            feedback: Optional feedback from previous compilation attempt
            previous_compilation: Optional previous compilation that failed
            
        Returns:
            Compiled content with PSW structure
        """
        try:
            # Format citations for prompt
            citations_str = "\n".join(
                [f"[{c.get('id', '')}] {c.get('source', 'N/A')}" for c in citations]
            )
            
            if feedback and previous_compilation:
                # Recompile with feedback
                prompt = RECOMPILE_PROMPT.format(
                    technical_answer=technical_answer,
                    citations=citations_str,
                    previous_compilation=previous_compilation,
                    feedback="\n".join(feedback),
                )
            else:
                # Initial compilation
                prompt = COMPILER_PROMPT.format(
                    technical_answer=technical_answer,
                    citations=citations_str,
                )
            
            response = await self.model.ainvoke(prompt)
            compiled = response.content.strip()
            
            # Verify citations were preserved
            citation_ids = [c.get("id", "") for c in citations]
            missing_citations = [
                cid for cid in citation_ids if cid and f"[{cid}]" not in compiled
            ]
            
            if missing_citations:
                self.logger.warning(
                    "compiler.missing_citations",
                    missing=missing_citations,
                )
            
            self.logger.info(
                "compiler.complete",
                compiled_length=len(compiled),
                citations_preserved=len(citation_ids) - len(missing_citations),
            )
            
            return compiled
            
        except Exception as e:
            self.logger.error(
                "compiler.error",
                error=str(e),
                exc_info=True,
            )
            # Return original technical answer on error
            return technical_answer

