"""Compiler quality evaluator for PSW-structured content."""

from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CompilerEvaluation:
    """Results from compiler quality evaluation."""
    
    technical_preservation: float  # 0-30 points (CRITICAL)
    psw_structure: float          # 0-20 points
    micro_fix_clarity: float      # 0-20 points (CRITICAL)
    real_world_integration: float # 0-15 points
    reflective_depth: float       # 0-15 points
    total_score: float            # 0-100 points
    passed: bool                  # True if >= 95
    feedback: list[str]           # Specific improvement suggestions
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "technical_preservation": self.technical_preservation,
            "psw_structure": self.psw_structure,
            "micro_fix_clarity": self.micro_fix_clarity,
            "real_world_integration": self.real_world_integration,
            "reflective_depth": self.reflective_depth,
            "total_score": self.total_score,
            "passed": self.passed,
            "feedback": self.feedback,
        }


class CompilerQualityEvaluator:
    """
    Evaluates compiled content for PSW structure and learning effectiveness.
    
    Critical priorities:
    1. Technical facts must be preserved (non-negotiable)
    2. PSW structure must be subtle and natural
    3. "Small fixes, big clarity" must be explicit
    """
    
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
    
    def evaluate(
        self,
        compiled_content: str,
        technical_baseline: str,
    ) -> CompilerEvaluation:
        """
        Evaluate compiled content quality.
        
        Args:
            compiled_content: The compiled PSW-structured content
            technical_baseline: Original technical answer for comparison
            
        Returns:
            CompilerEvaluation with scores and feedback
        """
        feedback = []
        
        # Criterion 1: Technical Preservation (30 points) - CRITICAL
        tech_score = self._evaluate_technical_preservation(
            compiled_content, technical_baseline
        )
        if tech_score < 28:
            feedback.append("CRITICAL: Technical facts or citations were altered or removed")
        elif tech_score < 30:
            feedback.append("Some citations missing or technical details diluted")
        
        # Criterion 2: PSW Structure (20 points)
        psw_score = self._evaluate_psw_structure(compiled_content)
        if psw_score < 15:
            feedback.append("PSW structure is too explicit or missing natural flow")
        
        # Criterion 3: Micro-Fix Clarity (20 points) - CRITICAL
        micro_fix_score = self._evaluate_micro_fix_clarity(compiled_content)
        if micro_fix_score < 15:
            feedback.append("CRITICAL: 'Small fixes, big clarity' moment is unclear or missing")
        
        # Criterion 4: Real-World Integration (15 points)
        real_world_score = self._evaluate_real_world_integration(compiled_content)
        if real_world_score < 12:
            feedback.append("Need more embedded examples AND dedicated Real-World Examples section")
        
        # Criterion 5: Reflective Depth (15 points)
        reflective_score = self._evaluate_reflective_depth(compiled_content)
        if reflective_score < 12:
            feedback.append("Need more 'Consider...' prompts throughout AND final reflection question")
        
        total_score = (
            tech_score + psw_score + micro_fix_score + real_world_score + reflective_score
        )
        passed = total_score >= 95 and tech_score >= 28  # Hard floor on technical preservation
        
        self.logger.info(
            "compiler.evaluation.complete",
            total_score=total_score,
            passed=passed,
            tech_preservation=tech_score,
            micro_fix=micro_fix_score,
        )
        
        return CompilerEvaluation(
            technical_preservation=tech_score,
            psw_structure=psw_score,
            micro_fix_clarity=micro_fix_score,
            real_world_integration=real_world_score,
            reflective_depth=reflective_score,
            total_score=total_score,
            passed=passed,
            feedback=feedback,
        )
    
    def _evaluate_technical_preservation(
        self,
        compiled: str,
        technical: str,
    ) -> float:
        """
        Check if technical facts and citations are preserved.
        
        Returns: 0-30 points
        """
        score = 30.0
        
        # Check citation preservation
        import re
        tech_citations = set(re.findall(r'\[(doc|web)-\d+\]', technical))
        compiled_citations = set(re.findall(r'\[(doc|web)-\d+\]', compiled))
        
        missing_citations = tech_citations - compiled_citations
        if missing_citations:
            deduction = min(10, len(missing_citations) * 2)
            score -= deduction
            self.logger.warning(
                "compiler.eval.missing_citations",
                missing=list(missing_citations),
                deduction=deduction,
            )
        
        # Check for code blocks preservation (must have at least some code blocks if technical had them)
        tech_code_blocks = technical.count("```")
        compiled_code_blocks = compiled.count("```")
        if tech_code_blocks > 0 and compiled_code_blocks == 0:
            # No code blocks at all - major issue
            score -= 10
            self.logger.warning("compiler.eval.no_code_blocks")
        elif tech_code_blocks > 0 and compiled_code_blocks < (tech_code_blocks * 0.5):
            # Less than half the code blocks - minor issue
            score -= 3
            self.logger.warning("compiler.eval.reduced_code_blocks", 
                              tech=tech_code_blocks, compiled=compiled_code_blocks)
        
        # Check for key technical terms (more lenient - just check if they appear anywhere)
        tech_terms = set(re.findall(r'`([^`]+)`', technical))
        if tech_terms:
            # Check if term appears anywhere in compiled (with or without backticks)
            preserved_terms = sum(1 for term in tech_terms if term.lower() in compiled.lower())
            preservation_rate = preserved_terms / len(tech_terms)
            if preservation_rate < 0.6:  # Lowered from 0.8 to 0.6
                score -= 5
                self.logger.warning(
                    "compiler.eval.technical_terms_lost",
                    preservation_rate=preservation_rate,
                )
        
        return max(0, score)
    
    def _evaluate_psw_structure(self, compiled: str) -> float:
        """
        Check for subtle PSW structure (no explicit labels).
        
        Returns: 0-20 points
        """
        score = 20.0
        compiled_lower = compiled.lower()
        
        # Check for explicit PSW labels (should NOT be present)
        if "problem:" in compiled_lower or "system:" in compiled_lower or "win:" in compiled_lower:
            score -= 10
            self.logger.warning("compiler.eval.explicit_psw_labels")
        
        # Check for problem framing (opening)
        problem_indicators = [
            "challenge", "question", "issue", "problem", "why", "when",
            "matter", "important", "pain point", "difficulty"
        ]
        has_problem = any(indicator in compiled_lower[:500] for indicator in problem_indicators)
        if not has_problem:
            score -= 5
            self.logger.warning("compiler.eval.no_problem_framing")
        
        # Check for system explanation (middle)
        system_indicators = [
            "how", "works", "components", "technically", "mechanism",
            "process", "steps", "architecture"
        ]
        has_system = any(indicator in compiled_lower for indicator in system_indicators)
        if not has_system:
            score -= 5
            self.logger.warning("compiler.eval.no_system_explanation")
        
        # Check for win/impact (end)
        win_indicators = [
            "enables", "improves", "benefit", "impact", "advantage",
            "workflow", "productivity", "efficiency"
        ]
        has_win = any(indicator in compiled_lower[-500:] for indicator in win_indicators)
        if not has_win:
            score -= 5
            self.logger.warning("compiler.eval.no_win_impact")
        
        return max(0, score)
    
    def _evaluate_micro_fix_clarity(self, compiled: str) -> float:
        """
        Check for clear 'micro fix, macro impact' moment.
        
        Returns: 0-20 points
        """
        score = 20.0
        compiled_lower = compiled.lower()
        
        # Check for micro-fix language
        micro_fix_indicators = [
            "small fix", "micro fix", "small change", "simple change",
            "one change", "key insight", "crucial detail", "critical point",
            "big clarity", "macro impact", "big impact", "unlocks",
        ]
        micro_fix_count = sum(1 for indicator in micro_fix_indicators if indicator in compiled_lower)
        
        if micro_fix_count == 0:
            score -= 15
            self.logger.warning("compiler.eval.no_micro_fix")
        elif micro_fix_count < 2:
            score -= 8
            self.logger.warning("compiler.eval.weak_micro_fix")
        
        # Check for explicit "small fixes, big clarity" phrase
        if "small fix" in compiled_lower and ("big clarity" in compiled_lower or "macro" in compiled_lower):
            # Bonus for explicit mention (already at good score)
            pass
        
        return max(0, score)
    
    def _evaluate_real_world_integration(self, compiled: str) -> float:
        """
        Check for embedded examples AND dedicated section.
        
        Returns: 0-15 points
        """
        score = 15.0
        compiled_lower = compiled.lower()
        
        # Check for dedicated "Real-World Examples" section
        has_section = "real-world example" in compiled_lower or "real world example" in compiled_lower
        if not has_section:
            score -= 7
            self.logger.warning("compiler.eval.no_realworld_section")
        
        # Check for embedded examples throughout
        example_indicators = [
            "for example", "for instance", "consider", "imagine",
            "in practice", "production", "real-world", "industry"
        ]
        example_count = sum(1 for indicator in example_indicators if indicator in compiled_lower)
        
        if example_count < 3:
            score -= 5
            self.logger.warning("compiler.eval.insufficient_embedded_examples", count=example_count)
        
        return max(0, score)
    
    def _evaluate_reflective_depth(self, compiled: str) -> float:
        """
        Check for 'Consider...' prompts AND final reflection.
        
        Returns: 0-15 points
        """
        score = 15.0
        compiled_lower = compiled.lower()
        
        # Check for "Consider..." prompts throughout
        consider_count = compiled_lower.count("consider")
        if consider_count < 3:
            score -= 7
            self.logger.warning("compiler.eval.insufficient_consider_prompts", count=consider_count)
        
        # Check for dedicated Reflection section
        has_reflection = "reflection" in compiled_lower or "think about" in compiled_lower
        if not has_reflection:
            score -= 5
            self.logger.warning("compiler.eval.no_reflection_section")
        
        # Check for question in reflection
        if has_reflection and "?" not in compiled[-300:]:
            score -= 3
            self.logger.warning("compiler.eval.no_reflection_question")
        
        return max(0, score)

