"""add payout account

Revision ID: f92a6c04b871
Revises: e5c37a1b4d92
Create Date: 2026-09-18 03:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f92a6c04b871"
down_revision: str | Sequence[str] | None = "e5c37a1b4d92"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("payout_account", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "payout_name", sqlmodel.sql.sqltypes.AutoString(length=60), nullable=True
        ),
    )
    op.add_column(
        "users", sa.Column("payout_verified_at", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "payout_verified_at")
    op.drop_column("users", "payout_name")
    op.drop_column("users", "payout_account")
