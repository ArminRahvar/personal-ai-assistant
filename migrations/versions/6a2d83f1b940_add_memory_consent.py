"""Add explicit opt-in for automatic memory use

Revision ID: 6a2d83f1b940
Revises: 19b7c2a8d604
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6a2d83f1b940"
down_revision: Union[str, Sequence[str], None] = "19b7c2a8d604"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "memory_enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "memory_enabled")
