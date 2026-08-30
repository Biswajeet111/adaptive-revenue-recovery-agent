from decimal import Decimal

from backend.app.schemas.recovery_decision import RecoveryDecision
from backend.app.services.decision_safety_gate import (
    DecisionSafetyGate,
)


def make_decision(
    *,
    action: str = "alternative_payment_method",
    confidence: float = 0.91,
) -> RecoveryDecision:

    return RecoveryDecision(
        classification="BANK_DECLINED",
        recoverability="high",
        recommended_action=action,
        confidence=confidence,
        reason=(
            "The bank decline appears recoverable and "
            "policy evidence supports the selected action."
        ),
        policy_references=[
            "Recovery Policy v1.0",
            "Retry Policy v1.0",
        ],
    )


def main():

    gate = DecisionSafetyGate()

    # =========================================================
    # TEST 1 — Valid automated recovery
    # =========================================================

    decision = make_decision(
        confidence=0.91
    )

    result = gate.validate(
        decision=decision,
        transaction_amount=Decimal("100.00"),
        previous_recovery_attempts=0,
        policy_evidence_count=3,
    )

    assert (
        result.recommended_action
        == "alternative_payment_method"
    )

    print(
        "TEST 1 PASSED: "
        "Valid high-confidence decision accepted."
    )

    # =========================================================
    # TEST 2 — Low confidence
    # =========================================================

    decision = make_decision(
        confidence=0.30
    )

    result = gate.validate(
        decision=decision,
        transaction_amount=Decimal("100.00"),
        previous_recovery_attempts=0,
        policy_evidence_count=3,
    )

    assert (
        result.recommended_action
        == "manual_review"
    )

    print(
        "TEST 2 PASSED: "
        "Low-confidence decision escalated."
    )

    # =========================================================
    # TEST 3 — Too many recovery attempts
    # =========================================================

    decision = make_decision(
        confidence=0.95
    )

    result = gate.validate(
        decision=decision,
        transaction_amount=Decimal("100.00"),
        previous_recovery_attempts=2,
        policy_evidence_count=3,
    )

    assert (
        result.recommended_action
        == "manual_review"
    )

    print(
        "TEST 3 PASSED: "
        "Recovery attempt limit enforced."
    )

    # =========================================================
    # TEST 4 — High-value transaction
    # =========================================================

    decision = make_decision(
        confidence=0.95
    )

    result = gate.validate(
        decision=decision,
        transaction_amount=Decimal("10001.00"),
        previous_recovery_attempts=0,
        policy_evidence_count=3,
    )

    assert (
        result.recommended_action
        == "manual_review"
    )

    print(
        "TEST 4 PASSED: "
        "High-value transaction escalated."
    )

    # =========================================================
    # TEST 5 — No policy evidence
    # =========================================================

    decision = make_decision(
        confidence=0.95
    )

    try:
        gate.validate(
            decision=decision,
            transaction_amount=Decimal("100.00"),
            previous_recovery_attempts=0,
            policy_evidence_count=0,
        )

    except ValueError as exc:

        assert (
            "no policy evidence"
            in str(exc).lower()
        )

        print(
            "TEST 5 PASSED: "
            "Decision rejected without policy evidence."
        )

    else:

        raise AssertionError(
            "TEST 5 FAILED: "
            "Decision without policy evidence "
            "was not rejected."
        )

    # =========================================================
    # FINAL RESULT
    # =========================================================

    print()
    print(
        "=== SAFETY GATE TEST SUITE PASSED ==="
    )


if __name__ == "__main__":
    main()