"""staff_fiches.min_shift_hours Float → JSONB per service.

Revision ID: 20260921_0016
Revises: 20260921_0015
Create Date: 2026-09-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260921_0016"
down_revision: Union[str, Sequence[str], None] = "20260921_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "staff_fiches",
        "min_shift_hours",
        existing_type=sa.Float(),
        type_=JSONB(),
        existing_nullable=False,
        existing_server_default=sa.text("4"),
        server_default=sa.text("'{}'::jsonb"),
        postgresql_using=(
            "CASE WHEN min_shift_hours = 4 THEN '{}'::jsonb "
            "ELSE jsonb_build_object("
            "'morning', min_shift_hours, "
            "'midday', min_shift_hours, "
            "'evening', min_shift_hours) END"
        ),
    )


def downgrade() -> None:
    op.alter_column(
        "staff_fiches",
        "min_shift_hours",
        existing_type=JSONB(),
        type_=sa.Float(),
        existing_nullable=False,
        existing_server_default=sa.text("'{}'::jsonb"),
        server_default=sa.text("4"),
        postgresql_using=(
            "CASE WHEN min_shift_hours = '{}'::jsonb THEN 4 "
            "ELSE COALESCE("
            "(min_shift_hours->>'morning')::double precision, "
            "(min_shift_hours->>'midday')::double precision, "
            "(min_shift_hours->>'evening')::double precision, "
            "4) END"
        ),
    )
