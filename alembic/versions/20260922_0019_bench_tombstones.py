"""Alembic: bench_tombstones for catalogue dataset delete.

Revision ID: 20260922_0019
Revises: 20260922_0018
Create Date: 2026-09-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260922_0019"
down_revision: Union[str, Sequence[str], None] = "20260922_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bench_tombstones",
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("dataset_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("category", "dataset_id"),
    )


def downgrade() -> None:
    op.drop_table("bench_tombstones")
