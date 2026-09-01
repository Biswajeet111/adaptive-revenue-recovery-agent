from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.communication import Communication
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.services.communication_provider import (
    TestEmailProvider,
    TestSMSProvider,
)
from backend.app.services.communication_service import (
    CommunicationService,
)


def main():

    print(
        "=== PHASE 11.4 COMMUNICATION SERVICE TEST ==="
    )

    db = SessionLocal()

    communication_id = None

    try:

        # -------------------------------------------------
        # FIND TEST FIXTURE
        # -------------------------------------------------

        action = db.scalar(
            select(RecoveryAction)
            .where(
                RecoveryAction.action_type
                == "alternative_payment_method"
            )
            .order_by(
                RecoveryAction.id.desc()
            )
        )

        if action is None:
            raise RuntimeError(
                "No alternative-payment recovery action found."
            )

        recovery_case = db.scalar(
            select(RecoveryCase).where(
                RecoveryCase.id
                == action.recovery_case_id
            )
        )

        if recovery_case is None:
            raise RuntimeError(
                "Recovery case not found."
            )

        service = CommunicationService(
            db=db,
            providers={
                "email": TestEmailProvider(),
                "sms": TestSMSProvider(),
            },
        )

        idempotency_key = (
            f"phase11.4-"
            f"case-{recovery_case.id}-"
            f"action-{action.id}"
        )

        # -------------------------------------------------
        # CREATE
        # -------------------------------------------------

        communication = service.create(
            recovery_case=recovery_case,
            recovery_action=action,
            channel="email",
            recipient="test@example.com",
            variables={
                "customer_name": "Test Customer",
                "currency": "INR",
                "amount": "100.00",
                "payment_link": (
                    "https://example.test/pay"
                ),
                "expiry": "31 Aug 2026",
            },
            idempotency_key=idempotency_key,
            payment_link_created=True,
            recovery_confirmed=False,
        )

        communication_id = communication.id

        assert (
            communication.status
            == "pending"
        )

        assert (
            communication.template_name
            == "payment_recovery"
        )

        print(
            "TEST 1 PASSED: Communication created "
            "through policy and template layers."
        )

        # -------------------------------------------------
        # SEND
        # -------------------------------------------------

        communication = service.send(
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

        assert (
            communication.provider_message_id
            is not None
        )

        assert (
            communication.sent_at
            is not None
        )

        print(
            "TEST 2 PASSED: Communication sent "
            "through channel provider."
        )

        # -------------------------------------------------
        # DELIVER
        # -------------------------------------------------

        communication = (
            service.mark_delivered(
                communication
            )
        )

        assert (
            communication.status
            == "delivered"
        )

        assert (
            communication.delivered_at
            is not None
        )

        print(
            "TEST 3 PASSED: Delivery state "
            "recorded correctly."
        )

        # -------------------------------------------------
        # IDEMPOTENCY
        # -------------------------------------------------

        duplicate = service.create(
            recovery_case=recovery_case,
            recovery_action=action,
            channel="email",
            recipient="test@example.com",
            variables={
                "customer_name": "Test Customer",
                "currency": "INR",
                "amount": "100.00",
                "payment_link": (
                    "https://example.test/pay"
                ),
                "expiry": "31 Aug 2026",
            },
            idempotency_key=idempotency_key,
            payment_link_created=True,
            recovery_confirmed=False,
        )

        assert (
            duplicate.id
            == communication.id
        )

        assert (
            duplicate.status
            == "delivered"
        )

        print(
            "TEST 4 PASSED: Communication "
            "idempotency preserved."
        )

        # -------------------------------------------------
        # NO PROVIDER
        # -------------------------------------------------

        no_provider_service = (
            CommunicationService(
                db=db,
                providers={},
            )
        )

        no_provider_key = (
            f"{idempotency_key}-no-provider"
        )

        pending = no_provider_service.create(
            recovery_case=recovery_case,
            recovery_action=action,
            channel="email",
            recipient="test@example.com",
            variables={
                "customer_name": "Test Customer",
                "currency": "INR",
                "amount": "100.00",
                "payment_link": (
                    "https://example.test/pay"
                ),
                "expiry": "31 Aug 2026",
            },
            idempotency_key=no_provider_key,
            payment_link_created=True,
            recovery_confirmed=False,
        )

        no_provider_id = pending.id

        pending = no_provider_service.send(
            pending
        )

        assert (
            pending.status
            == "failed"
        )

        assert (
            pending.failed_at
            is not None
        )

        print(
            "TEST 5 PASSED: Missing provider "
            "fails communication safely."
        )

        db.delete(pending)
        db.commit()

        print(
            "\n=== PHASE 11.4 COMMUNICATION SERVICE "
            "TEST PASSED ==="
        )

    finally:

        if communication_id is not None:

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
                db.commit()

        db.close()


if __name__ == "__main__":
    main()