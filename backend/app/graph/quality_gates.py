"""Quality Gates - Lightweight checks between agents."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GateResult:
    """Result of a quality gate check."""
    passed: bool
    message: str
    metrics: dict[str, int | float]


class QualityGates:
    """Lightweight quality checks between agents."""
    
    @staticmethod
    def gate_1_technical(content: str) -> GateResult:
        """
        Check Agent 1 output: Technical synthesis.
        
        Requirements:
        - Code blocks ≥ 3
        - Citations ≥ 10
        - Has technical terms
        
        Args:
            content: Output from Agent 1
            
        Returns:
            GateResult with pass/fail and metrics
        """
        code_blocks = content.count("```python")
        citations = len(re.findall(r'\[(doc|web)-\d+\]', content))
        backticks = content.count("`")
        
        metrics = {
            "code_blocks": code_blocks,
            "citations": citations,
            "backticks": backticks,
        }
        
        issues = []
        if code_blocks < 3:
            issues.append(f"Need 3+ code blocks, found {code_blocks}")
        if citations < 10:
            issues.append(f"Need 10+ citations, found {citations}")
        if backticks < 20:
            issues.append(f"Need 20+ technical terms in backticks, found {backticks}")
        
        if issues:
            logger.warning(
                "gate_1.failed",
                issues=issues,
                metrics=metrics,
            )
            return GateResult(
                passed=False,
                message="; ".join(issues),
                metrics=metrics,
            )
        
        logger.info(
            "gate_1.passed",
            metrics=metrics,
        )
        return GateResult(
            passed=True,
            message="Technical synthesis meets requirements",
            metrics=metrics,
        )
    
    @staticmethod
    def gate_2_structure(content: str) -> GateResult:
        """
        Check Agent 2 output: Structure transformation.
        
        Requirements:
        - Headers (##) ≥ 5
        - Paragraphs (blank lines) ≥ 8
        - Code blocks preserved
        
        Args:
            content: Output from Agent 2
            
        Returns:
            GateResult with pass/fail and metrics
        """
        headers = content.count("##")
        paragraphs = content.count("\n\n")
        code_blocks = content.count("```python")
        
        metrics = {
            "headers": headers,
            "paragraphs": paragraphs,
            "code_blocks": code_blocks,
        }
        
        issues = []
        if headers < 5:
            issues.append(f"Need 5+ headers, found {headers}")
        if paragraphs < 8:
            issues.append(f"Need 8+ paragraphs, found {paragraphs}")
        if code_blocks < 3:
            issues.append(f"Code blocks lost! Found {code_blocks}")
        
        if issues:
            logger.warning(
                "gate_2.failed",
                issues=issues,
                metrics=metrics,
            )
            return GateResult(
                passed=False,
                message="; ".join(issues),
                metrics=metrics,
            )
        
        logger.info(
            "gate_2.passed",
            metrics=metrics,
        )
        return GateResult(
            passed=True,
            message="Structure transformation meets requirements",
            metrics=metrics,
        )
    
    @staticmethod
    def gate_3_compiler(
        total_score: float,
        tech_preservation: float,
    ) -> GateResult:
        """
        Check Agent 3 output: Technical compiler.
        
        Requirements:
        - Total score ≥ 95
        - Tech preservation ≥ 20
        
        Args:
            total_score: Compiler evaluation total score
            tech_preservation: Technical preservation score
            
        Returns:
            GateResult with pass/fail and metrics
        """
        metrics = {
            "total_score": total_score,
            "tech_preservation": tech_preservation,
        }
        
        issues = []
        if total_score < 95:
            issues.append(f"Need score ≥ 95, got {total_score}")
        if tech_preservation < 20:
            issues.append(f"Need tech preservation ≥ 20, got {tech_preservation}")
        
        if issues:
            logger.warning(
                "gate_3.failed",
                issues=issues,
                metrics=metrics,
            )
            return GateResult(
                passed=False,
                message="; ".join(issues),
                metrics=metrics,
            )
        
        logger.info(
            "gate_3.passed",
            metrics=metrics,
        )
        return GateResult(
            passed=True,
            message="Compiler output meets requirements",
            metrics=metrics,
        )

