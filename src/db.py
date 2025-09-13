import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import DEFAULT_DATA_DIR, DATABASE_URL

_engine = None  # Global engine instance

def get_engine():
    """
    Return a global SQLAlchemy engine using the DATABASE_URL from config.

    Returns:
        Engine: The SQLAlchemy engine instance for database connections.

    Raises:
        RuntimeError: If the DATABASE_URL is not set.
    """
    global _engine
    if _engine is not None:
        return _engine
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    _engine = create_engine(DATABASE_URL, echo=False, future=True)
    return _engine

def get_session():
    """
    Create and return a new SQLAlchemy session using the engine from get_engine().

    Returns:
        Session: A new SQLAlchemy session object for database operations.
    """
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return SessionLocal()
