"""
Database session management and initialization.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine = None
_SessionLocal = None


def get_engine():
    """
    Get or create the database engine.
    
    Returns:
        Engine: SQLAlchemy engine
    """
    global _engine
    
    if _engine is None:
        
        # Special handling for SQLite
        if settings.database_url.startswith("sqlite"):
            _engine = create_engine(
                settings.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False
            )
        else:
            _engine = create_engine(
                settings.database_url,
                echo=False,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
        
        logger.info(f"Database engine created: {settings.database_url.split('://')[0]}")
    
    return _engine


def get_session_factory():
    """
    Get or create the session factory.
    
    Returns:
        sessionmaker: Session factory
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        logger.info("Session factory created")
    
    return _SessionLocal


def get_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        Session: SQLAlchemy session
    """
    SessionLocal = get_session_factory()
    return SessionLocal()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    
    Yields:
        Session: Database session
    """
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def init_db(drop_all: bool = False) -> None:
    """
    Initialize the database.
    
    Creates all tables if they don't exist.
    
    Args:
        drop_all: If True, drop all tables before creating (DANGEROUS!)
    """
    engine = get_engine()
    
    if drop_all:
        logger.warning("Dropping all database tables!")
        Base.metadata.drop_all(bind=engine)
    
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def close_db() -> None:
    """Close database connections."""
    global _engine, _SessionLocal
    
    if _engine:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
        logger.info("Database connections closed")
