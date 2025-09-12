import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import DEFAULT_DATA_DIR, DATABASE_URL

# Create a global SQLAlchemy engine instance using the database URL.
# The engine manages connections to the database.
_engine = create_engine(DATABASE_URL, echo=False, future=True)

# Create a configured "Session" class.
# SessionLocal() will create new Session objects for interacting with the DB.
SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)

def get_engine():
    """
    Return the global SQLAlchemy engine.

    Returns:
        Engine: The SQLAlchemy engine instance for database connections.
    """
    return _engine

def get_session():
    """
    Create and return a new SQLAlchemy session.

    Returns:
        Session: A new SQLAlchemy session object for database operations.
    """
    return SessionLocal()
