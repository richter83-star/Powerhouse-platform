"""Drop raw refresh token column

Revision ID: drop_refresh_token_token
Revises: add_refresh_token_hash
Create Date: 2025-12-31 17:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "drop_refresh_token_token"
down_revision = "add_refresh_token_hash"
branch_labels = None
depends_on = None


def upgrade():
    """Remove raw refresh token storage."""
    op.execute("ALTER TABLE refresh_tokens DROP CONSTRAINT IF EXISTS refresh_tokens_token_key")
    op.execute("DROP INDEX IF EXISTS ix_refresh_tokens_token")
    op.execute("ALTER TABLE refresh_tokens DROP COLUMN IF EXISTS token")


def downgrade():
    """Re-add raw refresh token storage."""
    op.add_column("refresh_tokens", sa.Column("token", sa.String(length=500), nullable=True))
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"], unique=True)
