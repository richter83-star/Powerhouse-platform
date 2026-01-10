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
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def _is_integer(table: str, column: str) -> bool:
        cols = {col["name"]: col["type"] for col in inspector.get_columns(table)}
        return isinstance(cols.get(column), sa.Integer)

    if _is_integer("sellers", "user_id"):
        op.alter_column(
            "sellers",
            "user_id",
            existing_type=sa.Integer(),
            type_=sa.String(length=36),
            nullable=False
        )
    if _is_integer("marketplace_purchases", "buyer_id"):
        op.alter_column(
            "marketplace_purchases",
            "buyer_id",
            existing_type=sa.Integer(),
            type_=sa.String(length=36),
            nullable=False
        )
    if _is_integer("marketplace_reviews", "buyer_id"):
        op.alter_column(
            "marketplace_reviews",
            "buyer_id",
            existing_type=sa.Integer(),
            type_=sa.String(length=36),
            nullable=False
        )


def downgrade():
    """Revert marketplace user ID columns to integers."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def _is_string(table: str, column: str) -> bool:
        cols = {col["name"]: col["type"] for col in inspector.get_columns(table)}
        return isinstance(cols.get(column), sa.String)

    if _is_string("marketplace_reviews", "buyer_id"):
        op.alter_column(
            "marketplace_reviews",
            "buyer_id",
            existing_type=sa.String(length=36),
            type_=sa.Integer(),
            nullable=False
        )
    if _is_string("marketplace_purchases", "buyer_id"):
        op.alter_column(
            "marketplace_purchases",
            "buyer_id",
            existing_type=sa.String(length=36),
            type_=sa.Integer(),
            nullable=False
        )
    if _is_string("sellers", "user_id"):
        op.alter_column(
            "sellers",
            "user_id",
            existing_type=sa.String(length=36),
            type_=sa.Integer(),
            nullable=False
        )
