import json
from decimal import Decimal

from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.communication import Communication
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.communication_dispatcher import (
    CommunicationDispatcher,
)
from backend.app.services.communication_provider import (
    TestEmailProvider,
)
from backend.app.services.communication_recipient import (
    CommunicationRecipientResolver,
)
from backend.app.services.communication_service import (
    CommunicationService,
)
from backend.app.services.communication_trigger import (
    CommunicationTriggerService,
)


def main():

    print(
        "=== PHASE 11.7 COMMUNICATION DISPATCHER TEST ==="
    )

    db = SessionLocal()

    created_ids = []

    transaction = None
    recovery_case = None
    recovery_action = None

    try:

        # =================================================
        # CREATE TEST FIXTURES
        # =================================================

        transaction = Transaction(
            razorpay_order_id=(
                "PHASE11_7_TEST_TRANSACTION"
            ),
            amount=Decimal("100.00"),
            currency="INR",
            status="failed",
            payment_method="netbanking",
            failure_code="BANK_DECLINED",
            failure_reason="Test bank decline.",
        )

        db.add(transaction)
        db.flush()

        recovery_case = RecoveryCase(
            transaction_id=transaction.id,
            failure_code="BANK_DECLINED",
            failure_reason="Test bank decline.",
            classification="BANK_DECLINED",
            recoverability="high",
            risk_score=Decimal("10.00"),
            revenue_at_risk=Decimal("100.00"),
            recommended_action=(
                "alternative_payment_method"
            ),
            status="open",
            reason="Phase 11.7 test fixture.",
        )

        db.add(recovery_case)
        db.flush()

        recovery_action = RecoveryAction(
            recovery_case_id=recovery_case.id,
            action_type=(
                "alternative_payment_method"
            ),
            channel="email",
            status="executed",
            metadata_json=json.dumps(
                {
                    "provider": "razorpay",
                    "payment_link_id": (
                        "plink_PHASE11_7"
                    ),
                    "short_url": (
                        "https://example.test/pay"
                    ),
                    "status": "created",
                    "reference_id": "PHASE11_7",
                    "expire_by": 9999999999,
                }
            ),
        )

        db.add(recovery_action)
        db.commit()

        # =================================================
        # SERVICES
        # =================================================

        communication_service = (
            CommunicationService(
                db=db,
                providers={
                    "email": TestEmailProvider(),
                },
            )
        )

        dispatcher = CommunicationDispatcher(
            communication_service
        )

        recipient_resolver = (
            CommunicationRecipientResolver(
                default_email="test@example.com"
            )
        )

        triggers = CommunicationTriggerService()

        # =================================================
        # TEST 1
        # PAYMENT LINK CREATED
        # =================================================

        trigger = (
            triggers.payment_link_created(
                transaction=transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
            )
        )

        communication = dispatcher.dispatch(
            trigger=trigger,
            transaction=transaction,
            recovery_case=recovery_case,
            recovery_action=recovery_action,
            recipient_resolver=recipient_resolver,
            customer_name="Test Customer",
        )

        created_ids.append(
            communication.id
        )

        assert (
            communication.template_name
            == "payment_recovery"
        )

        assert (
            communication.status
            == "pending"
        )

        assert (
            communication.recipient
            == "test@example.com"
        )

        assert (
            "https://example.test/pay"
            in communication.message
        )

        assert (
            "BANK_DECLINED"
            not in communication.message
        )

        print(
            "TEST 1 PASSED: Payment Link trigger "
            "created approved recovery communication."
        )

        # =================================================
        # TEST 2
        # IDEMPOTENCY
        # =================================================

        duplicate = dispatcher.dispatch(
            trigger=trigger,
            transaction=transaction,
            recovery_case=recovery_case,
            recovery_action=recovery_action,
            recipient_resolver=recipient_resolver,
            customer_name="Test Customer",
        )

        assert (
            duplicate.id
            == communication.id
        )

        count = len(
            db.scalars(
                select(Communication).where(
                    Communication.id
                    == communication.id
                )
            ).all()
        )

        assert count == 1

        print(
            "TEST 2 PASSED: Duplicate lifecycle "
            "trigger did not create another message."
        )

        # =================================================
        # TEST 3
        # SEND
        # =================================================

        communication_service.send(
            communication
        )

        assert (
            communication.status
            == "sent"
        )

        assert (
            communication.provider
            == "test_email"
        )

        print(
            "TEST 3 PASSED: Dispatched communication "
            "sent through provider."
        )

        # =================================================
        # TEST 4
        # PARTIAL PAYMENT
        # =================================================

        recovery_case.status = (
            "partially_recovered"
        )

        recovery_case.recovered_amount = (
            Decimal("40.00")
        )

        db.commit()

        trigger = (
            triggers.partial_payment_received(
                transaction=transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
                recovered_amount=Decimal(
                    "40.00"
                ),
                remaining_amount=Decimal(
                    "60.00"
                ),
            )
        )

        partial = dispatcher.dispatch(
            trigger=trigger,
            transaction=transaction,
            recovery_case=recovery_case,
            recovery_action=recovery_action,
            recipient_resolver=recipient_resolver,
            customer_name="Test Customer",
        )

        created_ids.append(
            partial.id
        )

        assert (
            partial.template_name
            == "partial_payment_received"
        )

        assert (
            partial.recipient
            == "test@example.com"
        )

        assert (
            "40.00"
            in partial.message
        )

        assert (
            "60.00"
            in partial.message
        )

        print(
            "TEST 4 PASSED: Partial-payment trigger "
            "created correct communication."
        )

        # =================================================
        # TEST 5
        # FULL RECOVERY
        # =================================================

        recovery_case.status = "recovered"

        recovery_case.recovered_amount = (
            Decimal("100.00")
        )

        db.commit()

        trigger = (
            triggers.payment_recovered(
                transaction=transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
            )
        )

        recovered = dispatcher.dispatch(
            trigger=trigger,
            transaction=transaction,
            recovery_case=recovery_case,
            recovery_action=recovery_action,
            recipient_resolver=recipient_resolver,
            customer_name="Test Customer",
        )

        created_ids.append(
            recovered.id
        )

        assert (
            recovered.template_name
            == "payment_recovered"
        )

        assert (
            recovered.recipient
            == "test@example.com"
        )

        assert (
            "successfully received"
            in recovered.message
        )

        print(
            "TEST 5 PASSED: Provider-confirmed "
            "recovery created success communication."
        )

        # =================================================
        # TEST 6
        # EXPIRED LINK FAIL CLOSED
        # =================================================

        recovery_case.status = "open"
        db.commit()

        trigger = (
            triggers.payment_link_expired(
                transaction=transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
            )
        )

        rejected = False

        try:

            dispatcher.dispatch(
                trigger=trigger,
                transaction=transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
                recipient_resolver=recipient_resolver,
                customer_name="Test Customer",
            )

        except ValueError as exc:

            rejected = True

            assert (
                "No customer-facing template"
                in str(exc)
            )

        assert rejected

        print(
            "TEST 6 PASSED: Expired Payment Link "
            "communication fails closed."
        )

        # =================================================
        # TEST 7
        # ENTITY MISMATCH
        # =================================================

        bad_transaction = Transaction(
            razorpay_order_id=(
                "PHASE11_7_BAD_TRANSACTION"
            ),
            amount=Decimal("100.00"),
            currency="INR",
            status="failed",
        )

        db.add(bad_transaction)
        db.flush()

        rejected = False

        try:

            dispatcher.dispatch(
                trigger=(
                    triggers.payment_link_created(
                        transaction=transaction,
                        recovery_case=recovery_case,
                        recovery_action=recovery_action,
                    )
                ),
                transaction=bad_transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
                recipient_resolver=recipient_resolver,
                customer_name="Test Customer",
            )

        except ValueError as exc:

            rejected = True

            assert (
                "transaction"
                in str(exc).lower()
            )

        assert rejected

        db.delete(
            bad_transaction
        )

        db.commit()

        print(
            "TEST 7 PASSED: Entity mismatch "
            "rejected safely."
        )

        print(
            "\n=== PHASE 11.7 COMMUNICATION DISPATCHER "
            "TEST PASSED ==="
        )

    finally:

        # =================================================
        # CLEAN COMMUNICATIONS
        # =================================================

        for communication_id in created_ids:

            communication = db.scalar(
                select(Communication).where(
                    Communication.id
                    == communication_id
                )
            )

            if communication is not None:
                db.delete(
                    communication
                )

        # =================================================
        # CLEAN FIXTURES
        # =================================================

        if transaction is not None:

            action = None
            case = None

            if recovery_case is not None:

                action = db.scalar(
                    select(RecoveryAction).where(
                        RecoveryAction.recovery_case_id
                        == recovery_case.id
                    )
                )

                case = db.scalar(
                    select(RecoveryCase).where(
                        RecoveryCase.id
                        == recovery_case.id
                    )
                )

            if action is not None:
                db.delete(action)

            if case is not None:
                db.delete(case)

            db.delete(transaction)

        db.commit()
        db.close()


if __name__ == "__main__":
    main()