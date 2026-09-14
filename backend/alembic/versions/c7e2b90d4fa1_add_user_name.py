"""add user name

Revision ID: c7e2b90d4fa1
Revises: a41c6b2d7e83
Create Date: 2026-09-14 20:44:11.902845

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7e2b90d4fa1"
down_revision: str | Sequence[str] | None = "a41c6b2d7e83"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=60), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "name")
