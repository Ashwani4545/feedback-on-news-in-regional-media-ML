"""Configuration management for the application."""
import os
from typing import Optional


class Config:
    """Base configuration class."""
    
    # Database configuration
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./data/feedback.db")
    
    # API configuration
    API_PORT: int = int(os.environ.get("API_PORT", "8000"))
    API_HOST: str = os.environ.get("API_HOST", "0.0.0.0")
    
    # Twitter/X API configuration
    TWITTER_BEARER_TOKEN: Optional[str] = os.environ.get("TWITTER_BEARER_TOKEN")
    
    # Logging configuration
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Analysis configuration
    URGENCY_SCORE_CORRECTION: int = 8
    URGENCY_SCORE_NORMAL: int = 3
    SENTIMENT_POSITIVE_THRESHOLD: float = 0.2
    SENTIMENT_NEGATIVE_THRESHOLD: float = -0.2
    
    # Request timeouts
    REQUEST_TIMEOUT: int = 30
    
    @classmethod
    def is_sqlite(cls) -> bool:
        """Check if the database is SQLite."""
        return cls.DATABASE_URL.startswith("sqlite")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"


# Default configuration
config = Config()
