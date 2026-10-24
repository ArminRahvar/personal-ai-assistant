"""Add reminder delivery claim and retry state

Revision ID: 19b7c2a8d604
Revises: 440a0a170e88
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "19b7c2a8d604"
down_revision: Union[str, Sequence[str], None] = "440a0a170e88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_reminders_delivery_due",
        "reminders",
        ["is_sent", "scheduled_at"],
    )
    op.add_column(
        "reminders",
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "reminders",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "reminders",
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reminders", "next_attempt_at")
    op.drop_column("reminders", "attempt_count")
    op.drop_column("reminders", "claimed_at")
    op.drop_index("ix_reminders_delivery_due", table_name="reminders")
