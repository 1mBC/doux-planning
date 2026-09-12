"""Job heartbeat_at and bench active unique key.

Revision ID: 20260912_0012
Revises: 20260908_0011
Create Date: 2026-09-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260912_0012"
down_revision: Union[str, Sequence[str], None] = "20260908_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("generate_jobs", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bench_jobs", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE generate_jobs SET heartbeat_at = now() WHERE status = 'running'")
    op.execute("UPDATE bench_jobs SET heartbeat_at = now() WHERE status = 'running'")
    op.create_index(
        "generate_jobs_running_heartbeat_idx",
        "generate_jobs",
        ["heartbeat_at"],
        postgresql_where=sa.text("status = 'running'"),
    )
    op.create_index(
        "bench_jobs_running_heartbeat_idx",
        "bench_jobs",
        ["heartbeat_at"],
        postgresql_where=sa.text("status = 'running'"),
    )
    op.create_index(
        "bench_jobs_active_uniq",
        "bench_jobs",
        ["category", "dataset_id", "search_effort"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )


def downgrade() -> None:
    op.drop_index("bench_jobs_active_uniq", table_name="bench_jobs")
    op.drop_index("bench_jobs_running_heartbeat_idx", table_name="bench_jobs")
    op.drop_index("generate_jobs_running_heartbeat_idx", table_name="generate_jobs")
    op.drop_column("bench_jobs", "heartbeat_at")
    op.drop_column("generate_jobs", "heartbeat_at")
