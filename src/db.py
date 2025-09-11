import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import DEFAULT_DATA_DIR

_engine = create_engine("postgresql://postgres:jahmillionare13386@localhost:5432/bank_db", echo=False, future=True)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)

def get_engine():
    """Return the global SQLAlchemy engine."""
    return _engine

def get_session():
    """Create a new SQLAlchemy session."""
    return SessionLocal()
