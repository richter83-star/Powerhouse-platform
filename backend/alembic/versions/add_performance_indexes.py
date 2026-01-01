"""Add performance indexes

Revision ID: add_performance_indexes
Revises: 
Create Date: 2025-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = None  # Update this to match your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for common query patterns."""
    indexes = [
        ("idx_users_email", "users", "email"),
        ("idx_runs_tenant_status", "runs", "tenant_id, status"),
        ("idx_runs_created", "runs", "created_at"),
        ("idx_agent_runs_run_id", "agent_runs", "run_id"),
        ("idx_agent_runs_tenant", "agent_runs", "tenant_id"),
        ("idx_messages_run_id", "messages", "run_id"),
        ("idx_messages_tenant", "messages", "tenant_id"),
        ("idx_user_tenants_user", "user_tenants", "user_id"),
        ("idx_user_tenants_tenant", "user_tenants", "tenant_id"),
    ]

    for index_name, table_name, columns in indexes:
        op.execute(
            f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})"
        )


def downgrade():
    """Remove performance indexes."""
    op.drop_index('idx_user_tenants_tenant', table_name='user_tenants')
    op.drop_index('idx_user_tenants_user', table_name='user_tenants')
    op.drop_index('idx_messages_tenant', table_name='messages')
    op.drop_index('idx_messages_run_id', table_name='messages')
    op.drop_index('idx_agent_runs_tenant', table_name='agent_runs')
    op.drop_index('idx_agent_runs_run_id', table_name='agent_runs')
    op.drop_index('idx_runs_created', table_name='runs')
    op.drop_index('idx_runs_tenant_status', table_name='runs')
    op.drop_index('idx_users_email', table_name='users')

