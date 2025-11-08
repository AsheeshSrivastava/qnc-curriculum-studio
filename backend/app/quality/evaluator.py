"""Heuristic quality evaluator for agent responses."""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List

from app.quality.rubric import CRITERIA, QUALITY_GATES, TOTAL_POINTS, Criterion


@dataclass(slots=True)
class CriterionScore:
    key: str
    score: float
    max_points: int
    rationale: str


@dataclass(slots=True)
class EvaluationReport:
    total_score: float
    criteria: Dict[str, CriterionScore]
    coverage_score: float
    citation_density: float
    exec_ok: bool
    scope_ok: bool
    passed: bool
    feedback: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_score": round(self.total_score, 2),
            "criteria": {key: asdict(value) for key, value in self.criteria.items()},
            "coverage_score": round(self.coverage_score, 3),
            "citation_density": round(self.citation_density, 3),
            "exec_ok": self.exec_ok,
            "scope_ok": self.scope_ok,
            "passed": self.passed,
            "feedback": self.feedback,
        }


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def _sentence_lengths(answer: str) -> List[int]:
    sentences = [
        segment.strip()
        for segment in answer.replace("?", ".").replace("!", ".").split(".")
        if segment.strip()
    ]
    return [len(sentence.split()) for sentence in sentences if sentence]


class QualityEvaluator:
    """Rate answers against the Production-Grade Quality Framework."""

    def __init__(
        self,
        *,
        min_total_score: float = 85.0,
        coverage_threshold: float = QUALITY_GATES["coverage_score"],
        citation_density_threshold: float = QUALITY_GATES["citation_density"],
    ) -> None:
        self.min_total_score = min_total_score
        self.coverage_threshold = coverage_threshold
        self.citation_density_threshold = citation_density_threshold

    def evaluate(
        self,
        *,
        question: str,
        answer: str,
        documents: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
    ) -> EvaluationReport:
        answer_lower = answer.lower()
        doc_count = len(documents)
        unique_doc_citations = {
            citation["metadata"]["document_id"]
            for citation in citations
            if citation.get("type") == "document"
            and citation.get("metadata", {}).get("document_id")
        }
        coverage_score = (
            1.0
            if doc_count == 0
            else min(1.0, len(unique_doc_citations) / max(1, doc_count))
        )

        word_count = max(1, len(answer.split()))
        citations_count = len(citations)
        citation_density = citations_count / max(1.0, word_count / 150.0)

        exec_ok = "```" in answer or _contains_any(answer, ["import ", "def ", "class "])
        scope_ok = _contains_any(answer, question.lower().split()) or "python" in answer_lower

        criterion_scores: Dict[str, CriterionScore] = {}
        feedback: List[str] = []
        total = 0.0

        for criterion in CRITERIA:
            score, rationale = self._score_criterion(
                criterion,
                question=question,
                answer=answer,
                answer_lower=answer_lower,
                coverage_score=coverage_score,
                citation_density=citation_density,
                citations_count=citations_count,
            )
            total += score
            criterion_scores[criterion.key] = CriterionScore(
                key=criterion.key,
                score=round(score, 2),
                max_points=criterion.max_points,
                rationale=rationale,
            )
            if score < 0.7 * criterion.max_points:
                feedback.append(f"Improve {criterion.title.lower()}: {rationale}")

        if coverage_score < self.coverage_threshold:
            feedback.append(
                f"Coverage below threshold ({coverage_score:.2f} < {self.coverage_threshold}); cite more relevant chunks."
            )

        if citation_density < self.citation_density_threshold:
            feedback.append(
                f"Citation density low ({citation_density:.2f}); attach citations to substantive claims."
            )

        if not exec_ok:
            feedback.append("Add runnable Python snippets or detail execution expectations.")

        if not scope_ok:
            feedback.append("Keep the answer aligned with the question scope and Python focus.")

        passed = (
            total >= self.min_total_score
            and coverage_score >= self.coverage_threshold
            and citation_density >= self.citation_density_threshold
            and exec_ok
            and scope_ok
        )

        return EvaluationReport(
            total_score=total,
            criteria=criterion_scores,
            coverage_score=coverage_score,
            citation_density=citation_density,
            exec_ok=exec_ok,
            scope_ok=scope_ok,
            passed=passed,
            feedback=feedback,
        )

    def _score_criterion(
        self,
        criterion: Criterion,
        *,
        question: str,
        answer: str,
        answer_lower: str,
        coverage_score: float,
        citation_density: float,
        citations_count: int,
    ) -> tuple[float, str]:
        weight = criterion.max_points

        if criterion.key == "groundedness":
            multiplier = 0.5 * coverage_score + 0.5 * min(1.0, citation_density / 1.5)
            return weight * multiplier, f"Coverage={coverage_score:.2f}, density={citation_density:.2f}"

        if criterion.key == "technical_correctness":
            python_keywords = {"def", "class", "import", "lambda", "async", "await", "yield"}
            matches = sum(1 for keyword in python_keywords if keyword in answer_lower)
            multiplier = min(1.0, matches / 3.0)
            if "traceback" in answer_lower or "error" in answer_lower:
                multiplier = min(multiplier, 0.6)
            return weight * multiplier, f"{matches} python keywords detected"

        if criterion.key == "people_first_pedagogy":
            phrases = ["let's", "you will", "we will", "consider"]
            multiplier = 1.0 if _contains_any(answer, phrases) else 0.6
            return weight * multiplier, "Conversational guidance" if multiplier == 1.0 else "Add learner-centered framing"

        if criterion.key == "psw_actionability":
            has_problem = _contains_any(answer, ["problem", "challenge"])
            has_system = _contains_any(answer, ["system", "environment", "context"])
            has_win = _contains_any(answer, ["win", "benefit", "outcome", "solution"])
            matches = sum([has_problem, has_system, has_win])
            multiplier = matches / 3.0
            return weight * multiplier, f"PSW coverage {matches}/3 elements"

        if criterion.key == "mode_fidelity":
            socratic_cues = _contains_any(answer, ["consider", "what if", "how might"])
            directive_cues = _contains_any(answer, ["step", "first", "next"])
            multiplier = 1.0 if socratic_cues or directive_cues else 0.6
            return weight * multiplier, "Mode cues detected" if multiplier == 1.0 else "Add coaching prompts"

        if criterion.key == "self_paced_scaffolding":
            has_steps = any(
                token.strip().startswith(tuple(f"{i}." for i in range(1, 6)))
                for token in answer.splitlines()
            )
            multiplier = 1.0 if has_steps else 0.5
            return weight * multiplier, "Numbered steps provided" if has_steps else "Add a stepwise plan"

        if criterion.key == "retrieval_quality":
            multiplier = coverage_score
            if citations_count == 0:
                multiplier *= 0.4
            return weight * multiplier, f"Coverage score {coverage_score:.2f}"

        if criterion.key == "clarity":
            lengths = _sentence_lengths(answer)
            if not lengths:
                return weight * 0.4, "No declarative sentences detected"
            avg = statistics.mean(lengths)
            multiplier = 1.0 if 8 <= avg <= 28 else 0.7
            return weight * multiplier, f"Average sentence length {avg:.1f} words"

        if criterion.key == "bloom_alignment":
            verbs = {"implement", "design", "analyze", "explain", "compare"}
            matches = sum(1 for verb in verbs if verb in answer_lower)
            multiplier = min(1.0, matches / 2.0)
            return weight * multiplier, f"{matches} higher-order verbs detected"

        if criterion.key == "people_first_language":
            inclusive_phrases = {"please", "consider", "let's", "together", "feel free"}
            negative_terms = {"idiot", "stupid", "lazy"}
            multiplier = 1.0 if _contains_any(answer, inclusive_phrases) and not _contains_any(answer, negative_terms) else 0.5
            return weight * multiplier, "Respectful tone" if multiplier == 1.0 else "Adopt more respectful phrasing"

        return float(weight), "Full credit"




