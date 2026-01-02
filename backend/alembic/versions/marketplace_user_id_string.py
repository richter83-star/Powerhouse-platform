"""Change marketplace user IDs to strings

Revision ID: marketplace_user_id_string
Revises: drop_refresh_token_token
Create Date: 2026-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "marketplace_user_id_string"
down_revision = "drop_refresh_token_token"
branch_labels = None
depends_on = None


def upgrade():
    """Update marketplace user ID columns to string UUIDs."""
    op.alter_column(
        "sellers",
        "user_id",
        existing_type=sa.Integer(),
        type_=sa.String(length=36),
        nullable=False
    )
    op.alter_column(
        "marketplace_purchases",
        "buyer_id",
        existing_type=sa.Integer(),
        type_=sa.String(length=36),
        nullable=False
    )
    op.alter_column(
        "marketplace_reviews",
        "buyer_id",
        existing_type=sa.Integer(),
        type_=sa.String(length=36),
        nullable=False
    )


def downgrade():
    """Revert marketplace user ID columns to integers."""
    op.alter_column(
        "marketplace_reviews",
        "buyer_id",
        existing_type=sa.String(length=36),
        type_=sa.Integer(),
        nullable=False
    )
    op.alter_column(
        "marketplace_purchases",
        "buyer_id",
        existing_type=sa.String(length=36),
        type_=sa.Integer(),
        nullable=False
    )
    op.alter_column(
        "sellers",
        "user_id",
        existing_type=sa.String(length=36),
        type_=sa.Integer(),
        nullable=False
    )
