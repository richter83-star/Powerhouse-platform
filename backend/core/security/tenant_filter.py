"""
Tenant filtering utilities for database queries.
"""
from typing import TypeVar, Type, Optional
from sqlalchemy.orm import Query
from sqlalchemy import Column
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TenantFilter:
    """
    Utility class for filtering database queries by tenant_id.
    
    Ensures all queries automatically filter by tenant to prevent data leakage.
    """
    
    @staticmethod
    def filter_by_tenant(
        query: Query,
        tenant_id: str,
        model_class: Optional[Type] = None
    ) -> Query:
        """
        Filter query by tenant_id.
        
        Args:
            query: SQLAlchemy query object
            tenant_id: Tenant ID to filter by
            model_class: Model class (auto-detected from query if not provided)
            
        Returns:
            Filtered query
        """
        if not tenant_id:
            logger.warning("Empty tenant_id provided to filter_by_tenant")
            return query
        
        # Get model class from query if not provided
        if model_class is None:
            if hasattr(query, 'column_descriptions'):
                model_class = query.column_descriptions[0]['entity']
            elif hasattr(query, '_entity'):
                model_class = query._entity.class_
            else:
                logger.warning("Could not determine model class for tenant filtering")
                return query
        
        # Check if model has tenant_id column
        if hasattr(model_class, 'tenant_id'):
            return query.filter(model_class.tenant_id == tenant_id)
        else:
            # Model doesn't have tenant_id, log warning but don't fail
            logger.debug(f"Model {model_class.__name__} does not have tenant_id column")
            return query
    
    @staticmethod
    def ensure_tenant_isolation(
        query: Query,
        tenant_id: str,
        model_class: Optional[Type] = None
    ) -> Query:
        """
        Ensure query is filtered by tenant_id, raising error if tenant_id is missing.
        
        Args:
            query: SQLAlchemy query object
            tenant_id: Tenant ID (required)
            model_class: Model class
            
        Returns:
            Filtered query
            
        Raises:
            ValueError: If tenant_id is None or empty
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for tenant isolation")
        
        return TenantFilter.filter_by_tenant(query, tenant_id, model_class)
    
    @staticmethod
    def add_tenant_to_model(instance, tenant_id: str) -> None:
        """
        Add tenant_id to a model instance if it has the column.
        
        Args:
            instance: Model instance
            tenant_id: Tenant ID to set
        """
        if hasattr(instance, 'tenant_id'):
            instance.tenant_id = tenant_id
        else:
            logger.debug(f"Model {instance.__class__.__name__} does not have tenant_id attribute")


def get_tenant_id_from_request(request) -> Optional[str]:
    """
    Extract tenant_id from FastAPI request state.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Tenant ID or None
    """
    return getattr(request.state, 'tenant_id', None)


def require_tenant_id(request) -> str:
    """
    Require tenant_id from request, raising error if missing.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Tenant ID
        
    Raises:
        ValueError: If tenant_id is missing
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        raise ValueError("tenant_id is required but missing from request")
    return tenant_id

