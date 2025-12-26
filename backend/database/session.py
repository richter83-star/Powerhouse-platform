"""
Database session management and initialization.
"""

from typing import Generator, Optional
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Try to use optimized connection pool if available
try:
    from core.performance.connection_pool import create_optimized_engine
    USE_OPTIMIZED_POOL = True
except ImportError:
    USE_OPTIMIZED_POOL = False
    logger.warning("Optimized connection pool not available, using default")

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
        database_url = settings.database_url
        if os.getenv("PYTEST_CURRENT_TEST"):
            database_url = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

        # Special handling for SQLite
        if database_url and database_url.startswith("sqlite"):
            _engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False
            )
        elif USE_OPTIMIZED_POOL and not (database_url and database_url.startswith("sqlite")):
            # Use optimized connection pool for PostgreSQL
            _engine = create_optimized_engine()
        else:
            # Fallback to default configuration
            if not database_url:
                database_url = (
                    f"postgresql://{settings.db_user}:{settings.db_password}"
                    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
                )
            _engine = create_engine(
                database_url,
                echo=False,
                pool_pre_ping=True,
                pool_size=10,  # Increased from 5
                max_overflow=20  # Increased from 10
            )
        
        db_type = "unknown"
        if database_url:
            try:
                db_type = database_url.split('://')[0]
            except (AttributeError, IndexError):
                pass
        logger.info(f"Database engine created: {db_type}")
    
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


def set_tenant_context(db: Session, tenant_id: str) -> None:
    """
    Set tenant context for Row-Level Security (RLS).
    
    This sets the PostgreSQL session variable that RLS policies use
    to filter queries by tenant.
    
    Args:
        db: Database session
        tenant_id: Tenant ID to set
    """
    try:
        # Set the tenant context for RLS
        db.execute(text("SET LOCAL app.current_tenant_id = :tenant_id"), {"tenant_id": tenant_id})
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to set tenant context (RLS may not be enabled): {e}")


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
