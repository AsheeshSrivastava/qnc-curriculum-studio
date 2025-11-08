"""Rubric definitions for production-grade Python content."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, List


@dataclass(frozen=True, slots=True)
class Criterion:
    key: str
    title: str
    max_points: int
    description: str


CRITERIA: Final[List[Criterion]] = [
    Criterion(
        key="groundedness",
        title="Groundedness & Citation",
        max_points=20,
        description="Evidence-based reasoning with explicit citations.",
    ),
    Criterion(
        key="technical_correctness",
        title="Technical Correctness",
        max_points=15,
        description="Python guidance is accurate and free from errors.",
    ),
    Criterion(
        key="people_first_pedagogy",
        title="People-First Pedagogy",
        max_points=15,
        description="Clear, empathetic instruction anchored in adult learning principles.",
    ),
    Criterion(
        key="psw_actionability",
        title="PSW Actionability",
        max_points=10,
        description="Identifies Problem, System, and actionable Wins for the reader.",
    ),
    Criterion(
        key="mode_fidelity",
        title="Mode Fidelity",
        max_points=10,
        description="Aligns with the intended coaching mode (coach/hybrid/socratic).",
    ),
    Criterion(
        key="self_paced_scaffolding",
        title="Self-Paced Scaffolding",
        max_points=10,
        description="Guides learners through progressive difficulty with checkpoints.",
    ),
    Criterion(
        key="retrieval_quality",
        title="Retrieval Quality",
        max_points=10,
        description="Selects context that is relevant, diverse, and non-redundant.",
    ),
    Criterion(
        key="clarity",
        title="Clarity",
        max_points=5,
        description="Communicates with succinct, easy-to-follow phrasing.",
    ),
    Criterion(
        key="bloom_alignment",
        title="Bloom Alignment",
        max_points=3,
        description="Targets the correct cognitive depth for the task.",
    ),
    Criterion(
        key="people_first_language",
        title="People-First Language",
        max_points=2,
        description="Uses inclusive, respectful language throughout.",
    ),
]


TOTAL_POINTS: Final[int] = sum(criterion.max_points for criterion in CRITERIA)

QUALITY_GATES = {
    "coverage_score": 0.65,
    "citation_density": 1.0,
    "exec_ok": True,
    "scope_ok": True,
}




