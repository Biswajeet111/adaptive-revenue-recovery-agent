from backend.app.services.communication_policy import (
    CommunicationPolicyService,
)


def main():

    print(
        "=== PHASE 11.3 COMMUNICATION POLICY TEST ==="
    )

    policy = CommunicationPolicyService()

    # -------------------------------------------------
    # TEST 1
    # ALTERNATIVE PAYMENT LINK
    # -------------------------------------------------

    decision = policy.evaluate(
        action_type="alternative_payment_method",
        recovery_case_status="open",
        recovery_action_status="executed",
        payment_link_created=True,
        recovery_confirmed=False,
        channel="email",
    )

    assert decision.decision == "allowed"

    assert (
        decision.template_name
        == "payment_recovery"
    )

    assert (
        decision.template_version
        == "1.0"
    )

    assert (
        decision.channel
        == "email"
    )

    print(
        "TEST 1 PASSED: Alternative payment "
        "communication allowed."
    )

    # -------------------------------------------------
    # TEST 2
    # PAYMENT LINK CREATION IS NOT RECOVERY
    # -------------------------------------------------

    decision = policy.evaluate(
        action_type="alternative_payment_method",
        recovery_case_status="open",
        recovery_action_status="executed",
        payment_link_created=True,
        recovery_confirmed=False,
        channel="email",
    )

    assert (
        decision.template_name
        != "payment_recovered"
    )

    print(
        "TEST 2 PASSED: Payment Link creation "
        "cannot be represented as recovery."
    )

    # -------------------------------------------------
    # TEST 3
    # RECOVERY CONFIRMED
    # -------------------------------------------------

    decision = policy.evaluate(
        action_type="alternative_payment_method",
        recovery_case_status="recovered",
        recovery_action_status="successful",
        payment_link_created=True,
        recovery_confirmed=True,
        channel="email",
    )

    assert decision.decision == "allowed"

    assert (
        decision.template_name
        == "payment_recovered"
    )

    print(
        "TEST 3 PASSED: Confirmed recovery "
        "communication allowed."
    )

    # -------------------------------------------------
    # TEST 4
    # RECOVERED WITHOUT PROVIDER CONFIRMATION
    # -------------------------------------------------

    decision = policy.evaluate(
        action_type="alternative_payment_method",
        recovery_case_status="recovered",
        recovery_action_status="successful",
        payment_link_created=True,
        recovery_confirmed=False,
        channel="email",
    )

    assert decision.decision == "blocked"

    print(
        "TEST 4 PASSED: Unconfirmed recovery "
        "communication blocked."
    )

    # -------------------------------------------------
    # TEST 5
    # MANUAL REVIEW
    # -------------------------------------------------

    decision = policy.evaluate(
        action_type="manual_review",
        recovery_case_status="open",
        recovery_action_status="pending",
        payment_link_created=False,
        recovery_confirmed=False,
        channel="email",
    )

    assert (
        decision.decision
        == "escalated"
    )

    print(
        "TEST 5 PASSED: Manual review "
        "correctly escalated."
    )

    # -------------------------------------------------
    # TEST 6
    # NO PAYMENT LINK
    # -------------------------------------------------

    decision = policy.evaluate(
        action_type="alternative_payment_method",
        recovery_case_status="open",
        recovery_action_status="pending",
        payment_link_created=False,
        recovery_confirmed=False,
        channel="email",
    )

    assert (
        decision.decision
        == "blocked"
    )

    print(
        "TEST 6 PASSED: Communication blocked "
        "without recovery option."
    )

    # -------------------------------------------------
    # TEST 7
    # INTERNAL DATA PROTECTION
    # -------------------------------------------------

    variables = {
        "customer_name": "Test Customer",
        "currency": "INR",
        "amount": "100.00",
        "payment_link": "https://example.test/pay",
        "expiry": "31 Aug 2026",
        "failure_code": "BANK_DECLINED",
    }

    rejected = False

    try:

        policy.validate_variables(
            variables,
            frozenset(
                {
                    "customer_name",
                    "currency",
                    "amount",
                    "payment_link",
                    "expiry",
                }
            ),
        )

    except ValueError as exc:

        rejected = True

        assert (
            "internal fields"
            in str(exc)
        )

    assert rejected

    print(
        "TEST 7 PASSED: Internal failure "
        "information cannot be exposed."
    )

    # -------------------------------------------------
    # TEST 8
    # VALID VARIABLES
    # -------------------------------------------------

    valid_variables = {
        "customer_name": "Test Customer",
        "currency": "INR",
        "amount": "100.00",
        "payment_link": "https://example.test/pay",
        "expiry": "31 Aug 2026",
    }

    policy.validate_variables(
        valid_variables,
        frozenset(
            {
                "customer_name",
                "currency",
                "amount",
                "payment_link",
                "expiry",
            }
        ),
    )

    print(
        "TEST 8 PASSED: Approved communication "
        "variables accepted."
    )

    print(
        "\n=== PHASE 11.3 COMMUNICATION POLICY "
        "TEST PASSED ==="
    )


if __name__ == "__main__":
    main()