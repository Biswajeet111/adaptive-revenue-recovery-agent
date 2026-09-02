"""add recovery action lease index

Revision ID: c8d9e0f1a2b3
Revises: b7c1a2d3e4f5
Create Date: 2026-09-02
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, None] = "b7c1a2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_recovery_actions_lease_until",
        "recovery_actions",
        ["lease_until"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recovery_actions_lease_until",
        table_name="recovery_actions",
    )