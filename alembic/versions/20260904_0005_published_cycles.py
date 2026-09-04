"""Live company published cycles JSONB (salle / cuisine).

Revision ID: 20260904_0005
Revises: 20260904_0004
Create Date: 2026-09-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260904_0005"
down_revision: Union[str, Sequence[str], None] = "20260904_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column(
            "published_cycles",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{\"salle\": null, \"cuisine\": null}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("companies", "published_cycles")
