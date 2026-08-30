from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RecoveryDecision:
    classification: str
    recoverability: str
    risk_score: Decimal
    recommended_action: str
    reason: str


class RecoveryPolicy:
    """
    Deterministic first-line recovery policy.

    This layer intentionally does not use an LLM.
    It provides safe, explainable baseline decisions
    that the future AI agent can reason over.
    """

    def evaluate(
        self,
        failure_code: str | None,
        failure_reason: str | None,
        payment_method: str | None,
        amount: Decimal,
    ) -> RecoveryDecision:

        code = (failure_code or "").upper()
        reason = (failure_reason or "").lower()
        method = (payment_method or "").lower()

        if (
            "INSUFFICIENT_FUNDS" in code
            or "insufficient" in reason
        ):
            return RecoveryDecision(
                classification="INSUFFICIENT_FUNDS",
                recoverability="medium",
                risk_score=Decimal("65.00"),
                recommended_action="delayed_retry",
                reason=(
                    "Payment appears to have failed because "
                    "the funding source may not have sufficient balance."
                ),
            )

        if (
            "EXPIRED" in code
            or "expired" in reason
        ):
            return RecoveryDecision(
                classification="PAYMENT_METHOD_EXPIRED",
                recoverability="high",
                risk_score=Decimal("80.00"),
                recommended_action="request_payment_method_update",
                reason=(
                    "The payment method appears to be expired "
                    "or no longer valid."
                ),
            )

        if (
            "BANK_DECLINED" in code
            or (
                "BAD_REQUEST_ERROR" in code
                and "declined" in reason
            )
            or "bank declined" in reason
            or "declined by the issuing bank" in reason
        ):
            return RecoveryDecision(
                classification="BANK_DECLINED",
                recoverability="high",
                risk_score=Decimal("75.00"),
                recommended_action="alternative_payment_method",
                reason=(
                    "The payment was declined by the bank. "
                    "An alternative payment method may recover the revenue."
                ),
            )

        if method == "netbanking":
            return RecoveryDecision(
                classification="NETBANKING_FAILURE",
                recoverability="medium",
                risk_score=Decimal("55.00"),
                recommended_action="alternative_payment_method",
                reason=(
                    "The payment failed through netbanking. "
                    "A different payment method may succeed."
                ),
            )

        return RecoveryDecision(
            classification="UNKNOWN_PAYMENT_FAILURE",
            recoverability="unknown",
            risk_score=Decimal("40.00"),
            recommended_action="manual_review",
            reason=(
                "The failure could not be confidently classified "
                "by the deterministic recovery policy."
            ),
        )