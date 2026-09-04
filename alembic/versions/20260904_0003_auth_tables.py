"""Auth tables: companies, fiches, accounts, hashed sessions.

Revision ID: 20260904_0003
Revises: 20260904_0002
Create Date: 2026-09-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260904_0003"
down_revision: Union[str, Sequence[str], None] = "20260904_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("invite_code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("linked_employee_ids", JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invite_code"),
    )
    op.create_table(
        "staff_fiches",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("team", sa.String(), nullable=False),
        sa.Column("invite_token", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invite_token"),
    )
    op.create_table(
        "account_emails",
        sa.Column("email", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("email"),
    )
    op.create_table(
        "restaurateur_accounts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("restaurant_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["email"], ["account_emails.email"]),
        sa.ForeignKeyConstraint(["restaurant_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("restaurant_id"),
    )
    op.create_table(
        "employee_accounts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("restaurant_id", sa.String(), nullable=False),
        sa.Column("employee_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["email"], ["account_emails.email"]),
        sa.ForeignKeyConstraint(["restaurant_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["staff_fiches.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("employee_id"),
    )
    op.create_table(
        "sessions",
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("account_id", sa.String(), nullable=False),
        sa.Column("restaurant_id", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("token_hash"),
    )


def downgrade() -> None:
    op.drop_table("sessions")
    op.drop_table("employee_accounts")
    op.drop_table("restaurateur_accounts")
    op.drop_table("account_emails")
    op.drop_table("staff_fiches")
    op.drop_table("companies")
