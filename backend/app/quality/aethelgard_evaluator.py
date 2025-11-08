"""Aethelgard brand quality evaluator for final content polish."""

from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AethelgardEvaluation:
    """Results from Aethelgard brand quality evaluation."""
    
    brand_voice: float          # 0-25 points (CRITICAL)
    keyword_integration: float  # 0-20 points
    rag_structure: float        # 0-20 points
    final_quality: float        # 0-20 points
    uniqueness: float           # 0-15 points
    total_score: float          # 0-100 points
    passed: bool                # True if >= 85
    feedback: list[str]         # Specific improvement suggestions
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "brand_voice": self.brand_voice,
            "keyword_integration": self.keyword_integration,
            "rag_structure": self.rag_structure,
            "final_quality": self.final_quality,
            "uniqueness": self.uniqueness,
            "total_score": self.total_score,
            "passed": self.passed,
            "feedback": self.feedback,
        }


class AethelgardQualityEvaluator:
    """
    Evaluates content for Aethelgard Academy brand consistency and RAG optimization.
    
    Brand pillars:
    - Honest: Acknowledges complexity, no false simplification
    - Reflective: Encourages thinking, includes thought-provoking questions
    - Clear: Micro fixes that create macro clarity
    """
    
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
    
    def evaluate(
        self,
        content: str,
        technical_baseline_score: float,
    ) -> AethelgardEvaluation:
        """
        Evaluate content for Aethelgard brand and RAG compliance.
        
        Args:
            content: Final polished content
            technical_baseline_score: Original technical quality score (must not degrade)
            
        Returns:
            AethelgardEvaluation with scores and feedback
        """
        feedback = []
        
        # Criterion 1: Brand Voice (25 points) - CRITICAL
        brand_score = self._evaluate_brand_voice(content)
        if brand_score < 20:
            feedback.append("CRITICAL: Brand voice (honest, reflective, clear) is weak or missing")
        
        # Criterion 2: Keyword Integration (20 points)
        keyword_score = self._evaluate_keyword_integration(content)
        if keyword_score < 15:
            feedback.append("Keywords missing or poorly integrated for RAG retrieval")
        
        # Criterion 3: RAG Structure (20 points)
        rag_score = self._evaluate_rag_structure(content)
        if rag_score < 15:
            feedback.append("Content structure not optimized for RAG/chatbot retrieval")
        
        # Criterion 4: Final Quality (20 points)
        # Check if quality was maintained from technical baseline
        quality_score = self._evaluate_quality_preservation(
            content, technical_baseline_score
        )
        if quality_score < 15:
            feedback.append("Quality degraded from technical baseline")
        
        # Criterion 5: Uniqueness (15 points)
        uniqueness_score = self._evaluate_uniqueness(content)
        if uniqueness_score < 10:
            feedback.append("Content feels generic, lacks Aethelgard distinctiveness")
        
        total_score = (
            brand_score + keyword_score + rag_score + quality_score + uniqueness_score
        )
        passed = total_score >= 85 and brand_score >= 20  # Hard floor on brand voice
        
        self.logger.info(
            "aethelgard.evaluation.complete",
            total_score=total_score,
            passed=passed,
            brand_voice=brand_score,
            uniqueness=uniqueness_score,
        )
        
        return AethelgardEvaluation(
            brand_voice=brand_score,
            keyword_integration=keyword_score,
            rag_structure=rag_score,
            final_quality=quality_score,
            uniqueness=uniqueness_score,
            total_score=total_score,
            passed=passed,
            feedback=feedback,
        )
    
    def _evaluate_brand_voice(self, content: str) -> float:
        """
        Check for Aethelgard brand voice: honest, reflective, clear.
        
        Returns: 0-25 points
        """
        score = 25.0
        content_lower = content.lower()
        
        # Check for HONEST voice (acknowledges complexity)
        honesty_indicators = [
            "complex", "confusing", "tricky", "subtle", "nuanced",
            "at first", "initially", "seems", "can be",
            "important to understand", "worth noting",
        ]
        honesty_count = sum(1 for indicator in honesty_indicators if indicator in content_lower)
        if honesty_count == 0:
            score -= 8
            self.logger.warning("aethelgard.eval.missing_honesty")
        elif honesty_count < 2:
            score -= 4
        
        # Check for REFLECTIVE voice (thought-provoking questions)
        has_reflection_question = "?" in content and any(
            phrase in content_lower
            for phrase in [
                "think about", "consider", "reflect", "imagine",
                "what if", "how might", "when was", "have you",
            ]
        )
        if not has_reflection_question:
            score -= 8
            self.logger.warning("aethelgard.eval.missing_reflection")
        
        # Check for CLEAR voice (micro fix, macro clarity)
        clarity_indicators = [
            "micro", "small fix", "small change", "one command", "one line",
            "clarity", "clear", "simple", "straightforward",
            "aha", "moment", "clicked", "realized",
        ]
        clarity_count = sum(1 for indicator in clarity_indicators if indicator in content_lower)
        if clarity_count == 0:
            score -= 9
            self.logger.warning("aethelgard.eval.missing_clarity_language")
        elif clarity_count < 2:
            score -= 4
        
        return max(0, score)
    
    def _evaluate_keyword_integration(self, content: str) -> float:
        """
        Check for natural and metadata keyword integration.
        
        Returns: 0-20 points
        """
        score = 20.0
        
        # Check for metadata keywords section
        has_metadata_keywords = "**Keywords:**" in content or "**keywords:**" in content.lower()
        if not has_metadata_keywords:
            score -= 8
            self.logger.warning("aethelgard.eval.missing_keywords_metadata")
        
        # Check for Quick Answer section (for chatbot)
        has_quick_answer = "**Quick Answer" in content or "**quick answer" in content.lower()
        if not has_quick_answer:
            score -= 7
            self.logger.warning("aethelgard.eval.missing_quick_answer")
        
        # Check for natural keyword integration (technical terms in backticks)
        import re
        backtick_terms = len(re.findall(r'`[^`]+`', content))
        if backtick_terms < 5:
            score -= 5
            self.logger.warning(
                "aethelgard.eval.insufficient_technical_terms",
                count=backtick_terms,
            )
        
        return max(0, score)
    
    def _evaluate_rag_structure(self, content: str) -> float:
        """
        Check for RAG-friendly structure.
        
        Returns: 0-20 points
        """
        score = 20.0
        
        # Check for clear sections/headers
        header_count = content.count("**")
        if header_count < 4:  # At least 2 sections (4 asterisks)
            score -= 7
            self.logger.warning("aethelgard.eval.insufficient_structure")
        
        # Check for Related Concepts section
        has_related_concepts = "**Related Concepts" in content or "**related concepts" in content.lower()
        if not has_related_concepts:
            score -= 6
            self.logger.warning("aethelgard.eval.missing_related_concepts")
        
        # Check for scannable content (paragraphs, not walls of text)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if len(paragraphs) < 4:
            score -= 4
            self.logger.warning("aethelgard.eval.insufficient_paragraphs")
        
        # Check for code blocks (important for technical RAG)
        code_blocks = content.count("```")
        if code_blocks < 2:  # At least one code block (2 backticks)
            score -= 3
            self.logger.warning("aethelgard.eval.missing_code_blocks")
        
        return max(0, score)
    
    def _evaluate_quality_preservation(
        self,
        content: str,
        baseline_score: float,
    ) -> float:
        """
        Check if quality was preserved from technical baseline.
        
        Returns: 0-20 points
        """
        score = 20.0
        
        # Heuristic: Check if content is substantially longer (might indicate bloat)
        word_count = len(content.split())
        if word_count > 1500:  # Very long
            score -= 5
            self.logger.warning(
                "aethelgard.eval.excessive_length",
                word_count=word_count,
            )
        
        # Check if citations are still present
        citation_count = content.count("[doc-") + content.count("[web-")
        if citation_count < 3:
            score -= 8
            self.logger.warning(
                "aethelgard.eval.insufficient_citations",
                count=citation_count,
            )
        
        # Check if code blocks are present
        if "```" not in content:
            score -= 7
            self.logger.warning("aethelgard.eval.no_code_examples")
        
        return max(0, score)
    
    def _evaluate_uniqueness(self, content: str) -> float:
        """
        Check if content feels unique and distinctive.
        
        Returns: 0-15 points
        """
        score = 15.0
        content_lower = content.lower()
        
        # Check for scenario/character (makes it unique)
        has_character = any(
            name in content_lower
            for name in ["priya", "maya", "alex", "sam", "she ", "he ", "they "]
        )
        if not has_character:
            score -= 5
            self.logger.warning("aethelgard.eval.no_character_scenario")
        
        # Check for storytelling elements
        storytelling_indicators = [
            "realized", "discovered", "moment", "clicked",
            "struggled", "wondered", "tried", "found",
        ]
        storytelling_count = sum(
            1 for indicator in storytelling_indicators if indicator in content_lower
        )
        if storytelling_count < 2:
            score -= 5
            self.logger.warning("aethelgard.eval.weak_storytelling")
        
        # Check for Aethelgard-specific language
        aethelgard_markers = [
            "micro fix", "macro", "small fix", "big clarity",
            "aha moment", "clicked", "unlocked",
        ]
        has_aethelgard_language = any(
            marker in content_lower for marker in aethelgard_markers
        )
        if not has_aethelgard_language:
            score -= 5
            self.logger.warning("aethelgard.eval.missing_brand_language")
        
        return max(0, score)



