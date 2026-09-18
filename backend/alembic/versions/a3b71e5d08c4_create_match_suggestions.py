"""create match suggestions

Revision ID: a3b71e5d08c4
Revises: f92a6c04b871
Create Date: 2026-09-18 03:55:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3b71e5d08c4"
down_revision: str | Sequence[str] | None = "f92a6c04b871"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "match_suggestions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("state", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["charge_requests.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id", "transaction_id"),
    )
    op.create_index(
        op.f("ix_match_suggestions_user_id"), "match_suggestions", ["user_id"]
    )
    op.create_index(
        op.f("ix_match_suggestions_request_id"), "match_suggestions", ["request_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("match_suggestions")
