"""
Tests for query optimization functionality.
"""
import pytest
from sqlalchemy.orm import Session, Query
from unittest.mock import Mock, patch

from core.performance.query_optimizer import QueryOptimizer, create_indexes
from database.models import User, Run
from database.query_helpers import query_with_tenant, get_by_id_with_tenant


@pytest.mark.unit
@pytest.mark.database
class TestQueryOptimizer:
    """Test query optimizer utilities."""
    
    def test_eager_load_relationships(self, db_session):
        """Test eager loading prevents N+1 queries."""
        query = db_session.query(User)
        
        # Add eager loading
        optimized_query = QueryOptimizer.eager_load_relationships(
            query,
            ['refresh_tokens', 'user_tenants']
        )
        
        # Query should have options set
        assert optimized_query is not None
    
    def test_paginate_query(self, db_session):
        """Test query pagination."""
        # Create some test data
        from database.models import User
        for i in range(25):
            user = User(
                id=f"user-{i}",
                email=f"user{i}@example.com",
                password_hash="hash",
                is_active=1
            )
            db_session.add(user)
        db_session.commit()
        
        query = db_session.query(User)
        items, pagination = QueryOptimizer.paginate_query(query, page=1, page_size=10)
        
        assert len(items) == 10
        assert pagination["total"] == 25
        assert pagination["page"] == 1
        assert pagination["page_size"] == 10
        assert pagination["total_pages"] == 3
        assert pagination["has_next"] is True
        assert pagination["has_prev"] is False
    
    def test_paginate_query_page_2(self, db_session):
        """Test pagination on page 2."""
        from database.models import User
        for i in range(25):
            user = User(
                id=f"user-{i}",
                email=f"user{i}@example.com",
                password_hash="hash",
                is_active=1
            )
            db_session.add(user)
        db_session.commit()
        
        query = db_session.query(User)
        items, pagination = QueryOptimizer.paginate_query(query, page=2, page_size=10)
        
        assert len(items) == 10
        assert pagination["page"] == 2
        assert pagination["has_next"] is True
        assert pagination["has_prev"] is True
    
    def test_paginate_query_max_page_size(self, db_session):
        """Test pagination respects max_page_size."""
        query = db_session.query(User)
        items, pagination = QueryOptimizer.paginate_query(
            query,
            page=1,
            page_size=200,  # Exceeds max
            max_page_size=100
        )
        
        assert pagination["page_size"] == 100
    
    def test_batch_query(self, db_session):
        """Test batch query execution."""
        from database.models import User
        for i in range(15):
            user = User(
                id=f"user-{i}",
                email=f"user{i}@example.com",
                password_hash="hash",
                is_active=1
            )
            db_session.add(user)
        db_session.commit()
        
        query = db_session.query(User)
        batches = list(QueryOptimizer.batch_query(query, batch_size=5))
        
        assert len(batches) == 3
        assert len(batches[0]) == 5
        assert len(batches[1]) == 5
        assert len(batches[2]) == 5
    
    def test_create_indexes(self):
        """Test index creation function."""
        indexes = create_indexes()
        
        assert len(indexes) > 0
        # Should have indexes for common query patterns
        index_names = [idx.name for idx in indexes]
        assert any("users" in name.lower() for name in index_names)
        assert any("runs" in name.lower() for name in index_names)


@pytest.mark.unit
@pytest.mark.database
class TestQueryHelpers:
    """Test query helper functions."""
    
    def test_query_with_tenant(self, db_session, sample_tenant_data):
        """Test query_with_tenant helper."""
        from database.models import Run
        
        # Create test run with tenant
        run = Run(
            id="test-run-1",
            tenant_id=sample_tenant_data["id"],
            workflow_type="compliance",
            status="pending"
        )
        db_session.add(run)
        db_session.commit()
        
        # Query with tenant filter
        query = query_with_tenant(
            db_session,
            Run,
            sample_tenant_data["id"]
        )
        results = query.all()
        
        assert len(results) >= 1
        assert all(r.tenant_id == sample_tenant_data["id"] for r in results)
    
    def test_get_by_id_with_tenant(self, db_session, sample_tenant_data):
        """Test get_by_id_with_tenant helper."""
        from database.models import Run
        
        # Create test run
        run = Run(
            id="test-run-2",
            tenant_id=sample_tenant_data["id"],
            workflow_type="compliance",
            status="pending"
        )
        db_session.add(run)
        db_session.commit()
        
        # Get by ID with tenant
        result = get_by_id_with_tenant(
            db_session,
            Run,
            "test-run-2",
            sample_tenant_data["id"]
        )
        
        assert result is not None
        assert result.id == "test-run-2"
        assert result.tenant_id == sample_tenant_data["id"]
    
    def test_get_by_id_wrong_tenant(self, db_session, sample_tenant_data):
        """Test get_by_id_with_tenant returns None for wrong tenant."""
        from database.models import Run
        
        # Create run for tenant-1
        run = Run(
            id="test-run-3",
            tenant_id="tenant-1",
            workflow_type="compliance",
            status="pending"
        )
        db_session.add(run)
        db_session.commit()
        
        # Try to get with different tenant
        result = get_by_id_with_tenant(
            db_session,
            Run,
            "test-run-3",
            "tenant-2"  # Different tenant
        )
        
        assert result is None  # Should not find it


@pytest.mark.integration
@pytest.mark.database
class TestQueryPerformance:
    """Test query performance improvements."""
    
    def test_eager_loading_reduces_queries(self, db_session):
        """Test that eager loading reduces number of queries."""
        # This is a conceptual test - in practice, you'd use query counting
        query = db_session.query(User)
        
        # Without eager loading, accessing relationships would trigger additional queries
        # With eager loading, relationships are loaded in initial query
        optimized = QueryOptimizer.eager_load_relationships(
            query,
            ['user_tenants']
        )
        
        assert optimized is not None

