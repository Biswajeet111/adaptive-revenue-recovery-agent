import json
import uuid

from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.models.webhook_event import WebhookEvent
from backend.app.services.webhook_service import WebhookService


TEST_ACTION_ID = 9
TEST_PAYMENT_LINK_ID = "plink_PHASE9_IDEMPOTENCY_TEST"


def main():
    db = SessionLocal()

    try:
        action = db.scalar(
            select(RecoveryAction).where(
                RecoveryAction.id == TEST_ACTION_ID
            )
        )

        if action is None:
            raise RuntimeError(
                f"Recovery Action {TEST_ACTION_ID} not found."
            )

        recovery_case = db.scalar(
            select(RecoveryCase).where(
                RecoveryCase.id == action.recovery_case_id
            )
        )

        if recovery_case is None:
            raise RuntimeError(
                "Recovery case not found."
            )

        transaction = db.scalar(
            select(Transaction).where(
                Transaction.id == recovery_case.transaction_id
            )
        )

        if transaction is None:
            raise RuntimeError(
                "Transaction not found."
            )

        # ---------------------------------------------------------
        # CONTROLLED TEST FIXTURE
        # ---------------------------------------------------------

        action.status = "executed"
        action.result = None
        action.metadata_json = json.dumps(
            {
                "provider": "razorpay",
                "payment_link_id": TEST_PAYMENT_LINK_ID,
                "reference_id": "PHASE9-IDEMPOTENCY",
            }
        )

        recovery_case.status = "open"
        recovery_case.recovered_amount = None
        recovery_case.recovered_at = None

        transaction.status = "failed"
        transaction.razorpay_payment_id = None

        payment_id = (
            f"pay_PHASE9_{uuid.uuid4().hex[:10]}"
        )

        payload = {
            "entity": "event",
            "event": "payment_link.partially_paid",
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": TEST_PAYMENT_LINK_ID,
                        "status": "partially_paid",
                        "amount": 10000,
                        "amount_paid": 4000,
                        "currency": "INR",
                        "reference_id": "PHASE9-IDEMPOTENCY",
                    }
                },
                "payment": {
                    "entity": {
                        "id": payment_id,
                        "amount": 4000,
                        "status": "captured",
                        "method": "netbanking",
                    }
                },
            },
        }

        event_id = (
            f"PHASE9-IDEMPOTENCY-{uuid.uuid4().hex}"
        )

        event = WebhookEvent(
            event_id=event_id,
            event_type="payment_link.partially_paid",
            payload=json.dumps(payload),
            signature="phase9-test",
            processed=False,
        )

        db.add(event)
        db.flush()

        service = WebhookService(db)

        print(
            "=== PHASE 9 WEBHOOK IDEMPOTENCY TEST ==="
        )

        print(
            f"Event ID: {event_id}"
        )

        # ---------------------------------------------------------
        # FIRST PROCESSING
        # ---------------------------------------------------------

        service.process_payment_link_event(event)

        db.commit()

        first_recovered = (
            recovery_case.recovered_amount
        )

        assert first_recovered is not None
        assert str(first_recovered) == "40.00"

        assert event.processed is True

        print(
            "First processing: PASSED"
        )

        print(
            f"Recovered amount after first event: "
            f"{first_recovered}"
        )

        # ---------------------------------------------------------
        # SECOND PROCESSING
        # ---------------------------------------------------------

        before_second = (
            recovery_case.recovered_amount
        )

        service.process_payment_link_event(event)

        db.commit()

        after_second = (
            recovery_case.recovered_amount
        )

        assert after_second == before_second

        print(
            "Second processing: PASSED"
        )

        print(
            "Recovered amount unchanged: "
            f"{after_second}"
        )

        print(
            "No duplicate recovery recorded."
        )

        # ---------------------------------------------------------
        # CLEANUP
        # ---------------------------------------------------------

        db.delete(event)

        action.status = "pending"
        action.result = None
        action.metadata_json = None
        action.executed_at = None

        recovery_case.status = "open"
        recovery_case.recovered_amount = None
        recovery_case.recovered_at = None

        transaction.status = "failed"
        transaction.razorpay_payment_id = None

        db.commit()

        print()
        print(
            "=== PHASE 9 WEBHOOK IDEMPOTENCY TEST PASSED ==="
        )

        print(
            "Test fixture removed."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()