from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/orchestrator.db")

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
    from src.models import Base
    Base.metadata.create_all(bind=engine)