from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class Communication(Base):
    __tablename__ = "communications"

    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="communications_idempotency_key_key",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    recovery_case_id: Mapped[int] = mapped_column(
        ForeignKey("recovery_cases.id"),
        nullable=False,
        index=True,
    )

    recovery_action_id: Mapped[int] = mapped_column(
        ForeignKey("recovery_actions.id"),
        nullable=False,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    template_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    template_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0",
    )

    recipient: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    subject: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    provider_message_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )