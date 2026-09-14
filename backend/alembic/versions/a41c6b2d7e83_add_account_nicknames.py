"""add account nicknames

Revision ID: a41c6b2d7e83
Revises: f63da1065cde
Create Date: 2026-09-14 09:41:02.117433

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a41c6b2d7e83"
down_revision: str | Sequence[str] | None = "f63da1065cde"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "akahu_account_settings",
        sa.Column(
            "nickname", sqlmodel.sql.sqltypes.AutoString(length=40), nullable=True
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("akahu_account_settings", "nickname")
