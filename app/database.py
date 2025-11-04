import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./data/feedback.db')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Channel(Base):
    __tablename__ = 'channels'
    channel_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)

class Feedback(Base):
    __tablename__ = 'feedback'
    feedback_id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer)
    raw_text = Column(Text)
    received_at = Column(DateTime, default=datetime.utcnow)
    raw_metadata = Column(Text)
    language = Column(String, default='en')

def init_db():
    os.makedirs(os.path.dirname(DATABASE_URL.replace('sqlite:///','')), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print('DB initialized')
