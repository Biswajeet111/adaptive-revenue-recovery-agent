import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.transaction import Transaction
from backend.app.models.webhook_event import WebhookEvent


class WebhookService:
    def __init__(self, db: Session):
        self.db = db

    def event_exists(self, event_id: str) -> bool:
        statement = select(WebhookEvent).where(
            WebhookEvent.event_id == event_id
        )

        return self.db.scalar(statement) is not None

    def store_event(
        self,
        event_id: str,
        event_type: str,
        payload: dict,
        signature: str | None,
    ) -> WebhookEvent:

        event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            payload=json.dumps(payload),
            signature=signature,
            processed=False,
            received_at=datetime.now(timezone.utc),
        )

        self.db.add(event)
        self.db.flush()

        return event

    def process_payment_event(
        self,
        event: WebhookEvent,
    ) -> None:

        payload = json.loads(event.payload)

        payment_container = payload.get("payload", {}).get("payment", {})
        payment = payment_container.get("entity", {})

        if not payment:
            raise ValueError(
                "Payment entity missing from Razorpay webhook payload"
            )

        payment_id = payment.get("id")
        order_id = payment.get("order_id")
        payment_status = payment.get("status")
        payment_method = payment.get("method")

        if not payment_id:
            raise ValueError(
                "Payment ID missing from Razorpay webhook payload"
            )

        if event.event_type == "payment.failed":
            transaction_status = "failed"

        elif event.event_type == "payment.authorized":
            transaction_status = "authorized"

        elif event.event_type == "payment.captured":
            transaction_status = "captured"

        else:
            return

        transaction = None

        if order_id:
            statement = select(Transaction).where(
                Transaction.razorpay_order_id == order_id
            )

            transaction = self.db.scalar(statement)

        if transaction is None:
            statement = select(Transaction).where(
                Transaction.razorpay_payment_id == payment_id
            )

            transaction = self.db.scalar(statement)

        if transaction is None:
            raise ValueError(
                f"No transaction found for "
                f"order_id={order_id}, payment_id={payment_id}"
            )

        transaction.razorpay_payment_id = payment_id
        transaction.status = transaction_status
        transaction.payment_method = payment_method

        if event.event_type == "payment.failed":
            transaction.failure_code = payment.get(
                "error_code"
            )

            transaction.failure_reason = payment.get(
                "error_description"
            )

        elif event.event_type in {
            "payment.authorized",
            "payment.captured",
        }:
            transaction.failure_code = None
            transaction.failure_reason = None

        event.processed = True
        event.processed_at = datetime.now(timezone.utc)

        self.db.flush()