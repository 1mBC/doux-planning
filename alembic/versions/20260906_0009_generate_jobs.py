"""Maximal generate_jobs table.

Revision ID: 20260906_0009
Revises: 20260906_0008
Create Date: 2026-09-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260906_0009"
down_revision: Union[str, Sequence[str], None] = "20260906_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generate_jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("restaurant_id", sa.String(), nullable=False),
        sa.Column("team", sa.String(), nullable=False),
        sa.Column("search_effort", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("estimated_seconds", sa.Integer(), nullable=False),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["restaurant_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "generate_jobs_active_team",
        "generate_jobs",
        ["restaurant_id", "team"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )


def downgrade() -> None:
    op.drop_index("generate_jobs_active_team", table_name="generate_jobs")
    op.drop_table("generate_jobs")
