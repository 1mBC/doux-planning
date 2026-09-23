"""Company hours JSONB and company-scoped staff fiche identity.

Revision ID: 20260905_0007
Revises: 20260904_0006
Create Date: 2026-09-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260905_0007"
down_revision: Union[str, Sequence[str], None] = "20260904_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("hours", JSONB(), nullable=True))
    op.drop_constraint("employee_accounts_employee_id_fkey", "employee_accounts", type_="foreignkey")
    op.drop_constraint("employee_accounts_employee_id_key", "employee_accounts", type_="unique")
    op.drop_constraint("staff_fiches_pkey", "staff_fiches", type_="primary")
    op.create_primary_key("staff_fiches_pkey", "staff_fiches", ["company_id", "id"])
    op.create_unique_constraint(
        "employee_accounts_restaurant_employee_key",
        "employee_accounts",
        ["restaurant_id", "employee_id"],
    )
    op.create_foreign_key(
        "employee_accounts_restaurant_employee_fkey",
        "employee_accounts",
        "staff_fiches",
        ["restaurant_id", "employee_id"],
        ["company_id", "id"],
    )


def downgrade() -> None:
    op.drop_constraint("employee_accounts_restaurant_employee_fkey", "employee_accounts", type_="foreignkey")
    op.drop_constraint("employee_accounts_restaurant_employee_key", "employee_accounts", type_="unique")
    op.drop_constraint("staff_fiches_pkey", "staff_fiches", type_="primary")
    op.create_primary_key("staff_fiches_pkey", "staff_fiches", ["id"])
    op.create_unique_constraint("employee_accounts_employee_id_key", "employee_accounts", ["employee_id"])
    op.create_foreign_key(
        "employee_accounts_employee_id_fkey",
        "employee_accounts",
        "staff_fiches",
        ["employee_id"],
        ["id"],
    )
    op.drop_column("companies", "hours")
