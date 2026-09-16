"""Live engine ref table and generate_logs.engine_ref column.

Revision ID: 20260916_0014
Revises: 20260914_0013
Create Date: 2026-09-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260916_0014"
down_revision: Union[str, Sequence[str], None] = "20260914_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "live_engine",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engine_ref", sa.String(), nullable=True),
    )
    op.add_column("generate_logs", sa.Column("engine_ref", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("generate_logs", "engine_ref")
    op.drop_table("live_engine")
