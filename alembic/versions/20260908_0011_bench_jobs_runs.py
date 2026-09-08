"""Admin bench_jobs and bench_runs tables.

Revision ID: 20260908_0011
Revises: 20260906_0010
Create Date: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260908_0011"
down_revision: Union[str, Sequence[str], None] = "20260906_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bench_jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("dataset_id", sa.String(), nullable=False),
        sa.Column("search_effort", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("run_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "bench_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("app_version", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("dataset_id", sa.String(), nullable=False),
        sa.Column("search_effort", sa.String(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("score", JSONB(), nullable=False),
        sa.Column("expected_score", JSONB(), nullable=False),
        sa.Column("deltas", JSONB(), nullable=False),
        sa.Column("assignments", JSONB(), nullable=False),
        sa.Column("warnings", JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("bench_runs")
    op.drop_table("bench_jobs")
