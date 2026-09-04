"""Live company context: services, ladders, types, typical week, fiche contracts.

Revision ID: 20260904_0004
Revises: 20260904_0003
Create Date: 2026-09-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260904_0004"
down_revision: Union[str, Sequence[str], None] = "20260904_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("legal_context_id", sa.String(), nullable=False, server_default="france"),
    )
    op.add_column(
        "companies",
        sa.Column("services", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.add_column(
        "companies",
        sa.Column("ladders", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column(
        "companies",
        sa.Column("types", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.add_column(
        "companies",
        sa.Column("typical_week", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column(
        "staff_fiches",
        sa.Column("role_level", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "staff_fiches",
        sa.Column("contractual_hours_per_week", sa.Float(), nullable=False, server_default="35"),
    )
    op.add_column(
        "staff_fiches",
        sa.Column("min_shift_hours", sa.Float(), nullable=False, server_default="4"),
    )
    op.add_column(
        "staff_fiches",
        sa.Column("unavailabilities", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.add_column(
        "staff_fiches",
        sa.Column("wellbeing", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )


def downgrade() -> None:
    op.drop_column("staff_fiches", "wellbeing")
    op.drop_column("staff_fiches", "unavailabilities")
    op.drop_column("staff_fiches", "min_shift_hours")
    op.drop_column("staff_fiches", "contractual_hours_per_week")
    op.drop_column("staff_fiches", "role_level")
    op.drop_column("companies", "typical_week")
    op.drop_column("companies", "types")
    op.drop_column("companies", "ladders")
    op.drop_column("companies", "services")
    op.drop_column("companies", "legal_context_id")
