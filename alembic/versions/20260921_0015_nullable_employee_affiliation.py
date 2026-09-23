"""Nullable employee affiliation after staff delete.

Revision ID: 20260921_0015
Revises: 20260916_0014
Create Date: 2026-09-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260921_0015"
down_revision: Union[str, Sequence[str], None] = "20260916_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "employee_accounts",
        "restaurant_id",
        existing_type=sa.String(),
        nullable=True,
    )
    op.alter_column(
        "employee_accounts",
        "employee_id",
        existing_type=sa.String(),
        nullable=True,
    )
    op.alter_column(
        "sessions",
        "restaurant_id",
        existing_type=sa.String(),
        nullable=True,
    )
    op.create_check_constraint(
        "employee_accounts_affiliation_nulls_check",
        "employee_accounts",
        "(restaurant_id IS NULL) = (employee_id IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("employee_accounts_affiliation_nulls_check", "employee_accounts", type_="check")
    op.alter_column(
        "sessions",
        "restaurant_id",
        existing_type=sa.String(),
        nullable=False,
    )
    op.alter_column(
        "employee_accounts",
        "employee_id",
        existing_type=sa.String(),
        nullable=False,
    )
    op.alter_column(
        "employee_accounts",
        "restaurant_id",
        existing_type=sa.String(),
        nullable=False,
    )
