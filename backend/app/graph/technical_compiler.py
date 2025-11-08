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


def _inject_missing_citations(
    compiled: str,
    technical_answer: str,
    missing_citations: list[str],
) -> str:
    """
    Inject missing citations back into compiled content.
    
    Strategy:
    1. Find where each citation appeared in the technical answer
    2. Extract the sentence/context around it
    3. Find similar sentence in compiled content
    4. Inject citation at the end of that sentence
    
    Args:
        compiled: The compiled content (missing citations)
        technical_answer: The original technical answer (has all citations)
        missing_citations: List of citation IDs to inject (e.g., ['doc-1', 'web-5'])
        
    Returns:
        Compiled content with missing citations injected
    """
    if not missing_citations:
        return compiled
    
    logger.info(
        "citation_injection.start",
        missing_count=len(missing_citations),
        missing=missing_citations,
    )
    
    # Split technical answer into sentences
    tech_sentences = re.split(r'(?<=[.!?])\s+', technical_answer)
    
    for citation_id in missing_citations:
        citation_tag = f"[{citation_id}]"
        
        # Find the sentence in technical answer that contains this citation
        source_sentence = None
        for sentence in tech_sentences:
            if citation_tag in sentence:
                # Remove the citation tag to get the core content
                source_sentence = sentence.replace(citation_tag, '').strip()
                break
        
        if not source_sentence:
            logger.warning(
                "citation_injection.no_source",
                citation=citation_id,
            )
            continue
        
        # Extract key terms from the source sentence (for matching)
        # Use words longer than 4 chars, excluding common words
        key_terms = [
            word.lower() for word in re.findall(r'\b\w{5,}\b', source_sentence)
            if word.lower() not in {'which', 'where', 'there', 'these', 'those', 'their', 'about'}
        ]
        
        if not key_terms:
            logger.warning(
                "citation_injection.no_key_terms",
                citation=citation_id,
                sentence=source_sentence[:100],
            )
            continue
        
        # Find the best matching sentence in compiled content
        compiled_sentences = re.split(r'(?<=[.!?])\s+', compiled)
        best_match_idx = -1
        best_match_score = 0
        
        for idx, comp_sentence in enumerate(compiled_sentences):
            comp_lower = comp_sentence.lower()
            # Count how many key terms appear in this sentence
            match_score = sum(1 for term in key_terms if term in comp_lower)
            if match_score > best_match_score:
                best_match_score = match_score
                best_match_idx = idx
        
        # If we found a good match (at least 1 key term), inject citation
        if best_match_idx >= 0 and best_match_score > 0:
            target_sentence = compiled_sentences[best_match_idx]
            
            # Don't inject if citation already exists in this sentence
            if citation_tag not in target_sentence:
                # Inject citation at the end of the sentence (before period/punctuation)
                if target_sentence.endswith('.'):
                    injected_sentence = target_sentence[:-1] + f" {citation_tag}."
                elif target_sentence.endswith('!') or target_sentence.endswith('?'):
                    injected_sentence = target_sentence[:-1] + f" {citation_tag}" + target_sentence[-1]
                else:
                    injected_sentence = target_sentence + f" {citation_tag}"
                
                compiled_sentences[best_match_idx] = injected_sentence
                
                logger.info(
                    "citation_injection.success",
                    citation=citation_id,
                    match_score=best_match_score,
                    key_terms=key_terms[:3],
                )
            else:
                logger.info(
                    "citation_injection.already_exists",
                    citation=citation_id,
                )
        else:
            logger.warning(
                "citation_injection.no_match",
                citation=citation_id,
                key_terms=key_terms[:3],
            )
    
    # Rejoin sentences
    injected_compiled = ' '.join(compiled_sentences)
    
    # Verify injection success
    final_citations = _extract_citation_ids(injected_compiled)
    injected_count = len([c for c in missing_citations if f"[{c}]" in injected_compiled])
    
    logger.info(
        "citation_injection.complete",
        attempted=len(missing_citations),
        injected=injected_count,
        success_rate=f"{injected_count/len(missing_citations)*100:.1f}%",
    )
    
    return injected_compiled

COMPILER_PROMPT = """# ROLE & CONTEXT
You are an Expert Technical Content Compiler specializing in educational restructuring.

Your PRIMARY OBJECTIVE: Transform technical content into learner-friendly format while maintaining 100% factual accuracy.

Your CRITICAL CONSTRAINT: You MUST preserve EVERY citation, code block, and technical term EXACTLY as provided. Citation loss = automatic failure.

# CITATION PRESERVATION PROTOCOL (NON-NEGOTIABLE)

## Step 1: Citation Inventory
Input contains these citations (YOU MUST USE ALL OF THEM):
{citations}

## Step 2: Citation Mapping Rules
BEFORE you restructure, understand these ABSOLUTE RULES:

1. **One-to-One Preservation**: Every [doc-X] and [web-X] from input → MUST appear in output
   - Input has [doc-1]? → Output MUST have [doc-1]
   - Input has [web-5]? → Output MUST have [web-5]
   - NO EXCEPTIONS

2. **Attachment Fidelity**: Keep citations with their ORIGINAL facts
   - If input says "Python uses duck typing [doc-3]" 
   - Output must keep [doc-3] with duck typing explanation
   - Don't move citations to different facts

3. **No Consolidation**: NEVER merge multiple citations
   - Input: "Lists are mutable [doc-1] and ordered [doc-2]"
   - Output: "Lists are mutable [doc-1] and ordered [doc-2]" ✅
   - NOT: "Lists are mutable and ordered [doc-1][doc-2]" ❌

4. **Sentence Splitting**: If you split a sentence, attach citation to the MOST RELEVANT part
   - Input: "List comprehensions are faster and more readable [web-4]"
   - If split into 2 sentences, attach [web-4] to the sentence about speed OR readability (whichever is primary)

5. **Paragraph Restructuring**: When moving content, MOVE THE CITATIONS WITH IT
   - Don't leave citations orphaned in old locations
   - Citations travel with their facts

## Step 3: Verification Checkpoint
BEFORE submitting, COUNT:
- Input citations: {citation_count}
- Output citations: [YOU MUST COUNT THESE]
- THEY MUST MATCH EXACTLY

If they don't match, you FAILED. Go back and find the missing citations.

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

RECOMPILE_PROMPT = """# RECOMPILATION TASK

## Context
You are recompiling technical content that FAILED quality evaluation. This is your second chance.

## Why You Failed
{feedback}

## Critical Constraints (Same as Before)
1. **Citation Preservation**: ALL {citation_count} citations MUST appear in output
2. **Code Preservation**: ALL code blocks MUST be preserved exactly
3. **Technical Accuracy**: NO facts can be changed or removed

## Your Source Materials

### Original Technical Answer (YOUR SOURCE OF TRUTH):
{technical_answer}

### Citations (COUNT THEM - Must be {citation_count} in your output):
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
            citation_count = len(citations)
            
            if feedback and previous_compilation:
                # Recompile with feedback
                prompt = RECOMPILE_PROMPT.format(
                    technical_answer=technical_answer,
                    citations=citations_str,
                    citation_count=citation_count,
                    previous_compilation=previous_compilation,
                    feedback="\n".join(feedback),
                )
            else:
                # Initial compilation
                prompt = COMPILER_PROMPT.format(
                    technical_answer=technical_answer,
                    citations=citations_str,
                    citation_count=citation_count,
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
                
                # CITATION PRESERVATION LAYER: Inject missing citations back
                self.logger.info(
                    "compiler.citation_injection.starting",
                    missing_count=len(missing_citations),
                )
                compiled = _inject_missing_citations(
                    compiled=compiled,
                    technical_answer=technical_answer,
                    missing_citations=missing_citations,
                )
                
                # Re-verify after injection
                still_missing = [
                    cid for cid in citation_ids if cid and f"[{cid}]" not in compiled
                ]
                if still_missing:
                    self.logger.error(
                        "compiler.citation_injection.failed",
                        still_missing=still_missing,
                    )
                else:
                    self.logger.info(
                        "compiler.citation_injection.success",
                        recovered=len(missing_citations),
                    )
            
            final_citations_preserved = len([
                cid for cid in citation_ids if cid and f"[{cid}]" in compiled
            ])
            
            self.logger.info(
                "compiler.complete",
                compiled_length=len(compiled),
                citations_preserved=final_citations_preserved,
                citations_total=len(citation_ids),
                preservation_rate=f"{final_citations_preserved/max(1, len(citation_ids))*100:.1f}%",
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

