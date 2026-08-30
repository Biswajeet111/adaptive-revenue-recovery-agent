from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.schemas.recovery_decision import RecoveryDecision
from backend.app.services.decision_safety_gate import (
    DecisionSafetyGate,
)
from backend.app.services.policy_retrieval_service import (
    PolicyEvidence,
    PolicyRetrievalService,
)


class AIRecoveryService:

    def __init__(
        self,
        db: Session,
        retrieval_service: PolicyRetrievalService,
        safety_gate: DecisionSafetyGate,
    ):
        self.db = db
        self.retrieval_service = retrieval_service
        self.safety_gate = safety_gate

    def build_context(
        self,
        *,
        transaction: Transaction,
        recovery_case: RecoveryCase,
    ) -> dict:

        previous_attempts = (
            self._previous_attempt_count(
                recovery_case.id
            )
        )

        return {
            "transaction_id": transaction.id,
            "amount": str(transaction.amount),
            "currency": transaction.currency,
            "razorpay_order_id": (
                transaction.razorpay_order_id
            ),
            "payment_method": (
                transaction.payment_method
            ),
            "status": transaction.status,
            "failure_code": (
                recovery_case.failure_code
            ),
            "failure_reason": (
                recovery_case.failure_reason
            ),
            "recovery_case_id": recovery_case.id,
            "classification": (
                recovery_case.classification
            ),
            "recoverability": (
                recovery_case.recoverability
            ),
            "previous_recovery_attempts": (
                previous_attempts
            ),
        }

    def retrieve_policy_evidence(
        self,
        *,
        transaction: Transaction,
        recovery_case: RecoveryCase,
        limit: int = 3,
    ) -> list[PolicyEvidence]:

        context = self.build_context(
            transaction=transaction,
            recovery_case=recovery_case,
        )

        query = self._build_policy_query(
            context
        )

        return self.retrieval_service.retrieve(
            query=query,
            limit=limit,
        )

    def validate_decision(
        self,
        *,
        decision: RecoveryDecision,
        transaction: Transaction,
        recovery_case: RecoveryCase,
        evidence: list[PolicyEvidence],
    ) -> RecoveryDecision:

        previous_attempts = (
            self._previous_attempt_count(
                recovery_case.id
            )
        )

        return self.safety_gate.validate(
            decision=decision,
            transaction_amount=Decimal(
                str(transaction.amount)
            ),
            previous_recovery_attempts=(
                previous_attempts
            ),
            policy_evidence_count=len(
                evidence
            ),
        )

    def _previous_attempt_count(
        self,
        recovery_case_id: int,
    ) -> int:

        statement = (
            select(
                func.count(RecoveryAction.id)
            )
            .where(
                RecoveryAction.recovery_case_id
                == recovery_case_id
            )
            .where(
                RecoveryAction.status.in_(
                    [
                        "executing",
                        "executed",
                        "successful",
                        "failed",
                    ]
                )
            )
        )

        return int(
            self.db.scalar(statement) or 0
        )


    @staticmethod
    def _build_policy_query(
        context: dict,
    ) -> str:

        return (
            "Determine the appropriate revenue "
            "recovery strategy for a failed payment. "
            f"Failure classification: "
            f"{context.get('classification')}. "
            f"Failure code: "
            f"{context.get('failure_code')}. "
            f"Failure reason: "
            f"{context.get('failure_reason')}. "
            f"Payment method: "
            f"{context.get('payment_method')}. "
            f"Transaction amount: "
            f"{context.get('amount')}. "
            f"Recoverability: "
            f"{context.get('recoverability')}. "
            f"Previous recovery attempts: "
            f"{context.get('previous_recovery_attempts')}."
        )