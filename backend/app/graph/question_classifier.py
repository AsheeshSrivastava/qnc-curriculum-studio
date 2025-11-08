"""Question complexity classifier for enrichment routing.

Determines whether a question needs narrative enrichment based on complexity.
"""

from __future__ import annotations

from enum import Enum


class QuestionComplexity(str, Enum):
    """Question complexity levels."""
    
    BASIC = "basic"  # Simple definitions, skip enrichment if quality >= 90
    STANDARD = "standard"  # How-to questions, always enrich
    COMPLEX = "complex"  # Multi-concept, always enrich


class QuestionClassifier:
    """Classify questions by complexity to optimize enrichment routing."""

    # Keywords that indicate complex questions
    COMPLEX_KEYWORDS = {
        "why", "when", "compare", "difference", "versus", "vs",
        "best practice", "production", "deploy", "scale",
        "architecture", "design", "pattern", "trade-off",
    }
    
    # Keywords that indicate basic questions
    BASIC_KEYWORDS = {
        "what is", "define", "definition", "meaning",
    }

    @classmethod
    def classify(cls, question: str) -> QuestionComplexity:
        """Classify a question's complexity level.
        
        Args:
            question: The user's question
            
        Returns:
            QuestionComplexity enum value
            
        Examples:
            >>> QuestionClassifier.classify("What is a variable?")
            QuestionComplexity.BASIC
            
            >>> QuestionClassifier.classify("How do I use virtual environments?")
            QuestionComplexity.STANDARD
            
            >>> QuestionClassifier.classify("Why should I use async/await in production?")
            QuestionComplexity.COMPLEX
        """
        question_lower = question.lower().strip()
        word_count = len(question.split())
        
        # Check for complex keywords
        if any(keyword in question_lower for keyword in cls.COMPLEX_KEYWORDS):
            return QuestionComplexity.COMPLEX
        
        # Check for basic keywords
        if any(keyword in question_lower for keyword in cls.BASIC_KEYWORDS):
            if word_count <= 10:
                return QuestionComplexity.BASIC
        
        # Word count heuristics
        if word_count <= 6:
            return QuestionComplexity.BASIC
        elif word_count > 25:
            return QuestionComplexity.COMPLEX
        
        # Default to standard
        return QuestionComplexity.STANDARD

    @classmethod
    def should_enrich(
        cls,
        question: str,
        quality_score: float,
        quality_threshold: float = 90.0,
    ) -> bool:
        """Determine if a question should receive narrative enrichment.
        
        Decision logic:
        - BASIC + quality >= threshold: Skip enrichment (good enough)
        - BASIC + quality < threshold: Enrich (boost quality)
        - STANDARD: Always enrich
        - COMPLEX: Always enrich
        
        Args:
            question: The user's question
            quality_score: Quality evaluation score (0-100)
            quality_threshold: Minimum score to skip enrichment (default: 90)
            
        Returns:
            True if enrichment should be applied, False otherwise
        """
        complexity = cls.classify(question)
        
        # Basic questions: only enrich if quality is low
        if complexity == QuestionComplexity.BASIC:
            return quality_score < quality_threshold
        
        # Standard and complex questions: always enrich
        return True



