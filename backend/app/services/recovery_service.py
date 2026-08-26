from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.recovery_policy import RecoveryPolicy


class RecoveryService:

    def __init__(self, db: Session):
        self.db = db
        self.policy = RecoveryPolicy()

    def create_case_for_transaction(
        self,
        transaction: Transaction,
    ) -> RecoveryCase:

        existing = self.db.scalar(
            select(RecoveryCase).where(
                RecoveryCase.transaction_id == transaction.id
            )
        )

        if existing:
            return existing

        decision = self.policy.evaluate(
            failure_code=transaction.failure_code,
            failure_reason=transaction.failure_reason,
            payment_method=transaction.payment_method,
            amount=transaction.amount,
        )

        recovery_case = RecoveryCase(
            transaction_id=transaction.id,
            classification=decision.classification,
            recoverability=decision.recoverability,
            risk_score=decision.risk_score,
            revenue_at_risk=Decimal(transaction.amount),
            recommended_action=decision.recommended_action,
            status="open",
            reason=decision.reason,
        )

        self.db.add(recovery_case)
        self.db.flush()

        action = RecoveryAction(
            recovery_case_id=recovery_case.id,
            action_type=decision.recommended_action,
            channel=self._channel_for_action(
                decision.recommended_action
            ),
            status="pending",
        )

        self.db.add(action)

        self.db.flush()

        return recovery_case

    @staticmethod
    def _channel_for_action(action_type: str) -> str:

        channels = {
            "delayed_retry": "payment",
            "request_payment_method_update": "payment",
            "alternative_payment_method": "payment",
            "manual_review": "support",
        }

        return channels.get(
            action_type,
            "support",
        )