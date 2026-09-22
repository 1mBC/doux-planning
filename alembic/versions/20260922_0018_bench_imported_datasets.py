"""Alembic: bench_imported_datasets for restaurant → bench import.

Revision ID: 20260922_0018
Revises: 20260922_0017
Create Date: 2026-09-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260922_0018"
down_revision: Union[str, Sequence[str], None] = "20260922_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bench_imported_datasets",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("challenge_fr", sa.String(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("origin", sa.String(), nullable=False),
        sa.Column("source_restaurant_id", sa.String(), nullable=True),
        sa.Column("context", JSONB(), nullable=False),
        sa.Column("expected", JSONB(), nullable=False),
        sa.Column("manual_score_override", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("bench_imported_datasets")
