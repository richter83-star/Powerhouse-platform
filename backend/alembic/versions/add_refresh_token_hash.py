"""Add refresh token hash

Revision ID: add_refresh_token_hash
Revises: add_performance_indexes
Create Date: 2025-12-31 13:38:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_refresh_token_hash"
down_revision = "add_performance_indexes"
branch_labels = None
depends_on = None


def upgrade():
    """Add token_hash column to refresh_tokens."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("refresh_tokens")}
    if "token_hash" not in columns:
        op.add_column("refresh_tokens", sa.Column("token_hash", sa.String(length=128), nullable=True))
    indexes = {idx["name"] for idx in inspector.get_indexes("refresh_tokens")}
    if "idx_refresh_tokens_token_hash" not in indexes:
        op.create_index("idx_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=False)


def downgrade():
    """Remove token_hash column from refresh_tokens."""
    op.drop_index("idx_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "token_hash")
