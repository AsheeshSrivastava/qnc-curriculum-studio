"""Utilities to ensure content is Python-focused."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

from .chunker import TextChunk

PYTHON_KEYWORDS = {
    "def",
    "class",
    "import",
    "from",
    "async",
    "await",
    "lambda",
    "yield",
    "with",
    "try",
    "except",
    "finally",
    "global",
    "nonlocal",
    "pass",
    "raise",
    "return",
    "for",
    "while",
    "if",
    "elif",
    "else",
    "match",
    "case",
    "type",
    "typing",
    "pytest",
    "pip",
    "virtualenv",
    "poetry",
    "fastapi",
    "langchain",
}

CODE_BLOCK_PATTERN = re.compile(r"```(?:python)?(.*?)```", re.IGNORECASE | re.DOTALL)


class PythonRelevanceFilter:
    """Simple heuristic filter to ensure chunks are Python-centric."""

    def __init__(self, keyword_threshold: float = 0.02, min_keyword_hits: int = 2) -> None:
        self.keyword_threshold = keyword_threshold
        self.min_keyword_hits = min_keyword_hits

    def filter_relevant(self, chunks: Iterable[TextChunk]) -> list[TextChunk]:
        relevant: list[TextChunk] = []
        for chunk in chunks:
            score = self.score_chunk(chunk.content)
            if score >= self.keyword_threshold:
                relevant.append(chunk)
        return relevant

    def score_chunk(self, text: str) -> float:
        lowered = text.lower()
        code_blocks = CODE_BLOCK_PATTERN.findall(lowered)
        if code_blocks:
            return 1.0

        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", lowered)
        if not tokens:
            return 0.0

        counts = Counter(tokens)
        hits = sum(counts[key] for key in PYTHON_KEYWORDS if key in counts)
        if hits < self.min_keyword_hits:
            return 0.0

        return hits / math.sqrt(len(tokens))




