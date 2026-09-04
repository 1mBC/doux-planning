"""Live company sandbox drafts JSONB (salle / cuisine).

Revision ID: 20260904_0006
Revises: 20260904_0005
Create Date: 2026-09-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260904_0006"
down_revision: Union[str, Sequence[str], None] = "20260904_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column(
            "live_sandboxes",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{\"salle\": null, \"cuisine\": null}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("companies", "live_sandboxes")
