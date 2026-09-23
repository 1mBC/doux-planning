"""Admin is_admin flag and generate_logs.

Revision ID: 20260906_0008
Revises: 20260905_0007
Create Date: 2026-09-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260906_0008"
down_revision: Union[str, Sequence[str], None] = "20260905_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "restaurateur_accounts",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_table(
        "generate_logs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("restaurant_name", sa.String(), nullable=False),
        sa.Column("team", sa.String(), nullable=False),
        sa.Column("warnings", JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("generate_logs")
    op.drop_column("restaurateur_accounts", "is_admin")
