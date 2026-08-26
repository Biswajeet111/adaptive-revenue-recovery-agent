from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"),
        nullable=False,
        index=True,
    )

    classification: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    recoverability: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    revenue_at_risk: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    recommended_action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="open",
        index=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
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