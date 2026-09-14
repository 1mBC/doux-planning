"""Bench trace, engine_ref, batch_id, started_at, 4-key unique.

Revision ID: 20260914_0013
Revises: 20260912_0012
Create Date: 2026-09-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260914_0013"
down_revision: Union[str, Sequence[str], None] = "20260912_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("bench_runs", sa.Column("trace", JSONB(), nullable=True))
    op.add_column("bench_jobs", sa.Column("engine_ref", sa.String(), nullable=True))
    op.execute("UPDATE bench_jobs SET engine_ref = 'core-3' WHERE engine_ref IS NULL")
    op.alter_column("bench_jobs", "engine_ref", existing_type=sa.String(), nullable=False)
    op.add_column("bench_jobs", sa.Column("batch_id", sa.String(), nullable=True))
    op.add_column("bench_jobs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_index("bench_jobs_active_uniq", table_name="bench_jobs")
    op.create_index(
        "bench_jobs_active_uniq",
        "bench_jobs",
        ["category", "dataset_id", "search_effort", "engine_ref"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )


def downgrade() -> None:
    op.drop_index("bench_jobs_active_uniq", table_name="bench_jobs")
    op.create_index(
        "bench_jobs_active_uniq",
        "bench_jobs",
        ["category", "dataset_id", "search_effort"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )
    op.drop_column("bench_jobs", "started_at")
    op.drop_column("bench_jobs", "batch_id")
    op.drop_column("bench_jobs", "engine_ref")
    op.drop_column("bench_runs", "trace")
