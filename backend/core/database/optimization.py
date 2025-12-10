"""
Database optimization utilities.

Includes index creation, connection pool monitoring, and query optimization.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import Index, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

from database.session import get_engine
from database.models import Base

logger = logging.getLogger(__name__)


def create_missing_indexes(engine: Optional[Engine] = None) -> List[str]:
    """
    Create missing indexes for common query patterns.
    
    Args:
        engine: Database engine (uses default if None)
        
    Returns:
        List of created index names
    """
    if engine is None:
        engine = get_engine()
    
    created_indexes = []
    inspector = inspect(engine)
    
    # Get existing indexes
    existing_indexes = {}
    for table_name in inspector.get_table_names():
        indexes = inspector.get_indexes(table_name)
        existing_indexes[table_name] = {idx['name'] for idx in indexes}
    
    # Define required indexes by table
    required_indexes = {
        'runs': [
            ('idx_runs_tenant_status', ['tenant_id', 'status']),
            ('idx_runs_tenant_created', ['tenant_id', 'created_at']),
            ('idx_runs_status_created', ['status', 'created_at']),
            ('idx_runs_project_id', ['project_id']),
        ],
        'agent_runs': [
            ('idx_agent_runs_run_id', ['run_id']),
            ('idx_agent_runs_tenant_agent', ['tenant_id', 'agent_name']),
            ('idx_agent_runs_status', ['status']),
            ('idx_agent_runs_created', ['created_at']),
        ],
        'messages': [
            ('idx_messages_run_id', ['run_id']),
            ('idx_messages_tenant', ['tenant_id']),
            ('idx_messages_created', ['created_at']),
        ],
        'users': [
            ('idx_users_email', ['email']),
            ('idx_users_created', ['created_at']),
            ('idx_users_is_active', ['is_active']),
        ],
        'refresh_tokens': [
            ('idx_refresh_tokens_user', ['user_id']),
            ('idx_refresh_tokens_expires', ['expires_at']),
            ('idx_refresh_tokens_is_revoked', ['is_revoked']),
            ('idx_refresh_tokens_token_hash', ['token_hash']),
        ],
        'marketplace_listings': [
            ('idx_marketplace_listings_category_status', ['category', 'status']),
            ('idx_marketplace_listings_price', ['price']),
            ('idx_marketplace_listings_rating', ['rating']),
            ('idx_marketplace_listings_created', ['created_at']),
        ],
        'marketplace_purchases': [
            ('idx_marketplace_purchases_listing_id', ['listing_id']),
            ('idx_marketplace_purchases_status', ['status']),
            ('idx_marketplace_purchases_created', ['created_at']),
        ],
        'sellers': [
            ('idx_sellers_user_id', ['user_id']),
            ('idx_sellers_display_name', ['display_name']),
        ],
    }
    
    # Create missing indexes
    with engine.connect() as conn:
        for table_name, indexes in required_indexes.items():
            if table_name not in inspector.get_table_names():
                logger.warning(f"Table {table_name} does not exist, skipping indexes")
                continue
            
            for index_name, columns in indexes:
                if index_name in existing_indexes.get(table_name, set()):
                    logger.debug(f"Index {index_name} already exists on {table_name}")
                    continue
                
                try:
                    # Create index using raw SQL
                    columns_str = ', '.join(columns)
                    create_index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns_str})"
                    conn.execute(text(create_index_sql))
                    conn.commit()
                    created_indexes.append(index_name)
                    logger.info(f"Created index: {index_name} on {table_name}({columns_str})")
                except Exception as e:
                    logger.error(f"Failed to create index {index_name}: {e}")
    
    return created_indexes


def get_connection_pool_stats(engine: Optional[Engine] = None) -> Dict[str, Any]:
    """
    Get connection pool statistics.
    
    Args:
        engine: Database engine (uses default if None)
        
    Returns:
        Dict with pool statistics
    """
    if engine is None:
        engine = get_engine()
    
    pool: Pool = engine.pool
    
    stats = {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid(),
    }
    
    # Calculate utilization
    total_connections = stats["checked_in"] + stats["checked_out"]
    if pool.size() > 0:
        stats["utilization_percent"] = (stats["checked_out"] / pool.size()) * 100
    else:
        stats["utilization_percent"] = 0.0
    
    # Add pool configuration
    stats["pool_config"] = {
        "pool_size": getattr(pool, '_pool_size', None),
        "max_overflow": getattr(pool, '_max_overflow', None),
        "pool_timeout": getattr(pool, '_timeout', None),
        "pool_recycle": getattr(pool, '_recycle', None),
    }
    
    return stats


def check_connection_leaks(engine: Optional[Engine] = None, threshold: int = 10) -> Dict[str, Any]:
    """
    Check for potential connection leaks.
    
    Args:
        engine: Database engine (uses default if None)
        threshold: Threshold for considering it a potential leak
        
    Returns:
        Dict with leak detection results
    """
    stats = get_connection_pool_stats(engine)
    
    checked_out = stats["checked_out"]
    pool_size = stats["size"]
    
    leak_detected = checked_out > threshold or (pool_size > 0 and checked_out > pool_size * 0.8)
    
    result = {
        "leak_detected": leak_detected,
        "checked_out_connections": checked_out,
        "pool_size": pool_size,
        "threshold": threshold,
        "stats": stats
    }
    
    if leak_detected:
        logger.warning(
            f"Potential connection leak detected: {checked_out} connections checked out "
            f"(pool size: {pool_size}, threshold: {threshold})"
        )
    
    return result


def analyze_table_statistics(engine: Optional[Engine] = None) -> Dict[str, Any]:
    """
    Analyze table statistics for optimization opportunities.
    
    Args:
        engine: Database engine (uses default if None)
        
    Returns:
        Dict with table statistics
    """
    if engine is None:
        engine = get_engine()
    
    inspector = inspect(engine)
    statistics = {}
    
    with engine.connect() as conn:
        for table_name in inspector.get_table_names():
            try:
                # Get row count (PostgreSQL)
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()
                
                # Get table size (PostgreSQL)
                result = conn.execute(
                    text(f"SELECT pg_total_relation_size('{table_name}')")
                )
                table_size_bytes = result.scalar() or 0
                
                # Get indexes
                indexes = inspector.get_indexes(table_name)
                
                statistics[table_name] = {
                    "row_count": row_count,
                    "size_bytes": table_size_bytes,
                    "size_mb": round(table_size_bytes / (1024 * 1024), 2),
                    "index_count": len(indexes),
                    "indexes": [idx['name'] for idx in indexes]
                }
            except Exception as e:
                logger.warning(f"Failed to get statistics for {table_name}: {e}")
                statistics[table_name] = {"error": str(e)}
    
    return statistics


def optimize_database() -> Dict[str, Any]:
    """
    Run complete database optimization.
    
    Returns:
        Dict with optimization results
    """
    engine = get_engine()
    
    results = {
        "indexes_created": [],
        "pool_stats": {},
        "leak_check": {},
        "table_stats": {},
        "optimizations_applied": []
    }
    
    try:
        # Create missing indexes
        logger.info("Creating missing indexes...")
        created_indexes = create_missing_indexes(engine)
        results["indexes_created"] = created_indexes
        
        # Get connection pool stats
        logger.info("Analyzing connection pool...")
        results["pool_stats"] = get_connection_pool_stats(engine)
        
        # Check for connection leaks
        logger.info("Checking for connection leaks...")
        results["leak_check"] = check_connection_leaks(engine)
        
        # Analyze table statistics
        logger.info("Analyzing table statistics...")
        results["table_stats"] = analyze_table_statistics(engine)
        
        results["optimizations_applied"] = [
            f"Created {len(created_indexes)} indexes",
            "Analyzed connection pool",
            "Checked for connection leaks",
            "Analyzed table statistics"
        ]
        
        logger.info("Database optimization complete")
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}", exc_info=True)
        results["error"] = str(e)
    
    return results

