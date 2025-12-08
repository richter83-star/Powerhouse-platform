"""
Database connection pool optimization.
"""
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from config.settings import settings

logger = logging.getLogger(__name__)


def create_optimized_engine(database_url: Optional[str] = None):
    """
    Create optimized SQLAlchemy engine with connection pooling.
    
    Args:
        database_url: Database URL (uses settings if None)
    
    Returns:
        Optimized SQLAlchemy engine
    """
    if database_url is None:
        if settings.database_url:
            database_url = settings.database_url
        else:
            database_url = (
                f"postgresql://{settings.db_user}:{settings.db_password}"
                f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
            )
    
    # Connection pool configuration
    pool_config = {
        "poolclass": QueuePool,
        "pool_size": 10,  # Number of connections to maintain
        "max_overflow": 20,  # Additional connections beyond pool_size
        "pool_timeout": 30,  # Seconds to wait for connection
        "pool_recycle": 3600,  # Recycle connections after 1 hour
        "pool_pre_ping": True,  # Verify connections before using
        "echo": settings.debug,  # Log SQL queries in debug mode
    }
    
    engine = create_engine(
        database_url,
        **pool_config,
        connect_args={
            "connect_timeout": 10,
            "application_name": "powerhouse_backend"
        }
    )
    
    # Add connection pool event listeners
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Set SQLite pragmas for better performance (if using SQLite)."""
        if 'sqlite' in database_url:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
            cursor.close()
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Log connection checkout for monitoring."""
        logger.debug("Connection checked out from pool")
    
    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Log connection checkin for monitoring."""
        logger.debug("Connection returned to pool")
    
    logger.info(f"Created optimized database engine with pool_size=10, max_overflow=20")
    
    return engine

