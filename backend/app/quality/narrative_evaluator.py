"""Narrative quality evaluator for story-driven content."""

from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NarrativeEvaluation:
    """Results from narrative quality evaluation."""
    
    technical_preservation: float  # 0-30 points (CRITICAL)
    complexity_alignment: float    # 0-20 points
    scenario_quality: float        # 0-20 points
    aha_moment: float             # 0-20 points (CRITICAL)
    narrative_flow: float         # 0-10 points
    total_score: float            # 0-100 points
    passed: bool                  # True if >= 80
    feedback: list[str]           # Specific improvement suggestions
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "technical_preservation": self.technical_preservation,
            "complexity_alignment": self.complexity_alignment,
            "scenario_quality": self.scenario_quality,
            "aha_moment": self.aha_moment,
            "narrative_flow": self.narrative_flow,
            "total_score": self.total_score,
            "passed": self.passed,
            "feedback": self.feedback,
        }


class NarrativeQualityEvaluator:
    """
    Evaluates narrative quality while ensuring technical integrity.
    
    Critical priorities:
    1. Technical facts must be preserved (non-negotiable)
    2. Complexity must match topic (simple stays simple, critical goes deep)
    3. "Aha moment" must be present and clear
    """
    
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
    
    def evaluate(
        self,
        narrative_content: str,
        technical_answer: str,
        citations: list[dict[str, Any]],
        complexity: str,
    ) -> NarrativeEvaluation:
        """
        Evaluate narrative quality against technical baseline.
        
        Args:
            narrative_content: Story-driven version
            technical_answer: Original technical answer
            citations: Citation list from technical answer
            complexity: simple | standard | critical
            
        Returns:
            NarrativeEvaluation with scores and feedback
        """
        feedback = []
        
        # Criterion 1: Technical Preservation (30 points) - CRITICAL
        tech_score = self._evaluate_technical_preservation(
            narrative_content, technical_answer, citations
        )
        if tech_score < 25:
            feedback.append("CRITICAL: Technical facts or citations were altered or removed")
        elif tech_score < 28:
            feedback.append("Some citations missing or technical details diluted")
        
        # Criterion 2: Complexity Alignment (20 points)
        complexity_score = self._evaluate_complexity_alignment(
            narrative_content, complexity
        )
        if complexity_score < 15:
            feedback.append(f"Content complexity doesn't match '{complexity}' level")
        
        # Criterion 3: Scenario Quality (20 points)
        scenario_score = self._evaluate_scenario_quality(narrative_content)
        if scenario_score < 15:
            feedback.append("Scenario needs improvement: ensure one character, one problem, one solution")
        
        # Criterion 4: Aha Moment (20 points) - CRITICAL
        aha_score = self._evaluate_aha_moment(narrative_content)
        if aha_score < 15:
            feedback.append("CRITICAL: 'Micro fix, macro impact' moment is unclear or missing")
        
        # Criterion 5: Narrative Flow (10 points)
        flow_score = self._evaluate_narrative_flow(narrative_content)
        if flow_score < 7:
            feedback.append("Narrative flow is choppy or disjointed")
        
        total_score = (
            tech_score + complexity_score + scenario_score + aha_score + flow_score
        )
        passed = total_score >= 80 and tech_score >= 25  # Hard floor on technical preservation
        
        self.logger.info(
            "narrative.evaluation.complete",
            total_score=total_score,
            passed=passed,
            tech_preservation=tech_score,
            aha_moment=aha_score,
        )
        
        return NarrativeEvaluation(
            technical_preservation=tech_score,
            complexity_alignment=complexity_score,
            scenario_quality=scenario_score,
            aha_moment=aha_score,
            narrative_flow=flow_score,
            total_score=total_score,
            passed=passed,
            feedback=feedback,
        )
    
    def _evaluate_technical_preservation(
        self,
        narrative: str,
        technical: str,
        citations: list[dict[str, Any]],
    ) -> float:
        """
        Check if technical facts and citations are preserved.
        
        Returns: 0-30 points
        """
        score = 30.0
        
        # Check citation preservation
        citation_ids = [c.get("id", "") for c in citations]
        missing_citations = []
        for cid in citation_ids:
            if cid and f"[{cid}]" not in narrative:
                missing_citations.append(cid)
        
        # Deduct for missing citations
        if missing_citations:
            deduction = min(10, len(missing_citations) * 2)
            score -= deduction
            self.logger.warning(
                "narrative.eval.missing_citations",
                missing=missing_citations,
                deduction=deduction,
            )
        
        # Check for code blocks preservation
        tech_code_blocks = technical.count("```")
        narrative_code_blocks = narrative.count("```")
        if narrative_code_blocks < tech_code_blocks:
            score -= 5
            self.logger.warning("narrative.eval.missing_code_blocks")
        
        # Check for key technical terms (heuristic)
        # Extract words in backticks from technical answer
        import re
        tech_terms = set(re.findall(r'`([^`]+)`', technical))
        if tech_terms:
            preserved_terms = sum(1 for term in tech_terms if f"`{term}`" in narrative or term in narrative)
            preservation_rate = preserved_terms / len(tech_terms)
            if preservation_rate < 0.7:
                score -= 5
                self.logger.warning(
                    "narrative.eval.technical_terms_lost",
                    preservation_rate=preservation_rate,
                )
        
        return max(0, score)
    
    def _evaluate_complexity_alignment(self, narrative: str, complexity: str) -> float:
        """
        Check if narrative complexity matches topic complexity.
        
        Returns: 0-20 points
        """
        word_count = len(narrative.split())
        
        # Expected word count ranges
        ranges = {
            "simple": (200, 500),    # Concise
            "standard": (400, 800),  # Balanced
            "critical": (600, 1200), # Deep
        }
        
        min_words, max_words = ranges.get(complexity, (400, 800))
        
        score = 20.0
        
        if word_count < min_words:
            score -= 10
            self.logger.warning(
                "narrative.eval.too_short",
                complexity=complexity,
                word_count=word_count,
                min_expected=min_words,
            )
        elif word_count > max_words:
            score -= 5
            self.logger.warning(
                "narrative.eval.too_long",
                complexity=complexity,
                word_count=word_count,
                max_expected=max_words,
            )
        
        # Check for Chain-of-Thought indicators in critical topics
        if complexity == "critical":
            cot_indicators = [
                "first", "then", "next", "finally",
                "step", "realize", "understand", "discover",
                "why", "because", "therefore",
            ]
            cot_count = sum(1 for indicator in cot_indicators if indicator in narrative.lower())
            if cot_count < 5:
                score -= 5
                self.logger.warning("narrative.eval.missing_cot_reasoning")
        
        return max(0, score)
    
    def _evaluate_scenario_quality(self, narrative: str) -> float:
        """
        Check scenario structure: one character, one problem, one solution.
        
        Returns: 0-20 points
        """
        score = 20.0
        narrative_lower = narrative.lower()
        
        # Check for character presence (name or pronoun pattern)
        has_character = any(
            indicator in narrative_lower
            for indicator in ["she ", "he ", "they ", "priya", "maya", "alex", "sam"]
        )
        if not has_character:
            score -= 7
            self.logger.warning("narrative.eval.no_character")
        
        # Check for problem indication
        problem_indicators = [
            "problem", "issue", "error", "broke", "failed", "stuck",
            "confused", "wondering", "struggled", "hit", "faced",
        ]
        has_problem = any(indicator in narrative_lower for indicator in problem_indicators)
        if not has_problem:
            score -= 7
            self.logger.warning("narrative.eval.no_problem")
        
        # Check for solution/resolution
        solution_indicators = [
            "solution", "fix", "solved", "realized", "discovered",
            "learned", "understood", "aha", "moment", "clicked",
        ]
        has_solution = any(indicator in narrative_lower for indicator in solution_indicators)
        if not has_solution:
            score -= 6
            self.logger.warning("narrative.eval.no_solution")
        
        return max(0, score)
    
    def _evaluate_aha_moment(self, narrative: str) -> float:
        """
        Check for clear 'micro fix, macro impact' moment.
        
        Returns: 0-20 points
        """
        score = 20.0
        narrative_lower = narrative.lower()
        
        # Check for aha moment indicators
        aha_indicators = [
            "aha", "moment", "realized", "clicked", "suddenly",
            "micro fix", "macro", "small", "big", "clarity",
            "unlock", "insight", "revelation", "discovered",
        ]
        aha_count = sum(1 for indicator in aha_indicators if indicator in narrative_lower)
        
        if aha_count == 0:
            score -= 15
            self.logger.warning("narrative.eval.no_aha_moment")
        elif aha_count < 2:
            score -= 8
            self.logger.warning("narrative.eval.weak_aha_moment")
        
        # Check for explicit micro-fix language
        has_micro_fix = "micro" in narrative_lower or "small fix" in narrative_lower
        if has_micro_fix:
            score += 0  # Bonus for explicit mention (already at max)
        
        return max(0, score)
    
    def _evaluate_narrative_flow(self, narrative: str) -> float:
        """
        Check narrative flow and readability.
        
        Returns: 0-10 points
        """
        score = 10.0
        
        # Check for paragraph structure
        paragraphs = [p.strip() for p in narrative.split("\n\n") if p.strip()]
        if len(paragraphs) < 3:
            score -= 3
            self.logger.warning("narrative.eval.insufficient_paragraphs")
        
        # Check for jarring transitions (heuristic)
        # Look for abrupt topic changes without connectors
        sentences = narrative.split(". ")
        if len(sentences) > 5:
            # Simple check: are there transition words?
            transition_words = [
                "however", "but", "then", "next", "first", "second",
                "finally", "meanwhile", "therefore", "because",
            ]
            transition_count = sum(
                1 for word in transition_words if word in narrative.lower()
            )
            if transition_count < len(sentences) * 0.1:  # At least 10% of sentences
                score -= 2
                self.logger.warning("narrative.eval.weak_transitions")
        
        return max(0, score)



