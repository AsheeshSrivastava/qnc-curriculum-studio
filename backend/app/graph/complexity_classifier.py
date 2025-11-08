"""Complexity classifier for adaptive content generation."""

from typing import Literal

from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

ComplexityLevel = Literal["simple", "standard", "critical"]

CLASSIFICATION_PROMPT = """Classify this Python question's complexity level.

SIMPLE: Single concept, no dependencies, beginner-friendly, straightforward answer
Examples:
- "What is print()?"
- "How to create a variable?"
- "What is the input() function?"
- "How to write a comment?"

STANDARD: Multiple aspects, some depth, requires context, moderate explanation
Examples:
- "What is Anaconda?"
- "How to import modules?"
- "What are list comprehensions?"
- "How does pip work?"

CRITICAL: Multi-layered, deep understanding needed, has sub-concepts, requires reasoning
Examples:
- "Why use virtual environments?"
- "How does pip resolve dependencies?"
- "What are decorators and when should I use them?"
- "Explain Python's GIL and its implications"

Question: {question}

Return ONLY one word: simple, standard, or critical"""


class ComplexityClassifier:
    """
    Classifies question complexity to determine appropriate content depth.
    
    Uses fast GPT-4o-mini for quick classification.
    """
    
    def __init__(self) -> None:
        settings = get_settings()
        self.model = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0.0,  # Deterministic classification
            max_tokens=10,    # Only need one word
        )
        self.logger = get_logger(__name__)
    
    async def classify(self, question: str) -> ComplexityLevel:
        """
        Classify question complexity.
        
        Args:
            question: The Python question to classify
            
        Returns:
            "simple" | "standard" | "critical"
        """
        try:
            prompt = CLASSIFICATION_PROMPT.format(question=question)
            response = await self.model.ainvoke(prompt)
            
            # Extract classification
            classification = response.content.strip().lower()
            
            # Validate and default to standard if unclear
            if classification not in ["simple", "standard", "critical"]:
                self.logger.warning(
                    "complexity.classification.invalid",
                    question=question[:50],
                    raw_response=classification,
                )
                classification = "standard"  # Safe default
            
            self.logger.info(
                "complexity.classification.complete",
                question=question[:50],
                complexity=classification,
            )
            
            return classification  # type: ignore
            
        except Exception as e:
            self.logger.error(
                "complexity.classification.error",
                question=question[:50],
                error=str(e),
                exc_info=True,
            )
            # Default to standard on error
            return "standard"
    
    @staticmethod
    def classify_heuristic(question: str) -> ComplexityLevel:
        """
        Fast heuristic-based classification (fallback).
        
        Uses keyword matching and question structure.
        """
        question_lower = question.lower()
        words = question_lower.split()
        
        # Simple indicators
        simple_keywords = [
            "what is", "what are", "how to create", "how to write",
            "define", "print", "input", "variable", "comment",
        ]
        if any(keyword in question_lower for keyword in simple_keywords):
            if len(words) < 10:  # Short question
                return "simple"
        
        # Critical indicators
        critical_keywords = [
            "why", "when should", "implications", "trade-offs",
            "best practices", "architecture", "design pattern",
            "performance", "optimization", "under the hood",
            "gil", "decorator", "metaclass", "async", "concurrency",
        ]
        if any(keyword in question_lower for keyword in critical_keywords):
            return "critical"
        
        # Multi-part questions are usually critical
        if " and " in question_lower and len(words) > 15:
            return "critical"
        
        # Default to standard
        return "standard"



