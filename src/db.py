import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import DEFAULT_DATA_DIR

# Get the database URL from an environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

_engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)

def get_engine():
    """Return the global SQLAlchemy engine."""
    return _engine

def get_session():
    """Create a new SQLAlchemy session."""
    return SessionLocal()
