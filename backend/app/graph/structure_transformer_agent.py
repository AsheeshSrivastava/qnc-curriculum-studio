"""Agent 2: Structure Transformer - Markdown formatting and organization."""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

STRUCTURE_PROMPT = """You are Agent 2: Structure Transformer.

Your SOLE job: Transform plain text into well-structured markdown.

=== INPUT ===

Plain text technical content with code blocks and citations.

=== YOUR JOB ===

Add markdown structure WITHOUT changing any content.

=== TRANSFORMATION RULES ===

1. **Add Markdown Headers**:
   - Use ## for main sections
   - Use ### for subsections
   - Create clear hierarchy

2. **Add Paragraph Breaks**:
   - Add blank lines between paragraphs
   - NO walls of text
   - Each paragraph = 3-5 sentences max

3. **Preserve Everything**:
   - Keep ALL code blocks exactly as-is
   - Keep ALL citations exactly as-is
   - Keep ALL technical terms exactly as-is
   - Keep ALL explanations exactly as-is
   - ONLY add formatting, NEVER change content

=== OUTPUT STRUCTURE ===

## Understanding [Topic Name]

[Opening paragraph: What is it?]

[Second paragraph: Why does it matter?]

### Basic Syntax

```python
# Code block (preserved exactly)
```

[Explanation paragraph]

## How It Works

[Paragraph: Internal mechanics]

[Paragraph: Processing details]

### Syntax Variations

```python
# Variation 1 (preserved exactly)
```

[Explanation]

```python
# Variation 2 (preserved exactly)
```

[Explanation]

## Advanced Usage

[Paragraph: Complex patterns]

### Advanced Example

```python
# Advanced code (preserved exactly)
```

[Explanation with edge cases]

## Comparisons & Best Practices

[Paragraph: vs alternatives]

[Paragraph: When to use]

=== CRITICAL RULES ===

- **PRESERVE ALL CONTENT**: Do not change, remove, or add any facts
- **PRESERVE ALL CODE**: Copy code blocks exactly, including comments
- **PRESERVE ALL CITATIONS**: Keep [doc-X] and [web-X] in same locations
- **ONLY ADD**: Markdown headers (##, ###) and blank lines
- **NO CONTENT CHANGES**: Your job is formatting ONLY

=== INPUT CONTENT ===

{technical_content}

=== YOUR STRUCTURED OUTPUT ===

Transform the above into well-structured markdown. Preserve everything, add only formatting.
"""


class StructureTransformerAgent:
    """
    Agent 2: Transform plain text into structured markdown.
    
    Input: Technical draft from Agent 1
    Output: Markdown with headers, sections, paragraphs
    """
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = ChatOpenAI(
            model="gpt-4o",
            api_key=self.settings.openai_api_key,
            temperature=self.settings.structure_temperature,
        )
        self.logger = get_logger(__name__)
    
    async def transform(
        self,
        technical_content: str,
    ) -> str:
        """
        Transform plain text into structured markdown.
        
        Args:
            technical_content: Plain text from Agent 1
            
        Returns:
            Markdown-structured content
        """
        try:
            prompt = STRUCTURE_PROMPT.format(
                technical_content=technical_content,
            )
            
            self.logger.info(
                "agent_2.structure.start",
                input_length=len(technical_content),
            )
            
            response = await self.model.ainvoke(prompt)
            structured = response.content.strip()
            
            # Quick validation
            headers = structured.count("##")
            paragraphs = structured.count("\n\n")
            code_blocks = structured.count("```python")
            
            self.logger.info(
                "agent_2.structure.complete",
                output_length=len(structured),
                headers=headers,
                paragraphs=paragraphs,
                code_blocks=code_blocks,
            )
            
            return structured
            
        except Exception as e:
            self.logger.error(
                "agent_2.structure.error",
                error=str(e),
                exc_info=True,
            )
            raise

