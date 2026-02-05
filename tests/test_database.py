"""Tests for database models and initialization."""
import pytest
from sqlalchemy import inspect
from app.database import init_db, Base, Channel, Feedback, FeedbackProcessing, engine


def test_database_models_exist():
    """Test that all required models are defined."""
    assert Channel is not None
    assert Feedback is not None
    assert FeedbackProcessing is not None


def test_feedback_processing_model_fields():
    """Test that FeedbackProcessing model has all required fields."""
    # Get column names
    columns = [col.name for col in FeedbackProcessing.__table__.columns]
    
    assert 'processing_id' in columns
    assert 'feedback_id' in columns
    assert 'sentiment_score' in columns
    assert 'sentiment_label' in columns
    assert 'urgency' in columns
    assert 'correction_suggested' in columns
    assert 'nlp_metadata' in columns


def test_sentiment_score_is_float():
    """Test that sentiment_score column is Float type."""
    sentiment_score_col = FeedbackProcessing.__table__.columns['sentiment_score']
    assert str(sentiment_score_col.type) == 'FLOAT'


def test_database_initialization():
    """Test that database can be initialized without errors."""
    init_db()
    
    # Verify tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    assert 'channels' in tables
    assert 'feedback' in tables
    assert 'feedback_processing' in tables
