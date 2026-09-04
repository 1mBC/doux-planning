"""Example snapshot tables: legal_contexts, restaurants, example_snapshots.

Revision ID: 20260904_0002
Revises: 20260904_0001
Create Date: 2026-09-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260904_0002"
down_revision: Union[str, Sequence[str], None] = "20260904_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sandbox_sessions",
        sa.Column("restaurant_id", sa.String(), nullable=False),
        sa.Column("document", JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("restaurant_id"),
    )


def downgrade() -> None:
    op.drop_table("sandbox_sessions")
