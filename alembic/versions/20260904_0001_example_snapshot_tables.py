"""Example snapshot tables: legal_contexts, restaurants, example_snapshots.

Revision ID: 20260904_0001
Revises:
Create Date: 2026-09-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260904_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "legal_contexts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("document", JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "restaurants",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("legal_context", sa.String(), nullable=False),
        sa.Column("document", JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["legal_context"], ["legal_contexts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "example_snapshots",
        sa.Column("example_id", sa.String(), nullable=False),
        sa.Column("restaurant_id", sa.String(), nullable=False),
        sa.Column("restaurant", JSONB(), nullable=False),
        sa.Column("planning", JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"]),
        sa.PrimaryKeyConstraint("example_id"),
    )


def downgrade() -> None:
    op.drop_table("example_snapshots")
    op.drop_table("restaurants")
    op.drop_table("legal_contexts")
