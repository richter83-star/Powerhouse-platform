"""Base schema

Revision ID: base_schema
Revises:
Create Date: 2026-01-01 03:00:00.000000

"""
from alembic import op

from database.models import Base


# revision identifiers, used by Alembic.
revision = "base_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create all tables from the SQLAlchemy models."""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade():
    """Drop all tables created by the base schema."""
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
