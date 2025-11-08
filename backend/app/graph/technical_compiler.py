"""Technical Compiler Agent for PSW-structured content."""

from __future__ import annotations

import re
from typing import Any

from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _extract_citation_ids(text: str) -> set[str]:
    """Extract all citation IDs from text (e.g., [doc-1], [web-5])."""
    return set(re.findall(r'\[(doc|web)-\d+\]', text))


def _strip_citation_tags(text: str) -> str:
    """
    Remove all citation tags ([doc-X], [web-X]) from text.
    
    Citations are returned separately in the citations array,
    so they should NOT appear in the final answer text.
    
    Args:
        text: Text with citation tags
        
    Returns:
        Text with citation tags removed
    """
    # Remove all [doc-X] and [web-X] tags
    cleaned = re.sub(r'\s*\[(doc|web)-\d+\]\s*', ' ', text)
    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Clean up space before punctuation
    cleaned = re.sub(r'\s+([.,!?;:])', r'\1', cleaned)
    return cleaned.strip()

COMPILER_PROMPT = """# ROLE & CONTEXT
You are an Expert Technical Content Compiler for Educational Content.

Your PRIMARY OBJECTIVE: Transform technical content into learner-friendly, structured format while maintaining 100% factual accuracy.

**CRITICAL**: Do NOT include citation tags like [doc-1] or [web-5] in your output. Citations are handled separately by the system.

# STRUCTURE REQUIREMENTS

Your output MUST follow this EXACT structure:

## PART 1: PROBLEM FRAMING (2-3 paragraphs)
Start by framing the challenge or question naturally:
- "When working with..."
- "In real projects, developers face..."
- "Consider the challenge of..."
- "Why does [concept] matter?"

Include 1 "Consider..." reflection prompt here.

## PART 2: CORE EXPLANATION (Main body, 4-6 paragraphs)
Explain how it works technically. MUST include:
- ALL code blocks from source material (preserved exactly)
- ALL technical terms in backticks
- 2-3 "Consider..." reflection prompts embedded naturally
- Production-ready examples (not toy code)
- Progressive complexity (simple → advanced)

## PART 3: IMPACT & BENEFITS (1-2 paragraphs)
Explain what this enables in practice:
- How does it improve workflows?
- What does it unlock?
- Connect to bigger picture
- Highlight the "small fix, big clarity" moment

Include 1 "Consider..." prompt here.

## PART 4: REAL-WORLD EXAMPLES (REQUIRED)
You MUST include this EXACT heading:

### Real-World Examples

Then provide 3 concrete examples:

**1. Production Scenario**
[Describe actual industry use case - 2-3 sentences]

**2. Common Development Workflow**
[Describe typical developer workflow - 2-3 sentences]

**3. Advanced Application**
[Describe advanced use with trade-offs - 2-3 sentences]

## PART 5: REFLECTION (REQUIRED)
You MUST include this EXACT heading:

### Reflection

Then ask ONE focused question about the micro-fix that creates macro clarity:
"What small change in [concept] creates the biggest impact in [real application]?"

# TECHNICAL PRESERVATION

FROM THE TECHNICAL ANSWER BELOW:
- Preserve EVERY code block exactly as written
- Preserve EVERY technical term (use backticks)
- Do NOT change technical facts or accuracy
- Do NOT simplify code examples

# CHECKLIST BEFORE SUBMITTING

□ Problem framing paragraph (starts with challenge/question)
□ Core explanation with ALL code blocks
□ ALL technical terms in backticks
□ 4-5 "Consider..." prompts throughout
□ Impact paragraph ("small fix, big clarity")
□ "### Real-World Examples" section with 3 examples
□ "### Reflection" section with 1 question
□ PSW flow (problem → explanation → impact)
□ Professional, mentor-like tone
□ NO citation tags ([doc-X], [web-X]) in output

# INPUT

Technical Answer:
{technical_answer}

# YOUR OUTPUT

"""

RECOMPILE_PROMPT = """# RECOMPILATION TASK

## Context
You are recompiling technical content that FAILED quality evaluation. This is your second chance.

## Why You Failed
{feedback}

## Critical Requirements
1. **NO Citation Tags**: Do NOT include [doc-X] or [web-X] in output
2. **Code Preservation**: ALL code blocks MUST be preserved exactly
3. **Technical Accuracy**: NO facts can be changed or removed
4. **Required Structure**: MUST include all sections (Problem Framing, Real-World Examples, Reflection)

## Your Source Materials

### Original Technical Answer (YOUR SOURCE OF TRUTH):
{technical_answer}

### Your Previous Attempt (FAILED):
{previous_compilation}

## What You MUST Fix

Address EVERY feedback point above. Common issues:
1. **Missing Problem Framing** → START with "When working with..." or "Consider the challenge of..."
2. **Missing "### Real-World Examples"** → ADD IT with 3 examples
3. **Missing "### Reflection"** → ADD IT with 1 question
4. **Missing "Consider..." prompts** → ADD 4-5 throughout
5. **Missing code blocks** → COPY them exactly from technical answer
6. **Missing Impact section** → END with "This enables..." or "This unlocks..."
7. **Citation tags in output** → REMOVE ALL [doc-X] and [web-X] tags

## Required Structure (COPY THIS)

[Problem framing paragraph - start with challenge/question]
Consider... [reflection prompt]

[Core explanation with ALL code blocks, ALL technical terms]
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

## Checklist (ALL MUST BE TRUE)

□ Every code block is preserved exactly
□ "### Real-World Examples" heading exists
□ 3 examples under Real-World Examples
□ "### Reflection" heading exists
□ 1 reflection question under Reflection
□ 4-5 "Consider..." prompts throughout
□ Problem → Explanation → Impact flow
□ NO citation tags ([doc-X], [web-X]) in output

## YOUR RECOMPILED OUTPUT

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
            if feedback and previous_compilation:
                # Recompile with feedback
                prompt = RECOMPILE_PROMPT.format(
                    technical_answer=technical_answer,
                    previous_compilation=previous_compilation,
                    feedback="\n".join(feedback),
                )
            else:
                # Initial compilation
                prompt = COMPILER_PROMPT.format(
                    technical_answer=technical_answer,
                )
            
            response = await self.model.ainvoke(prompt)
            compiled = response.content.strip()
            
            # IMPORTANT: Strip all citation tags from final output
            # Citations are returned separately in the citations array
            compiled_clean = _strip_citation_tags(compiled)
            
            self.logger.info(
                "compiler.complete",
                compiled_length=len(compiled_clean),
                had_citation_tags=('[doc-' in compiled or '[web-' in compiled),
            )
            
            return compiled_clean
            
        except Exception as e:
            self.logger.error(
                "compiler.error",
                error=str(e),
                exc_info=True,
            )
            # Return original technical answer on error (with citations stripped)
            return _strip_citation_tags(technical_answer)

