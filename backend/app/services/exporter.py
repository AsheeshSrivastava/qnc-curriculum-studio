"""Utilities to export chat responses in various formats."""

from __future__ import annotations

import io
import json
from datetime import datetime
from typing import List, Optional

from fpdf import FPDF

from app.schemas.chat import Citation, EvaluationSummary


def render_markdown(answer: str, citations: List[Citation], evaluation: Optional[EvaluationSummary]) -> str:
    lines: list[str] = ["# Research Portal Response", ""]
    lines.append("## Answer")
    lines.append(answer)

    if citations:
        lines.extend(["", "## Citations"])
        for citation in citations:
            label = citation.id
            source = citation.source or "Unknown source"
            lines.append(f"- **{label}** — {source}")

    if evaluation:
        lines.extend(["", "## Evaluation Summary", f"- Total Score: {evaluation.total_score:.2f}"])
        lines.append(f"- Passed: {'✅' if evaluation.passed else '❌'}")
        lines.append(f"- Coverage Score: {evaluation.coverage_score:.2f}")
        lines.append(f"- Citation Density: {evaluation.citation_density:.2f}")
        lines.append(f"- Execution OK: {evaluation.exec_ok}")
        lines.append(f"- Scope OK: {evaluation.scope_ok}")
        if evaluation.feedback:
            lines.append("- Feedback:")
            for item in evaluation.feedback:
                lines.append(f"  - {item}")

    lines.append("")
    lines.append(f"_Exported {datetime.utcnow().isoformat()}Z_")
    return "\n".join(lines)


def render_json(answer: str, citations: List[Citation], evaluation: Optional[EvaluationSummary]) -> bytes:
    payload = {
        "answer": answer,
        "citations": [citation.model_dump() for citation in citations],
        "evaluation": evaluation.model_dump() if evaluation else None,
        "exported_at": datetime.utcnow().isoformat() + "Z",
    }
    return json.dumps(payload, indent=2).encode("utf-8")


def render_pdf(answer: str, citations: List[Citation], evaluation: Optional[EvaluationSummary]) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Research Portal Response", ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Answer", ln=True)

    pdf.set_font("Arial", "", 11)
    for line in answer.splitlines():
        pdf.multi_cell(0, 6, line)

    if citations:
        pdf.ln(4)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Citations", ln=True)
        pdf.set_font("Arial", "", 11)
        for citation in citations:
            source = citation.source or "Unknown source"
            pdf.multi_cell(0, 6, f"{citation.id}: {source}")

    if evaluation:
        pdf.ln(4)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Evaluation Summary", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 6, f"Total Score: {evaluation.total_score:.2f}")
        pdf.multi_cell(0, 6, f"Passed: {'Yes' if evaluation.passed else 'No'}")
        pdf.multi_cell(0, 6, f"Coverage Score: {evaluation.coverage_score:.2f}")
        pdf.multi_cell(0, 6, f"Citation Density: {evaluation.citation_density:.2f}")
        pdf.multi_cell(0, 6, f"Execution OK: {evaluation.exec_ok}")
        pdf.multi_cell(0, 6, f"Scope OK: {evaluation.scope_ok}")
        if evaluation.feedback:
            pdf.multi_cell(0, 6, "Feedback:")
            for item in evaluation.feedback:
                pdf.multi_cell(0, 6, f"- {item}")

    pdf.ln(4)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 5, f"Exported {datetime.utcnow().isoformat()}Z")

    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()




