"""
Database query helpers with automatic tenant filtering.
"""
from typing import TypeVar, Type, Optional, List
from sqlalchemy.orm import Query, Session
from sqlalchemy import and_

from core.security.tenant_filter import TenantFilter
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


def query_with_tenant(
    db: Session,
    model_class: Type[T],
    tenant_id: str,
    **filters
) -> Query:
    """
    Create a query filtered by tenant_id.
    
    Args:
        db: Database session
        model_class: SQLAlchemy model class
        tenant_id: Tenant ID to filter by
        **filters: Additional filter conditions (e.g., status='active')
        
    Returns:
        Filtered query
        
    Example:
        # Get all runs for a tenant
        runs = query_with_tenant(db, Run, tenant_id).all()
        
        # Get active runs for a tenant
        active_runs = query_with_tenant(
            db, Run, tenant_id, 
            status=RunStatus.COMPLETED
        ).all()
    """
    if not tenant_id:
        raise ValueError("tenant_id is required")
    
    query = db.query(model_class)
    
    # Apply tenant filter
    query = TenantFilter.filter_by_tenant(query, tenant_id, model_class)
    
    # Apply additional filters
    for key, value in filters.items():
        if hasattr(model_class, key):
            query = query.filter(getattr(model_class, key) == value)
        else:
            logger.warning(f"Model {model_class.__name__} does not have attribute {key}")
    
    return query


def get_by_id_with_tenant(
    db: Session,
    model_class: Type[T],
    record_id: str,
    tenant_id: str
) -> Optional[T]:
    """
    Get a record by ID, ensuring it belongs to the tenant.
    
    Args:
        db: Database session
        model_class: SQLAlchemy model class
        record_id: Record ID
        tenant_id: Tenant ID
        
    Returns:
        Model instance or None if not found or doesn't belong to tenant
        
    Example:
        run = get_by_id_with_tenant(db, Run, run_id, tenant_id)
        if not run:
            raise HTTPException(404, "Run not found")
    """
    if not tenant_id:
        raise ValueError("tenant_id is required")
    
    query = db.query(model_class).filter(model_class.id == record_id)
    query = TenantFilter.filter_by_tenant(query, tenant_id, model_class)
    
    return query.first()


def create_with_tenant(
    db: Session,
    model_instance: T,
    tenant_id: str
) -> T:
    """
    Create a model instance with tenant_id automatically set.
    
    Args:
        db: Database session
        model_instance: Model instance to create
        tenant_id: Tenant ID to set
        
    Returns:
        Created model instance
        
    Example:
        run = Run(id=uuid4(), project_id=project_id, ...)
        run = create_with_tenant(db, run, tenant_id)
    """
    if not tenant_id:
        raise ValueError("tenant_id is required")
    
    TenantFilter.add_tenant_to_model(model_instance, tenant_id)
    
    db.add(model_instance)
    db.commit()
    db.refresh(model_instance)
    
    return model_instance

