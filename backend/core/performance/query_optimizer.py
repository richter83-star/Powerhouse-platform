"""
Database query optimization utilities.
"""
import logging
from typing import List, Optional, TypeVar, Type
from sqlalchemy.orm import Session, Query, joinedload, selectinload
from sqlalchemy import Index

from database.models import Base

logger = logging.getLogger(__name__)

T = TypeVar('T')


class QueryOptimizer:
    """
    Utilities for optimizing database queries.
    
    Features:
    - Eager loading to prevent N+1 queries
    - Query result pagination
    - Selective field loading
    - Query result batching
    """
    
    @staticmethod
    def eager_load_relationships(
        query: Query,
        relationships: List[str]
    ) -> Query:
        """
        Add eager loading for relationships to prevent N+1 queries.
        
        Args:
            query: SQLAlchemy query
            relationships: List of relationship names to eager load
        
        Returns:
            Optimized query with eager loading
        
        Example:
            query = db.query(User)
            query = QueryOptimizer.eager_load_relationships(
                query, ['refresh_tokens', 'user_tenants']
            )
        """
        for rel in relationships:
            try:
                query = query.options(joinedload(rel))
            except Exception as e:
                logger.warning(f"Could not eager load relationship {rel}: {e}")
        return query
    
    @staticmethod
    def paginate_query(
        query: Query,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ) -> tuple[List, dict]:
        """
        Paginate query results.
        
        Args:
            query: SQLAlchemy query
            page: Page number (1-indexed)
            page_size: Number of items per page
            max_page_size: Maximum allowed page size
        
        Returns:
            Tuple of (items, pagination_info)
            pagination_info contains: total, page, page_size, total_pages
        """
        # Clamp page_size
        page_size = min(page_size, max_page_size)
        page = max(1, page)
        
        # Get total count
        total = query.count()
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get paginated results
        items = query.offset(offset).limit(page_size).all()
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        pagination_info = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return items, pagination_info
    
    @staticmethod
    def batch_query(
        query: Query,
        batch_size: int = 1000
    ):
        """
        Execute query in batches to avoid loading all results into memory.
        
        Args:
            query: SQLAlchemy query
            batch_size: Number of items per batch
        
        Yields:
            Batches of results
        
        Example:
            for batch in QueryOptimizer.batch_query(query, batch_size=500):
                process_batch(batch)
        """
        offset = 0
        while True:
            batch = query.offset(offset).limit(batch_size).all()
            if not batch:
                break
            yield batch
            offset += batch_size
            if len(batch) < batch_size:
                break


def create_indexes():
    """
    Create database indexes for common query patterns.
    
    This should be called during database initialization.
    """
    # Indexes are typically created via Alembic migrations,
    # but this function can be used to ensure they exist.
    
    indexes = [
        # User indexes
        Index('idx_users_email', 'users.email'),
        Index('idx_users_tenant', 'users.tenant_id'),  # If users have tenant_id
        
        # Run indexes
        Index('idx_runs_tenant_status', 'runs.tenant_id', 'runs.status'),
        Index('idx_runs_created', 'runs.created_at'),
        
        # AgentRun indexes
        Index('idx_agent_runs_run_id', 'agent_runs.run_id'),
        Index('idx_agent_runs_tenant', 'agent_runs.tenant_id'),
        
        # Message indexes
        Index('idx_messages_run_id', 'messages.run_id'),
        Index('idx_messages_tenant', 'messages.tenant_id'),
        
        # UserTenant indexes
        Index('idx_user_tenants_user', 'user_tenants.user_id'),
        Index('idx_user_tenants_tenant', 'user_tenants.tenant_id'),
    ]
    
    return indexes

