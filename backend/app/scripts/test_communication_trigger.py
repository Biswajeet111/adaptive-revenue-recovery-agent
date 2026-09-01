from decimal import Decimal

from backend.app.services.communication_trigger import (
    CommunicationTriggerService,
)


def main():

    print(
        "=== PHASE 11.6 COMMUNICATION TRIGGER TEST ==="
    )

    service = CommunicationTriggerService()

    # Lightweight fixtures are enough because the trigger
    # service only needs model IDs and recovery state.

    transaction = type(
        "TransactionFixture",
        (),
        {
            "id": 101,
        },
    )()

    recovery_case = type(
        "RecoveryCaseFixture",
        (),
        {
            "id": 201,
            "recovered_amount": Decimal("100.00"),
        },
    )()

    recovery_action = type(
        "RecoveryActionFixture",
        (),
        {
            "id": 301,
        },
    )()

    # -------------------------------------------------
    # TEST 1 — PAYMENT LINK CREATED
    # -------------------------------------------------

    trigger = service.payment_link_created(
        transaction=transaction,
        recovery_case=recovery_case,
        recovery_action=recovery_action,
    )

    assert (
        trigger.event_type
        == "payment_link_created"
    )

    assert (
        trigger.transaction_id
        == transaction.id
    )

    assert (
        trigger.recovery_case_id
        == recovery_case.id
    )

    assert (
        trigger.recovery_action_id
        == recovery_action.id
    )

    assert trigger.payment_link_created is True
    assert trigger.recovery_confirmed is False

    print(
        "TEST 1 PASSED: Payment Link creation "
        "trigger generated correctly."
    )

    # -------------------------------------------------
    # TEST 2 — PARTIAL PAYMENT
    # -------------------------------------------------

    trigger = service.partial_payment_received(
        transaction=transaction,
        recovery_case=recovery_case,
        recovery_action=recovery_action,
        recovered_amount=Decimal("40.00"),
        remaining_amount=Decimal("60.00"),
    )

    assert (
        trigger.event_type
        == "partial_payment_received"
    )

    assert (
        trigger.recovered_amount
        == Decimal("40.00")
    )

    assert (
        trigger.remaining_amount
        == Decimal("60.00")
    )

    assert trigger.recovery_confirmed is False

    print(
        "TEST 2 PASSED: Partial-payment "
        "trigger preserves recovery amounts."
    )

    # -------------------------------------------------
    # TEST 3 — FULL RECOVERY
    # -------------------------------------------------

    trigger = service.payment_recovered(
        transaction=transaction,
        recovery_case=recovery_case,
        recovery_action=recovery_action,
    )

    assert (
        trigger.event_type
        == "payment_recovered"
    )

    assert trigger.recovery_confirmed is True

    assert (
        trigger.recovered_amount
        == Decimal("100.00")
    )

    assert (
        trigger.remaining_amount
        == Decimal("0")
    )

    print(
        "TEST 3 PASSED: Confirmed recovery "
        "trigger generated correctly."
    )

    # -------------------------------------------------
    # TEST 4 — EXPIRED PAYMENT LINK
    # -------------------------------------------------

    trigger = service.payment_link_expired(
        transaction=transaction,
        recovery_case=recovery_case,
        recovery_action=recovery_action,
    )

    assert (
        trigger.event_type
        == "payment_link_expired"
    )

    assert trigger.payment_link_created is True
    assert trigger.recovery_confirmed is False

    print(
        "TEST 4 PASSED: Expired Payment Link "
        "trigger generated safely."
    )

    # -------------------------------------------------
    # TEST 5 — CANCELLED PAYMENT LINK
    # -------------------------------------------------

    trigger = service.payment_link_cancelled(
        transaction=transaction,
        recovery_case=recovery_case,
        recovery_action=recovery_action,
    )

    assert (
        trigger.event_type
        == "payment_link_cancelled"
    )

    assert trigger.payment_link_created is True
    assert trigger.recovery_confirmed is False

    print(
        "TEST 5 PASSED: Cancelled Payment Link "
        "trigger generated safely."
    )

    # -------------------------------------------------
    # TEST 6 — ENTITY ASSOCIATION
    # -------------------------------------------------

    assert (
        trigger.transaction_id
        == 101
    )

    assert (
        trigger.recovery_case_id
        == 201
    )

    assert (
        trigger.recovery_action_id
        == 301
    )

    print(
        "TEST 6 PASSED: Every trigger remains "
        "traceable to transaction, case, and action."
    )

    print(
        "\n=== PHASE 11.6 COMMUNICATION TRIGGER "
        "TEST PASSED ==="
    )


if __name__ == "__main__":
    main()