"""Nullable generate_logs search_effort and duration_seconds.

Revision ID: 20260906_0010
Revises: 20260906_0009
Create Date: 2026-09-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260906_0010"
down_revision: Union[str, Sequence[str], None] = "20260906_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("generate_logs", sa.Column("search_effort", sa.String(), nullable=True))
    op.add_column("generate_logs", sa.Column("duration_seconds", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("generate_logs", "duration_seconds")
    op.drop_column("generate_logs", "search_effort")
