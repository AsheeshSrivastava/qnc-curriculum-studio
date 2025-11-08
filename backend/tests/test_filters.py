from app.ingestion.chunker import TextChunk
from app.ingestion.filters import PythonRelevanceFilter


def test_python_relevance_filter_detects_keywords():
    chunk = TextChunk(index=0, content="def add(a, b):\n    return a + b", token_count=10)
    filterer = PythonRelevanceFilter(keyword_threshold=0.01)

    result = filterer.filter_relevant([chunk])

    assert len(result) == 1


def test_python_relevance_filter_rejects_irrelevant_text():
    chunk = TextChunk(index=0, content="This is a general essay about cooking.", token_count=7)
    filterer = PythonRelevanceFilter(keyword_threshold=0.05, min_keyword_hits=3)

    result = filterer.filter_relevant([chunk])

    assert len(result) == 0




