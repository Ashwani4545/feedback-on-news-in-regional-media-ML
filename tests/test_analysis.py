"""Tests for NLP analysis module."""
import pytest
from app.analysis import analyze_text


def test_analyze_positive_sentiment():
    """Test analysis of positive sentiment text."""
    result = analyze_text("This is a great article!")
    
    assert result['sentiment_label'] == 'positive'
    assert result['sentiment_score'] > 0.2
    assert result['urgency'] == 3
    assert result['correction_suggested'] is False


def test_analyze_negative_sentiment():
    """Test analysis of negative sentiment text."""
    result = analyze_text("This is a terrible and bad article")
    
    assert result['sentiment_label'] == 'negative'
    assert result['sentiment_score'] < -0.2
    assert result['urgency'] == 3  # No correction keywords
    assert result['correction_suggested'] is False


def test_analyze_neutral_sentiment():
    """Test analysis of neutral sentiment text."""
    result = analyze_text("The weather today is cloudy")
    
    assert result['sentiment_label'] == 'neutral'
    assert -0.2 <= result['sentiment_score'] <= 0.2


def test_analyze_correction_needed():
    """Test detection of correction indicators."""
    test_cases = [
        "This information is wrong",
        "Please correct this article",
        "The data is incorrect",
        "Information is missing from the report",
        "Where is the source for this claim"
    ]
    
    for text in test_cases:
        result = analyze_text(text)
        assert result['correction_suggested'] is True
        assert result['urgency'] == 8


def test_analyze_returns_required_fields():
    """Test that analyze_text returns all required fields."""
    result = analyze_text("Test text")
    
    assert 'sentiment_score' in result
    assert 'sentiment_label' in result
    assert 'urgency' in result
    assert 'correction_suggested' in result
    assert 'meta' in result
    
    # Check types
    assert isinstance(result['sentiment_score'], float)
    assert isinstance(result['sentiment_label'], str)
    assert isinstance(result['urgency'], int)
    assert isinstance(result['correction_suggested'], bool)


def test_analyze_empty_text():
    """Test analysis of empty text."""
    result = analyze_text("")
    
    assert 'sentiment_score' in result
    assert 'sentiment_label' in result
