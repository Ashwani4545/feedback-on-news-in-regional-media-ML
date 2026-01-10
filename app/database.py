"""Database models and initialization for the feedback system."""
import os
import logging
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from app.config import config

logger = logging.getLogger(__name__)

DATABASE_URL = config.DATABASE_URL
# Only add check_same_thread for SQLite databases
connect_args = {"check_same_thread": False} if config.is_sqlite() else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Channel(Base):
    """Channel model representing feedback sources (email, twitter, etc)."""
    __tablename__ = 'channels'
    channel_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)


class Feedback(Base):
    """Feedback model representing raw feedback from various channels."""
    __tablename__ = 'feedback'
    feedback_id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channels.channel_id'))
    raw_text = Column(Text)
    received_at = Column(DateTime, default=datetime.utcnow)
    raw_metadata = Column(Text)
    language = Column(String, default='en')
    
    # Relationship to FeedbackProcessing
    processing = relationship("FeedbackProcessing", back_populates="feedback", uselist=False)


class FeedbackProcessing(Base):
    """FeedbackProcessing model representing NLP analysis results."""
    __tablename__ = 'feedback_processing'
    processing_id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, ForeignKey('feedback.feedback_id'), unique=True, index=True)
    sentiment_score = Column(Float)  # Changed from String to Float
    sentiment_label = Column(String)
    urgency = Column(Integer)
    correction_suggested = Column(Boolean)
    nlp_metadata = Column(Text)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to Feedback
    feedback = relationship("Feedback", back_populates="processing")

def init_db() -> None:
    """Initialize the database by creating all tables.
    
    For SQLite databases, ensures the directory exists before creating tables.
    For other databases (PostgreSQL, MySQL), skips directory creation.
    """
    # Only try to create directories for SQLite databases
    if config.is_sqlite():
        # Extract the file path from the SQLite URL
        db_path = DATABASE_URL.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_path)
        if db_dir:  # Only create if there's a directory path
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Created database directory: {db_dir}")
            except Exception as e:
                logger.error(f"Failed to create database directory: {e}")
                raise
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info('Database initialized successfully')
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
