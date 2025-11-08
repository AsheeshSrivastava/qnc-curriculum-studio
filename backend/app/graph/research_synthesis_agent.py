"""Agent 1: Research & Synthesis - Technical content generation."""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SYNTHESIS_PROMPT = """You are Agent 1: Research & Synthesis Specialist.

Your SOLE job: Synthesize provided sources into technically accurate Python content.

=== YOUR FOCUS ===

1. **TECHNICAL ACCURACY**: Every fact must be correct
2. **CODE EXAMPLES**: Include 3-5 runnable Python examples
3. **CITATIONS**: Cite every fact with [doc-X] or [web-X]
4. **COMPLETENESS**: Cover basics, mechanics, and advanced usage

=== WHAT YOU DO NOT DO ===

- NO formatting (Agent 2 handles this)
- NO markdown headers (Agent 2 handles this)
- NO narrative or storytelling (Agent 4 handles this)
- NO real-world examples yet (Agent 4 handles this)

=== OUTPUT FORMAT ===

Plain text paragraphs with:
- Code blocks (```python)
- Inline citations [doc-X] [web-X]
- Technical terms in backticks
- Clear explanations

Write as if explaining to a colleague. Focus on WHAT it is and HOW it works.

=== CONTENT STRUCTURE ===

**Section 1: Definition & Purpose**
Define the concept clearly. Explain what it is and why it exists. Cite official documentation.

**Section 2: Basic Syntax**
Show the simplest possible example with code. Explain each part. Cite syntax references.

```python
# Basic example
[code here]
```

Explain how this code works line by line. Cite sources.

**Section 3: How It Works**
Explain the internal mechanics. How does Python process this? What happens under the hood? Cite technical sources.

**Section 4: Syntax Variations**
Show 2-3 different ways to use this feature. Include code examples. Cite documentation.

```python
# Variation 1
[code here]
```

```python
# Variation 2
[code here]
```

Explain when to use each variation. Cite best practices.

**Section 5: Advanced Usage**
Show complex real-world patterns. Include edge cases. Cite community sources and discussions.

```python
# Advanced example
[code here]
```

Explain advanced concepts and gotchas. Cite technical discussions.

**Section 6: Comparisons**
Compare to alternative approaches. Discuss performance implications. Cite benchmarks and style guides.

=== QUALITY REQUIREMENTS ===

Before submitting, verify:
- [ ] 3-5 code blocks with ```python
- [ ] 15-25 citations [doc-X] [web-X]
- [ ] Technical terms in `backticks`
- [ ] All facts are accurate
- [ ] Covers simple → intermediate → advanced

=== SOURCES PROVIDED ===

{sources_context}

=== QUESTION ===

{question}

=== YOUR TECHNICAL SYNTHESIS ===

Write plain text with code blocks and citations. Focus on accuracy and completeness.
"""


class ResearchSynthesisAgent:
    """
    Agent 1: Synthesize RAG + Tavily sources into technical content.
    
    Focus: Accuracy, code examples, citations
    Output: Plain text technical draft (no formatting)
    """
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = ChatOpenAI(
            model="gpt-4o",
            api_key=self.settings.openai_api_key,
            temperature=self.settings.synthesis_temperature,
        )
        self.logger = get_logger(__name__)
    
    async def synthesize(
        self,
        question: str,
        sources_context: str,
    ) -> str:
        """
        Synthesize sources into technical content.
        
        Args:
            question: User's question
            sources_context: Formatted RAG + Tavily sources
            
        Returns:
            Technical draft with code and citations
        """
        try:
            prompt = SYNTHESIS_PROMPT.format(
                question=question,
                sources_context=sources_context,
            )
            
            self.logger.info(
                "agent_1.synthesis.start",
                question=question[:100],
            )
            
            response = await self.model.ainvoke(prompt)
            synthesis = response.content.strip()
            
            # Quick validation
            code_blocks = synthesis.count("```python")
            citations = len([c for c in synthesis.split() if c.startswith("[doc-") or c.startswith("[web-")])
            
            self.logger.info(
                "agent_1.synthesis.complete",
                length=len(synthesis),
                code_blocks=code_blocks,
                citations=citations,
            )
            
            return synthesis
            
        except Exception as e:
            self.logger.error(
                "agent_1.synthesis.error",
                error=str(e),
                exc_info=True,
            )
            raise

