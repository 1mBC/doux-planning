"""generate_logs restaurant_id + score_global and impersonate_tokens.

Revision ID: 20260922_0017
Revises: 20260921_0016
Create Date: 2026-09-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260922_0017"
down_revision: Union[str, Sequence[str], None] = "20260921_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("generate_logs", sa.Column("restaurant_id", sa.String(), nullable=True))
    op.add_column("generate_logs", sa.Column("score_global", sa.Float(), nullable=True))
    op.execute(
        """
        UPDATE generate_logs AS g
        SET restaurant_id = a.restaurant_id
        FROM restaurateur_accounts AS a
        WHERE lower(a.email) = lower(g.email)
        """
    )
    op.create_table(
        "impersonate_tokens",
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("account_id", sa.String(), nullable=False),
        sa.Column("restaurant_id", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("token_hash"),
    )


def downgrade() -> None:
    op.drop_table("impersonate_tokens")
    op.drop_column("generate_logs", "score_global")
    op.drop_column("generate_logs", "restaurant_id")
