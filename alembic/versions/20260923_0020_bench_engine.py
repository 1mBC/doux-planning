"""Bench engine choice table.

Revision ID: 20260923_0020
Revises: 20260922_0019
Create Date: 2026-09-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260923_0020"
down_revision: Union[str, Sequence[str], None] = "20260922_0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bench_engine",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engine_ref", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("bench_engine")
