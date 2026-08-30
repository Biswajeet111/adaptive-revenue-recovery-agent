from decimal import Decimal

from backend.app.schemas.recovery_decision import (
    RecoveryDecision,
)


class DecisionSafetyGate:
    """
    Deterministic safety layer for AI recovery decisions.

    The AI may recommend an action, but this gate has
    final authority over whether automated recovery
    is permitted.
    """

    ALLOWED_ACTIONS = {
        "delayed_retry",
        "request_payment_method_update",
        "alternative_payment_method",
        "manual_review",
    }

    MAX_AUTOMATED_ATTEMPTS = 2

    MAX_AUTOMATED_AMOUNT = Decimal("10000")

    MIN_AUTOMATED_CONFIDENCE = 0.50

    def validate(
        self,
        *,
        decision: RecoveryDecision,
        transaction_amount: Decimal,
        previous_recovery_attempts: int,
        policy_evidence_count: int,
    ) -> RecoveryDecision:

        # =====================================================
        # 1. Policy evidence is mandatory
        # =====================================================

        if policy_evidence_count <= 0:

            raise ValueError(
                "AI decision rejected: "
                "no policy evidence."
            )

        # =====================================================
        # 2. Action must be explicitly supported
        # =====================================================

        if (
            decision.recommended_action
            not in self.ALLOWED_ACTIONS
        ):

            raise ValueError(
                "AI decision rejected: "
                "unsupported recovery action."
            )

        # =====================================================
        # 3. Low-confidence decisions cannot execute
        # =====================================================

        if (
            decision.confidence
            < self.MIN_AUTOMATED_CONFIDENCE
        ):

            original_reason = (
                decision.reason
            )

            decision.recommended_action = (
                "manual_review"
            )

            decision.reason = (
                "AI confidence was below the "
                "automated recovery threshold. "
                "Escalated to manual review. "
                "Original reasoning: "
                + original_reason
            )

        # =====================================================
        # 4. Recovery attempt limit
        # =====================================================

        if (
            previous_recovery_attempts
            >= self.MAX_AUTOMATED_ATTEMPTS
        ):

            decision.recommended_action = (
                "manual_review"
            )

            decision.reason = (
                "Transaction has reached the "
                "maximum automated recovery "
                "attempt limit of "
                f"{self.MAX_AUTOMATED_ATTEMPTS}. "
                "Escalated to manual review."
            )

        # =====================================================
        # 5. High-value transaction protection
        # =====================================================

        if (
            transaction_amount
            > self.MAX_AUTOMATED_AMOUNT
        ):

            decision.recommended_action = (
                "manual_review"
            )

            decision.reason = (
                "Transaction exceeds the automated "
                "recovery value threshold of "
                f"{self.MAX_AUTOMATED_AMOUNT}. "
                "Additional scrutiny is required."
            )

        return decision