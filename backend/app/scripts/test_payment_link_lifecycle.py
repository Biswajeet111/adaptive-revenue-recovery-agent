import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.models.webhook_event import WebhookEvent
from backend.app.services.webhook_service import WebhookService


TEST_ACTION_ID = 9
TEST_PAYMENT_LINK_ID = "plink_PHASE9_TEST"


def build_payload(
    event_type: str,
    amount_paid: int,
    payment_status: str,
):
    return {
        "entity": "event",
        "event": event_type,
        "payload": {
            "payment_link": {
                "entity": {
                    "id": TEST_PAYMENT_LINK_ID,
                    "status": (
                        "paid"
                        if event_type
                        == "payment_link.paid"
                        else "partially_paid"
                    ),
                    "amount": 10000,
                    "amount_paid": amount_paid,
                    "currency": "INR",
                    "reference_id": "PHASE9-TEST",
                }
            },
            "payment": {
                "entity": {
                    "id": f"pay_PHASE9_{uuid.uuid4().hex[:8]}",
                    "amount": amount_paid,
                    "status": payment_status,
                    "method": "netbanking",
                }
            },
        },
    }


def prepare_action(action):
    action.status = "executed"
    action.executed_at = datetime.now(timezone.utc)

    action.metadata_json = json.dumps(
        {
            "provider": "razorpay",
            "payment_link_id": TEST_PAYMENT_LINK_ID,
            "short_url": "https://example.com/phase9-test",
            "status": "created",
            "reference_id": "PHASE9-TEST",
            "expire_by": 9999999999,
        }
    )


def create_event(
    db,
    event_type: str,
    amount_paid: int,
    payment_status: str,
):
    event = WebhookEvent(
        event_id=(
            f"PHASE9-{uuid.uuid4().hex}"
        ),
        event_type=event_type,
        payload=json.dumps(
            build_payload(
                event_type=event_type,
                amount_paid=amount_paid,
                payment_status=payment_status,
            )
        ),
        signature="phase9-test",
        processed=False,
    )

    db.add(event)
    db.flush()

    return event


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
                f"Recovery Action {TEST_ACTION_ID} "
                "not found."
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

        service = WebhookService(db)

        print(
            "=== PHASE 9 PAYMENT LINK LIFECYCLE TEST ==="
        )

        print(
            f"Action: {action.id}"
        )

        print(
            f"Recovery Case: {recovery_case.id}"
        )

        print(
            f"Transaction: {transaction.id}"
        )

        # =====================================================
        # TEST 1 — PARTIAL PAYMENT
        # =====================================================

        prepare_action(action)

        recovery_case.recovered_amount = None
        recovery_case.recovered_at = None
        recovery_case.status = "open"

        transaction.status = "failed"
        transaction.razorpay_payment_id = None

        event = create_event(
            db=db,
            event_type="payment_link.partially_paid",
            amount_paid=4000,
            payment_status="captured",
        )

        service.process_payment_link_event(event)

        db.commit()

        assert (
            recovery_case.recovered_amount
            == Decimal("40.00")
        )

        assert recovery_case.status == "open"

        assert transaction.status == "failed"

        assert action.status == "pending"

        print(
            "TEST 1 PASSED: ₹40 partial recovery "
            "tracked correctly."
        )

        # =====================================================
        # TEST 2 — SECOND PARTIAL PAYMENT
        # =====================================================

        prepare_action(action)

        event = create_event(
            db=db,
            event_type="payment_link.partially_paid",
            amount_paid=6000,
            payment_status="captured",
        )

        service.process_payment_link_event(event)

        db.commit()

        assert (
            recovery_case.recovered_amount
            == Decimal("100.00")
        )

        assert recovery_case.status == "recovered"

        assert transaction.status == "captured"

        assert action.status == "successful"

        print(
            "TEST 2 PASSED: cumulative ₹40 + ₹60 "
            "completed recovery."
        )

        # =====================================================
        # TEST 3 — EXPIRED
        # =====================================================

        action.status = "executed"
        recovery_case.status = "open"
        recovery_case.recovered_amount = None
        recovery_case.recovered_at = None
        transaction.status = "failed"

        prepare_action(action)

        event = create_event(
            db=db,
            event_type="payment_link.expired",
            amount_paid=0,
            payment_status="failed",
        )

        service.process_payment_link_event(event)

        db.commit()

        assert action.status == "failed"
        assert recovery_case.status == "open"
        assert transaction.status == "failed"

        print(
            "TEST 3 PASSED: expired Payment Link "
            "handled safely."
        )

        # =====================================================
        # TEST 4 — CANCELLED
        # =====================================================

        action.status = "executed"

        prepare_action(action)

        event = create_event(
            db=db,
            event_type="payment_link.cancelled",
            amount_paid=0,
            payment_status="failed",
        )

        service.process_payment_link_event(event)

        db.commit()

        assert action.status == "failed"
        assert recovery_case.status == "open"
        assert transaction.status == "failed"

        print(
            "TEST 4 PASSED: cancelled Payment Link "
            "handled safely."
        )

        # =====================================================
        # CLEANUP
        # =====================================================

        action.status = "pending"
        action.executed_at = None
        action.result = None
        action.metadata_json = None

        recovery_case.status = "open"
        recovery_case.recovered_amount = None
        recovery_case.recovered_at = None

        transaction.status = "failed"
        transaction.razorpay_payment_id = None

        db.commit()

        print()
        print(
            "=== PHASE 9 LIFECYCLE TEST PASSED ==="
        )

        print(
            "Test action restored to pending."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()