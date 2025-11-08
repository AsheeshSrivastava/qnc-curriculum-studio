"""Tests for narrative enrichment functionality."""

import pytest

from app.graph.question_classifier import QuestionClassifier, QuestionComplexity


class TestQuestionClassifier:
    """Test question complexity classification."""

    def test_classify_basic_question(self):
        """Test that simple definition questions are classified as BASIC."""
        question = "What is a variable?"
        assert QuestionClassifier.classify(question) == QuestionComplexity.BASIC

    def test_classify_standard_question(self):
        """Test that how-to questions are classified as STANDARD."""
        question = "How do I use virtual environments in Python?"
        assert QuestionClassifier.classify(question) == QuestionComplexity.STANDARD

    def test_classify_complex_question_with_why(self):
        """Test that questions with 'why' are classified as COMPLEX."""
        question = "Why should I use async/await in production?"
        assert QuestionClassifier.classify(question) == QuestionComplexity.COMPLEX

    def test_classify_complex_question_long(self):
        """Test that long questions are classified as COMPLEX."""
        question = "Can you explain the differences between lists and tuples and when I should use each one in my Python projects?"
        assert QuestionClassifier.classify(question) == QuestionComplexity.COMPLEX

    def test_should_enrich_basic_high_quality(self):
        """Test that basic questions with high quality skip enrichment."""
        question = "What is a list?"
        quality_score = 95.0
        assert QuestionClassifier.should_enrich(question, quality_score) is False

    def test_should_enrich_basic_low_quality(self):
        """Test that basic questions with low quality get enriched."""
        question = "What is a list?"
        quality_score = 75.0
        assert QuestionClassifier.should_enrich(question, quality_score) is True

    def test_should_enrich_standard_always(self):
        """Test that standard questions always get enriched."""
        question = "How do I create a virtual environment?"
        quality_score = 95.0
        assert QuestionClassifier.should_enrich(question, quality_score) is True

    def test_should_enrich_complex_always(self):
        """Test that complex questions always get enriched."""
        question = "Why is dependency management important in production?"
        quality_score = 95.0
        assert QuestionClassifier.should_enrich(question, quality_score) is True



