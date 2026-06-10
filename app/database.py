import os
from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    DateTime, Boolean, Float, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./data/feedback.db')

# Fix: connect_args only for SQLite
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith(
    "sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Channel(Base):
    __tablename__ = 'channels'
    channel_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, default='')


class Feedback(Base):
    __tablename__ = 'feedback'
    feedback_id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, nullable=False)
    raw_text = Column(Text)
    received_at = Column(DateTime, default=datetime.utcnow)
    raw_metadata = Column(Text, default='{}')
    language = Column(String, default='en')
    # Unique tweet_id to prevent duplicates on repeated ETL runs
    tweet_id = Column(String, nullable=True, unique=True)


# Fix: this table was completely missing — caused crash on every API call
class FeedbackProcessing(Base):
    __tablename__ = 'feedback_processing'
    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, nullable=False, unique=True)
    sentiment_score = Column(Float, default=0.0)
    sentiment_label = Column(String, default='neutral')
    urgency = Column(Integer, default=3)
    correction_suggested = Column(Boolean, default=False)
    nlp_metadata = Column(Text, default='{}')
    processed_at = Column(DateTime, default=datetime.utcnow)


class TrustSnapshot(Base):
    """Rolling Audience Trust Score per channel — new differentiator feature."""
    __tablename__ = 'trust_snapshots'
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    trust_score = Column(Float, default=0.0)   # range -1.0 to 1.0
    pos_count = Column(Integer, default=0)
    neg_count = Column(Integer, default=0)
    correction_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)

    __table_args__ = (
        Index('ix_trust_channel_date', 'channel_id', 'date'),
    )


def init_db():
    os.makedirs('data', exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print('DB initialized')
