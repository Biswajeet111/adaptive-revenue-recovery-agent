import json
from datetime import datetime, timezone
from decimal import Decimal

from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.razorpay_service import RazorpayService


class ReconciliationService:

    def __init__(
        self,
        razorpay: RazorpayService,
    ):
        self.razorpay = razorpay

    def reconcile_payment_link(
        self,
        action: RecoveryAction,
        recovery_case: RecoveryCase,
        transaction: Transaction,
    ) -> bool:

        if action.status == "successful":
            return True

        if action.status != "executed":
            raise ValueError(
                f"Recovery action {action.id} "
                f"is not executable for reconciliation. "
                f"Current status: {action.status}"
            )

        if not action.metadata_json:
            raise ValueError(
                f"Recovery action {action.id} "
                "does not contain Payment Link metadata."
            )

        metadata = json.loads(
            action.metadata_json
        )

        payment_link_id = metadata.get(
            "payment_link_id"
        )

        if not payment_link_id:
            raise ValueError(
                "Payment Link ID missing from "
                "recovery action metadata."
            )

        payment_link = (
            self.razorpay.fetch_payment_link(
                payment_link_id
            )
        )

        payment_link_status = payment_link.get(
            "status"
        )

        payments = payment_link.get(
            "payments",
            [],
        )

        captured_payment = next(
            (
                payment
                for payment in payments
                if payment.get("status") == "captured"
            ),
            None,
        )

        if payment_link_status == "paid":
            if not captured_payment:
                raise ValueError(
                    "Payment Link reports paid, "
                    "but no captured payment was found."
                )

            return self._process_successful_recovery(
                action=action,
                recovery_case=recovery_case,
                transaction=transaction,
                payment_link=payment_link,
                captured_payment=captured_payment,
            )

        if payment_link_status == "expired":
            action.status = "failed"
            action.result = (
                "Payment Link expired without "
                "successful recovery."
            )
            return False

        if payment_link_status == "cancelled":
            action.status = "failed"
            action.result = (
                "Payment Link was cancelled."
            )
            return False

        return False

    def _process_successful_recovery(
        self,
        action: RecoveryAction,
        recovery_case: RecoveryCase,
        transaction: Transaction,
        payment_link: dict,
        captured_payment: dict,
    ) -> bool:

        expected_amount = (
            transaction.amount
        )

        paid_amount_paise = int(
            captured_payment.get(
                "amount",
                0,
            )
        )

        paid_amount = (
            Decimal(paid_amount_paise)
            / Decimal("100")
        )

        if paid_amount != expected_amount:
            raise ValueError(
                "Recovered payment amount does not "
                "match the transaction amount."
            )

        payment_id = captured_payment.get(
            "payment_id"
        )

        if not payment_id:
            raise ValueError(
                "Captured payment is missing "
                "payment_id."
            )

        transaction.status = "captured"
        transaction.razorpay_payment_id = (
            payment_id
        )
        transaction.payment_method = (
            captured_payment.get("method")
        )

        action.status = "successful"
        action.result = (
            "Recovery payment successfully "
            "captured through Razorpay "
            "Payment Link."
        )

        action.metadata_json = json.dumps(
            {
                "provider": "razorpay",
                "payment_link_id": payment_link.get(
                    "id"
                ),
                "short_url": payment_link.get(
                    "short_url"
                ),
                "payment_link_status": payment_link.get(
                    "status"
                ),
                "payment_id": payment_id,
                "payment_status": captured_payment.get(
                    "status"
                ),
                "payment_method": captured_payment.get(
                    "method"
                ),
                "amount_paid": paid_amount_paise,
                "reference_id": payment_link.get(
                    "reference_id"
                ),
            }
        )

        recovery_case.status = "recovered"
        recovery_case.recovered_amount = (
            paid_amount
        )
        recovery_case.recovered_at = (
            datetime.now(timezone.utc)
        )

        return True