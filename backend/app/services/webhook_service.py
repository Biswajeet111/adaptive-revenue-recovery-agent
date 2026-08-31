import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.models.webhook_event import WebhookEvent
from backend.app.services.reconciliation_service import (
    ReconciliationService,
)
from backend.app.services.recovery_service import RecoveryService
from backend.app.services.razorpay_service import RazorpayService


class WebhookService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # =========================================================
    # WEBHOOK EVENT STORAGE
    # =========================================================

    def event_exists(
        self,
        event_id: str,
    ) -> bool:

        statement = select(WebhookEvent).where(
            WebhookEvent.event_id == event_id
        )

        return (
            self.db.scalar(statement)
            is not None
        )

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
            received_at=datetime.now(
                timezone.utc
            ),
        )

        self.db.add(event)
        self.db.flush()

        return event

    def get_event(
        self,
        event_id: str,
    ) -> WebhookEvent | None:

        statement = select(
            WebhookEvent
        ).where(
            WebhookEvent.event_id == event_id
        )

        return self.db.scalar(
            statement
        )

    # =========================================================
    # PAYMENT EVENTS
    # =========================================================

    def process_payment_event(
        self,
        event: WebhookEvent,
    ) -> None:

        # -----------------------------------------------------
        # WEBHOOK EVENT IDEMPOTENCY
        # -----------------------------------------------------

        if event.processed:
            return

        payload = json.loads(
            event.payload
        )

        payment_container = (
            payload
            .get("payload", {})
            .get("payment", {})
        )

        payment = payment_container.get(
            "entity",
            {},
        )

        if not payment:
            raise ValueError(
                "Payment entity missing from "
                "Razorpay webhook payload."
            )

        payment_id = payment.get(
            "id"
        )

        order_id = payment.get(
            "order_id"
        )

        payment_method = payment.get(
            "method"
        )

        if not payment_id:
            raise ValueError(
                "Payment ID missing from "
                "Razorpay webhook payload."
            )

        # -----------------------------------------------------
        # Determine transaction status
        # -----------------------------------------------------

        if event.event_type == "payment.failed":

            transaction_status = "failed"

        elif event.event_type == "payment.authorized":

            transaction_status = "authorized"

        elif event.event_type == "payment.captured":

            transaction_status = "captured"

        else:
            return

        # -----------------------------------------------------
        # Find transaction using Razorpay order ID
        # -----------------------------------------------------

        transaction = None

        if order_id:

            statement = select(
                Transaction
            ).where(
                Transaction.razorpay_order_id
                == order_id
            )

            transaction = self.db.scalar(
                statement
            )

        # -----------------------------------------------------
        # Fallback: payment ID
        # -----------------------------------------------------

        if transaction is None:

            statement = select(
                Transaction
            ).where(
                Transaction.razorpay_payment_id
                == payment_id
            )

            transaction = self.db.scalar(
                statement
            )

        # -----------------------------------------------------
        # Payment Link underlying payment
        # -----------------------------------------------------

        if transaction is None:

            event.processed = True

            event.processed_at = (
                datetime.now(timezone.utc)
            )

            self.db.flush()

            return

        # -----------------------------------------------------
        # Update transaction
        # -----------------------------------------------------

        transaction.razorpay_payment_id = (
            payment_id
        )

        transaction.status = (
            transaction_status
        )

        transaction.payment_method = (
            payment_method
        )

        # -----------------------------------------------------
        # Failed payment
        # -----------------------------------------------------

        if event.event_type == "payment.failed":

            transaction.failure_code = (
                payment.get(
                    "error_code"
                )
            )

            transaction.failure_reason = (
                payment.get(
                    "error_description"
                )
            )

            recovery_service = (
                RecoveryService(
                    self.db
                )
            )

            recovery_service.create_case_for_transaction(
                transaction
            )

        # -----------------------------------------------------
        # Authorized / captured payment
        # -----------------------------------------------------

        elif event.event_type in {
            "payment.authorized",
            "payment.captured",
        }:

            transaction.failure_code = None

            transaction.failure_reason = None

        # -----------------------------------------------------
        # Mark processed
        # -----------------------------------------------------

        event.processed = True

        event.processed_at = (
            datetime.now(timezone.utc)
        )

        self.db.flush()

    # =========================================================
    # PAYMENT LINK EVENTS
    # =========================================================

    def process_payment_link_event(
        self,
        event: WebhookEvent,
    ) -> None:

        # -----------------------------------------------------
        # WEBHOOK EVENT IDEMPOTENCY
        # -----------------------------------------------------

        if event.processed:
            return

        # -----------------------------------------------------
        # Parse payload
        # -----------------------------------------------------

        payload = json.loads(
            event.payload
        )

        payload_data = payload.get(
            "payload",
            {},
        )

        # -----------------------------------------------------
        # Payment Link entity
        # -----------------------------------------------------

        payment_link = (
            payload_data
            .get("payment_link", {})
            .get("entity", {})
        )

        if not payment_link:

            raise ValueError(
                "Payment Link entity missing from "
                "Razorpay webhook payload."
            )

        payment_link_id = (
            payment_link.get("id")
        )

        if not payment_link_id:

            raise ValueError(
                "Payment Link ID missing from "
                "Razorpay webhook payload."
            )

        # -----------------------------------------------------
        # Payment entity
        # -----------------------------------------------------

        payment = (
            payload_data
            .get("payment", {})
            .get("entity", {})
        )

        # -----------------------------------------------------
        # Find recovery action
        # -----------------------------------------------------

        statement = select(
            RecoveryAction
        ).where(
            RecoveryAction.metadata_json.contains(
                payment_link_id
            )
        )

        action = self.db.scalar(
            statement
        )

        if action is None:

            raise ValueError(
                f"No recovery action found for "
                f"Payment Link {payment_link_id}."
            )

        # -----------------------------------------------------
        # Action-level idempotency
        # -----------------------------------------------------

        if action.status == "successful":

            event.processed = True

            event.processed_at = (
                datetime.now(timezone.utc)
            )

            self.db.flush()

            return

        # -----------------------------------------------------
        # Find recovery case
        # -----------------------------------------------------

        statement = select(
            RecoveryCase
        ).where(
            RecoveryCase.id
            == action.recovery_case_id
        )

        recovery_case = self.db.scalar(
            statement
        )

        if recovery_case is None:

            raise ValueError(
                f"Recovery case not found for "
                f"action {action.id}."
            )

        # -----------------------------------------------------
        # Find original transaction
        # -----------------------------------------------------

        statement = select(
            Transaction
        ).where(
            Transaction.id
            == recovery_case.transaction_id
        )

        transaction = self.db.scalar(
            statement
        )

        if transaction is None:

            raise ValueError(
                f"Transaction not found for "
                f"recovery case "
                f"{recovery_case.id}."
            )

        # -----------------------------------------------------
        # Reconciliation service
        # -----------------------------------------------------

        reconciliation_service = (
            ReconciliationService(
                RazorpayService()
            )
        )

        # =====================================================
        # PAYMENT LINK PAID
        # =====================================================

        if event.event_type == "payment_link.paid":

            if not payment:

                raise ValueError(
                    "Payment Link reports paid, "
                    "but payment entity is missing."
                )

            reconciliation_service.reconcile_payment_link(
                action=action,
                recovery_case=recovery_case,
                transaction=transaction,
                payment=payment,
                payment_link=payment_link,
            )

        # =====================================================
        # PAYMENT LINK PARTIALLY PAID
        # =====================================================

        elif (
            event.event_type
            == "payment_link.partially_paid"
        ):

            if not payment:

                raise ValueError(
                    "Payment Link reports partial payment, "
                    "but payment entity is missing."
                )

            reconciliation_service.reconcile_payment_link(
                action=action,
                recovery_case=recovery_case,
                transaction=transaction,
                payment=payment,
                payment_link=payment_link,
            )

        # =====================================================
        # PAYMENT LINK EXPIRED
        # =====================================================

        elif (
            event.event_type
            == "payment_link.expired"
        ):

            action.status = "failed"

            action.result = (
                "Razorpay Payment Link expired "
                "without successful recovery."
            )

        # =====================================================
        # PAYMENT LINK CANCELLED
        # =====================================================

        elif (
            event.event_type
            == "payment_link.cancelled"
        ):

            action.status = "failed"

            action.result = (
                "Razorpay Payment Link was "
                "cancelled."
            )

        # =====================================================
        # UNKNOWN PAYMENT LINK EVENT
        # =====================================================

        else:
            return

        # -----------------------------------------------------
        # Mark webhook event processed
        # -----------------------------------------------------

        event.processed = True

        event.processed_at = (
            datetime.now(timezone.utc)
        )

        self.db.flush()