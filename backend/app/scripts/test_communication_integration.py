from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.communication import Communication
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.services.communication_service import (
    CommunicationService,
)
from backend.app.services.communication_provider import (
    TestEmailProvider,
)


def main():

    print(
        "=== PHASE 11.5 COMMUNICATION INTEGRATION TEST ==="
    )

    db = SessionLocal()

    communication_id = None

    try:

        # -------------------------------------------------
        # FIND LATEST EXECUTED PAYMENT-LINK ACTION
        # -------------------------------------------------

        action = db.scalar(
            select(RecoveryAction)
            .where(
                RecoveryAction.status == "executed",
                RecoveryAction.action_type
                == "alternative_payment_method",
            )
            .order_by(
                RecoveryAction.id.desc()
            )
        )

        if action is None:

            raise RuntimeError(
                "No executed alternative-payment "
                "recovery action found."
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

        # -------------------------------------------------
        # EXTRACT PAYMENT LINK METADATA
        # -------------------------------------------------

        import json

        if not action.metadata_json:

            raise RuntimeError(
                "Recovery action does not contain "
                "Payment Link metadata."
            )

        metadata = json.loads(
            action.metadata_json
        )

        payment_link = metadata.get(
            "short_url"
        )

        if not payment_link:

            raise RuntimeError(
                "Payment Link URL missing from "
                "recovery action metadata."
            )

        # -------------------------------------------------
        # COMMUNICATION SERVICE
        # -------------------------------------------------

        service = CommunicationService(
            db=db,
            providers={
                "email": TestEmailProvider(),
            },
        )

        idempotency_key = (
            f"phase11.5-"
            f"case-{recovery_case.id}-"
            f"action-{action.id}"
        )

        # -------------------------------------------------
        # CREATE CUSTOMER COMMUNICATION
        # -------------------------------------------------

        communication = service.create(
            recovery_case=recovery_case,
            recovery_action=action,
            channel="email",
            recipient="test@example.com",
            variables={
                "customer_name": "Test Customer",
                "currency": "INR",
                "amount": str(
                    recovery_case.revenue_at_risk
                ),
                "payment_link": payment_link,
                "expiry": "31 Aug 2026",
            },
            idempotency_key=idempotency_key,
            payment_link_created=True,
            recovery_confirmed=False,
        )

        communication_id = (
            communication.id
        )

        # -------------------------------------------------
        # VERIFY DATABASE ASSOCIATION
        # -------------------------------------------------

        assert (
            communication.recovery_case_id
            == recovery_case.id
        )

        assert (
            communication.recovery_action_id
            == action.id
        )

        assert (
            communication.template_name
            == "payment_recovery"
        )

        assert (
            communication.template_version
            == "1.0"
        )

        assert (
            communication.channel
            == "email"
        )

        assert (
            communication.status
            == "pending"
        )

        print(
            "TEST 1 PASSED: Communication linked "
            "to recovery case and action."
        )

        # -------------------------------------------------
        # VERIFY CONTENT
        # -------------------------------------------------

        assert (
            "Test Customer"
            in communication.message
        )

        assert (
            payment_link
            in communication.message
        )

        assert (
            "BANK_DECLINED"
            not in communication.message
        )

        assert (
            "risk_score"
            not in communication.message
        )

        print(
            "TEST 2 PASSED: Customer message "
            "contains approved content only."
        )

        # -------------------------------------------------
        # VERIFY POLICY METADATA
        # -------------------------------------------------

        communication_metadata = json.loads(
            communication.metadata_json
        )

        assert (
            communication_metadata["policy"]
            == "Communication Policy"
        )

        assert (
            communication_metadata["policy_version"]
            == "1.0"
        )

        print(
            "TEST 3 PASSED: Policy provenance "
            "recorded with communication."
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
                "amount": str(
                    recovery_case.revenue_at_risk
                ),
                "payment_link": payment_link,
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

        print(
            "TEST 4 PASSED: Integration "
            "idempotency preserved."
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

        print(
            "TEST 5 PASSED: Integrated "
            "communication dispatched safely."
        )

        print(
            "\n=== PHASE 11.5 COMMUNICATION "
            "INTEGRATION TEST PASSED ==="
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