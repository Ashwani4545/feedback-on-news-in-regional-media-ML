"""Tests for configuration module."""
import os
import pytest
from app.config import Config, config


def test_config_has_required_attributes():
    """Test that Config class has all required attributes."""
    assert hasattr(Config, 'DATABASE_URL')
    assert hasattr(Config, 'API_PORT')
    assert hasattr(Config, 'API_HOST')
    assert hasattr(Config, 'TWITTER_BEARER_TOKEN')
    assert hasattr(Config, 'LOG_LEVEL')
    assert hasattr(Config, 'URGENCY_SCORE_CORRECTION')
    assert hasattr(Config, 'URGENCY_SCORE_NORMAL')


def test_config_is_sqlite_method():
    """Test the is_sqlite method."""
    # Test with SQLite URL
    Config.DATABASE_URL = 'sqlite:///./data/test.db'
    assert Config.is_sqlite() is True
    
    # Test with PostgreSQL URL
    Config.DATABASE_URL = 'postgresql://user:pass@localhost/db'
    assert Config.is_sqlite() is False
    
    # Reset to default
    Config.DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./data/feedback.db')


def test_config_default_values():
    """Test that config has sensible defaults."""
    assert config.API_PORT > 0
    assert config.URGENCY_SCORE_CORRECTION > config.URGENCY_SCORE_NORMAL
    assert config.REQUEST_TIMEOUT > 0
