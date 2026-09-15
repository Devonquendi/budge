"""create bills and charge requests

Revision ID: d81f4c0a92b7
Revises: c7e2b90d4fa1
Create Date: 2026-09-15 10:04:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d81f4c0a92b7"
down_revision: str | Sequence[str] | None = "c7e2b90d4fa1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "bills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column(
            "source_transaction_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bills_creator_id"), "bills", ["creator_id"])

    op.create_table(
        "charge_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column("token", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("payee_email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "payee_name", sqlmodel.sql.sqltypes.AutoString(length=60), nullable=True
        ),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bill_id"], ["bills.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_charge_requests_token"), "charge_requests", ["token"], unique=True
    )
    op.create_index(op.f("ix_charge_requests_bill_id"), "charge_requests", ["bill_id"])
    op.create_index(
        op.f("ix_charge_requests_payee_email"), "charge_requests", ["payee_email"]
    )

    op.create_table(
        "request_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("actor", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("note", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["charge_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_request_events_request_id"), "request_events", ["request_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("request_events")
    op.drop_table("charge_requests")
    op.drop_table("bills")
