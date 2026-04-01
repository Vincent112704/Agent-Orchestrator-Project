from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from src.utils.path import get_project_root
from dotenv import load_dotenv
import logging
from src.models import Base


logging.basicConfig(level=logging.INFO)
load_dotenv()
# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")
# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # For SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session for FastAPI dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)