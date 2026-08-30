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
        payment: dict | None = None,
        payment_link: dict | None = None,
    ) -> bool:

        # -------------------------------------------------
        # IDEMPOTENCY
        # -------------------------------------------------

        if action.status == "successful":

            if recovery_case.status != "recovered":
                recovery_case.status = "recovered"

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

        try:
            metadata = json.loads(
                action.metadata_json
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid metadata for recovery "
                f"action {action.id}."
            ) from exc

        payment_link_id = metadata.get(
            "payment_link_id"
        )

        if not payment_link_id:
            raise ValueError(
                "Payment Link ID missing from "
                "recovery action metadata."
            )

        # -------------------------------------------------
        # IF WEBHOOK PROVIDED PAYMENT DATA
        # -------------------------------------------------
        #
        # payment_link.paid contains:
        #
        # payload.payment.entity
        # payload.payment_link.entity
        #
        # This is the authoritative webhook payload.
        #
        # Avoid an unnecessary Razorpay API call.
        # -------------------------------------------------

        if payment is not None:

            if payment.get("status") != "captured":
                raise ValueError(
                    "Payment Link reported paid, "
                    "but webhook payment is not captured."
                )

            if payment_link is None:
                payment_link = {
                    "id": payment_link_id,
                    "status": "paid",
                    "reference_id": metadata.get(
                        "reference_id"
                    ),
                }

            return self._process_successful_recovery(
                action=action,
                recovery_case=recovery_case,
                transaction=transaction,
                payment_link=payment_link,
                captured_payment=payment,
            )

        # -------------------------------------------------
        # FALLBACK TO RAZORPAY API
        # -------------------------------------------------
        #
        # This supports manual reconciliation or cases
        # where the webhook does not contain payment data.
        # -------------------------------------------------

        payment_link = (
            self.razorpay.fetch_payment_link(
                payment_link_id
            )
        )

        payment_link_status = (
            payment_link.get("status")
        )

        payments = payment_link.get(
            "payments",
            [],
        )

        captured_payment = next(
            (
                item
                for item in payments
                if item.get("status")
                == "captured"
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

        # -------------------------------------------------
        # VALIDATE PAYMENT STATUS
        # -------------------------------------------------

        if captured_payment.get("status") != "captured":

            raise ValueError(
                "Recovery payment is not captured."
            )

        # -------------------------------------------------
        # VALIDATE AMOUNT
        # -------------------------------------------------

        expected_amount = Decimal(
            str(transaction.amount)
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
                "match the transaction amount. "
                f"Expected {expected_amount}, "
                f"received {paid_amount}."
            )

        # -------------------------------------------------
        # VALIDATE PAYMENT ID
        # -------------------------------------------------

        payment_id = captured_payment.get(
            "id"
        )

        # Some Razorpay API responses may use payment_id.
        if not payment_id:
            payment_id = captured_payment.get(
                "payment_id"
            )

        if not payment_id:

            raise ValueError(
                "Captured payment is missing "
                "payment_id."
            )

        # -------------------------------------------------
        # UPDATE ORIGINAL TRANSACTION
        # -------------------------------------------------

        transaction.status = "captured"

        transaction.razorpay_payment_id = (
            payment_id
        )

        transaction.payment_method = (
            captured_payment.get("method")
        )

        # The original failure has already been
        # preserved in RecoveryCase and audit history.

        transaction.failure_code = None
        transaction.failure_reason = None

        # -------------------------------------------------
        # UPDATE RECOVERY ACTION
        # -------------------------------------------------

        action.status = "successful"

        action.executed_at = (
            action.executed_at
            or datetime.now(timezone.utc)
        )

        action.result = (
            "Recovery payment successfully "
            "captured through Razorpay "
            "Payment Link."
        )

        action.metadata_json = json.dumps(
            {
                "provider": "razorpay",
                "payment_link_id": (
                    payment_link.get("id")
                ),
                "short_url": (
                    payment_link.get("short_url")
                ),
                "payment_link_status": (
                    payment_link.get("status")
                ),
                "payment_id": payment_id,
                "payment_status": (
                    captured_payment.get(
                        "status"
                    )
                ),
                "payment_method": (
                    captured_payment.get(
                        "method"
                    )
                ),
                "amount_paid": paid_amount_paise,
                "reference_id": (
                    payment_link.get(
                        "reference_id"
                    )
                ),
            }
        )

        # -------------------------------------------------
        # UPDATE RECOVERY CASE
        # -------------------------------------------------

        recovery_case.status = "recovered"

        recovery_case.recovered_amount = (
            paid_amount
        )

        recovery_case.recovered_at = (
            recovery_case.recovered_at
            or datetime.now(timezone.utc)
        )

        return True