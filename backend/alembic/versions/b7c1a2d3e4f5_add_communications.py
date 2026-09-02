"""add communications table

Revision ID: b7c1a2d3e4f5
Revises: a80425f69fb4
Create Date: 2026-09-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c1a2d3e4f5"
down_revision: Union[str, None] = "a80425f69fb4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "communications",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "recovery_case_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "recovery_action_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "template_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "template_version",
            sa.String(length=50),
            nullable=False,
            server_default="1.0",
        ),
        sa.Column(
            "recipient",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "subject",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "provider",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "provider_message_id",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "idempotency_key",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "delivered_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "failed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "failure_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "metadata_json",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recovery_case_id"],
            ["recovery_cases.id"],
        ),
        sa.ForeignKeyConstraint(
            ["recovery_action_id"],
            ["recovery_actions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "idempotency_key",
            name="communications_idempotency_key_key",
        ),
    )

    op.create_index(
        "ix_communications_recovery_case_id",
        "communications",
        ["recovery_case_id"],
    )

    op.create_index(
        "ix_communications_recovery_action_id",
        "communications",
        ["recovery_action_id"],
    )

    op.create_index(
        "ix_communications_channel",
        "communications",
        ["channel"],
    )

    op.create_index(
        "ix_communications_status",
        "communications",
        ["status"],
    )

    op.create_index(
        "ix_communications_provider_message_id",
        "communications",
        ["provider_message_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_communications_provider_message_id",
        table_name="communications",
    )
    op.drop_index(
        "ix_communications_status",
        table_name="communications",
    )
    op.drop_index(
        "ix_communications_channel",
        table_name="communications",
    )
    op.drop_index(
        "ix_communications_recovery_action_id",
        table_name="communications",
    )
    op.drop_index(
        "ix_communications_recovery_case_id",
        table_name="communications",
    )
    op.drop_table("communications")