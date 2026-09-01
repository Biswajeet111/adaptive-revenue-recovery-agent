import json
from datetime import datetime, timezone

from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.communication import Communication
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction


def main():

    print("=== PHASE 11.1 COMMUNICATION MODEL TEST ===")

    db = SessionLocal()

    communication_id = None

    try:

        # -------------------------------------------------
        # FIND A SAFE EXISTING RECOVERY ACTION
        # -------------------------------------------------

        action = db.scalar(
            select(RecoveryAction)
            .order_by(
                RecoveryAction.id.desc()
            )
        )

        if action is None:
            raise RuntimeError(
                "No recovery action exists. "
                "Create an AI test case first."
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

        transaction = db.scalar(
            select(Transaction).where(
                Transaction.id
                == recovery_case.transaction_id
            )
        )

        if transaction is None:
            raise RuntimeError(
                "Transaction not found."
            )

        # -------------------------------------------------
        # CREATE COMMUNICATION
        # -------------------------------------------------

        idempotency_key = (
            f"phase11.1-test-"
            f"case-{recovery_case.id}-"
            f"action-{action.id}"
        )

        communication = Communication(
            recovery_case_id=recovery_case.id,
            recovery_action_id=action.id,
            channel="email",
            template_name="payment_recovery",
            template_version="1.0",
            recipient="test@example.com",
            subject="Payment recovery test",
            message=(
                "This is a Phase 11.1 communication "
                "model test message."
            ),
            status="pending",
            provider="test",
            idempotency_key=idempotency_key,
            metadata_json=json.dumps(
                {
                    "test": True,
                    "transaction_id": (
                        transaction.id
                    ),
                }
            ),
        )

        db.add(communication)
        db.commit()
        db.refresh(communication)

        communication_id = communication.id

        print(
            f"Communication created: "
            f"{communication.id}"
        )

        assert (
            communication.recovery_case_id
            == recovery_case.id
        )

        assert (
            communication.recovery_action_id
            == action.id
        )

        assert (
            communication.status
            == "pending"
        )

        print(
            "TEST 1 PASSED: Communication "
            "persisted correctly."
        )

        # -------------------------------------------------
        # VERIFY IDEMPOTENCY KEY
        # -------------------------------------------------

        duplicate = Communication(
            recovery_case_id=recovery_case.id,
            recovery_action_id=action.id,
            channel="email",
            template_name="payment_recovery",
            template_version="1.0",
            recipient="test@example.com",
            subject="Duplicate test",
            message="Duplicate communication.",
            status="pending",
            provider="test",
            idempotency_key=idempotency_key,
        )

        db.add(duplicate)

        duplicate_rejected = False

        try:

            db.commit()

        except Exception:

            db.rollback()

            duplicate_rejected = True

        assert duplicate_rejected

        print(
            "TEST 2 PASSED: Duplicate "
            "idempotency key rejected."
        )

        # -------------------------------------------------
        # VERIFY LIFECYCLE FIELDS
        # -------------------------------------------------

        communication = db.scalar(
            select(Communication).where(
                Communication.id
                == communication_id
            )
        )

        now = datetime.now(timezone.utc)

        communication.status = "sent"
        communication.sent_at = now
        communication.provider_message_id = (
            "TEST-MESSAGE-001"
        )

        db.commit()

        db.refresh(communication)

        assert (
            communication.status
            == "sent"
        )

        assert (
            communication.sent_at
            is not None
        )

        assert (
            communication.provider_message_id
            == "TEST-MESSAGE-001"
        )

        print(
            "TEST 3 PASSED: Delivery lifecycle "
            "fields persisted correctly."
        )

        # -------------------------------------------------
        # VERIFY FAILURE STATE
        # -------------------------------------------------

        communication.status = "failed"
        communication.failed_at = (
            datetime.now(timezone.utc)
        )
        communication.failure_reason = (
            "Simulated provider failure."
        )

        db.commit()

        db.refresh(communication)

        assert (
            communication.status
            == "failed"
        )

        assert (
            communication.failed_at
            is not None
        )

        assert (
            communication.failure_reason
            == "Simulated provider failure."
        )

        print(
            "TEST 4 PASSED: Failure state "
            "persisted correctly."
        )

        print(
            "\n=== PHASE 11.1 COMMUNICATION "
            "MODEL TEST PASSED ==="
        )

    finally:

        # -------------------------------------------------
        # CLEAN TEST FIXTURE
        # -------------------------------------------------

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
