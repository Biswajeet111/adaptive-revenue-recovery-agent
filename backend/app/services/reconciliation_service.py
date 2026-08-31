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
        # WEBHOOK PAYMENT DATA
        # -------------------------------------------------

        if payment is not None:

            if payment_link is None:
                payment_link = {
                    "id": payment_link_id,
                    "status": "paid",
                    "reference_id": metadata.get(
                        "reference_id"
                    ),
                }

            # -------------------------------------------------
            # FULL PAYMENT LINK PAYMENT
            # -------------------------------------------------

            if (
                payment_link.get("status")
                == "paid"
            ):
                if payment.get("status") != "captured":
                    raise ValueError(
                        "Payment Link reported paid, "
                        "but webhook payment is not captured."
                    )

                return self._process_successful_recovery(
                    action=action,
                    recovery_case=recovery_case,
                    transaction=transaction,
                    payment_link=payment_link,
                    captured_payment=payment,
                )

            # -------------------------------------------------
            # PARTIAL PAYMENT LINK PAYMENT
            # -------------------------------------------------

            if (
                payment_link.get("status")
                == "partially_paid"
            ):
                return self._process_partial_recovery(
                    action=action,
                    recovery_case=recovery_case,
                    transaction=transaction,
                    payment_link=payment_link,
                    payment=payment,
                )

            raise ValueError(
                "Unsupported Payment Link status "
                f"for webhook reconciliation: "
                f"{payment_link.get('status')}"
            )

        # -------------------------------------------------
        # FALLBACK TO RAZORPAY API
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

        if payment_link_status == "partially_paid":

            partial_payment = next(
                (
                    item
                    for item in payments
                    if item.get("status")
                    in {
                        "captured",
                        "authorized",
                    }
                ),
                None,
            )

            if not partial_payment:
                return False

            return self._process_partial_recovery(
                action=action,
                recovery_case=recovery_case,
                transaction=transaction,
                payment_link=payment_link,
                payment=partial_payment,
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

    # =========================================================
    # PARTIAL RECOVERY
    # =========================================================

    def _process_partial_recovery(
        self,
        action: RecoveryAction,
        recovery_case: RecoveryCase,
        transaction: Transaction,
        payment_link: dict,
        payment: dict,
    ) -> bool:

        payment_id = payment.get("id")

        if not payment_id:
            payment_id = payment.get(
                "payment_id"
            )

        if not payment_id:
            raise ValueError(
                "Partial payment is missing "
                "payment_id."
            )

        amount_paise = int(
            payment.get(
                "amount",
                0,
            )
        )

        if amount_paise <= 0:
            raise ValueError(
                "Partial payment amount must "
                "be greater than zero."
            )

        partial_amount = (
            Decimal(amount_paise)
            / Decimal("100")
        )

        expected_amount = Decimal(
            str(transaction.amount)
        )

        existing_recovered = (
            Decimal(
                str(
                    recovery_case.recovered_amount
                    or Decimal("0.00")
                )
            )
        )

        cumulative_recovered = (
            existing_recovered
            + partial_amount
        )

        if cumulative_recovered > expected_amount:
            raise ValueError(
                "Cumulative recovered amount "
                "cannot exceed transaction amount. "
                f"Transaction: {expected_amount}, "
                f"recovered: {cumulative_recovered}."
            )

        # -------------------------------------------------
        # FULL RECOVERY THROUGH CUMULATIVE PAYMENTS
        # -------------------------------------------------

        if cumulative_recovered == expected_amount:

            transaction.status = "captured"

            transaction.razorpay_payment_id = (
                payment_id
            )

            transaction.payment_method = (
                payment.get("method")
            )

            transaction.failure_code = None
            transaction.failure_reason = None

            action.status = "successful"

            action.executed_at = (
                action.executed_at
                or datetime.now(timezone.utc)
            )

            action.result = (
                "Recovery completed through "
                "cumulative Payment Link payments."
            )

            action.metadata_json = json.dumps(
                {
                    "provider": "razorpay",
                    "payment_link_id": (
                        payment_link.get("id")
                    ),
                    "payment_id": payment_id,
                    "payment_status": (
                        payment.get("status")
                    ),
                    "payment_method": (
                        payment.get("method")
                    ),
                    "amount_paid": amount_paise,
                    "cumulative_recovered": (
                        int(cumulative_recovered * 100)
                    ),
                    "reference_id": (
                        payment_link.get(
                            "reference_id"
                        )
                    ),
                }
            )

            recovery_case.recovered_amount = (
                cumulative_recovered
            )

            recovery_case.status = "recovered"

            recovery_case.recovered_at = (
                recovery_case.recovered_at
                or datetime.now(timezone.utc)
            )

            return True

        # -------------------------------------------------
        # PARTIAL RECOVERY
        # -------------------------------------------------

        recovery_case.recovered_amount = (
            cumulative_recovered
        )

        recovery_case.status = "open"

        recovery_case.recovered_at = None

        action.status = "pending"

        action.result = (
            "Payment Link was partially paid. "
            f"Recovered {cumulative_recovered:.2f} "
            f"of {expected_amount:.2f}; "
            f"remaining "
            f"{expected_amount - cumulative_recovered:.2f}."
        )

        action.metadata_json = json.dumps(
            {
                "provider": "razorpay",
                "payment_link_id": (
                    payment_link.get("id")
                ),
                "payment_id": payment_id,
                "payment_status": (
                    payment.get("status")
                ),
                "payment_method": (
                    payment.get("method")
                ),
                "last_payment_amount": amount_paise,
                "cumulative_recovered": (
                    int(cumulative_recovered * 100)
                ),
                "remaining_amount": (
                    int(
                        (
                            expected_amount
                            - cumulative_recovered
                        )
                        * 100
                    )
                ),
                "reference_id": (
                    payment_link.get(
                        "reference_id"
                    )
                ),
            }
        )

        return False

    # =========================================================
    # FULL RECOVERY
    # =========================================================

    def _process_successful_recovery(
        self,
        action: RecoveryAction,
        recovery_case: RecoveryCase,
        transaction: Transaction,
        payment_link: dict,
        captured_payment: dict,
    ) -> bool:

        if captured_payment.get(
            "status"
        ) != "captured":

            raise ValueError(
                "Recovery payment is not captured."
            )

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

        payment_id = captured_payment.get(
            "id"
        )

        if not payment_id:
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

        transaction.failure_code = None
        transaction.failure_reason = None

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
                "cumulative_recovered": (
                    paid_amount_paise
                ),
                "remaining_amount": 0,
                "reference_id": (
                    payment_link.get(
                        "reference_id"
                    )
                ),
            }
        )

        recovery_case.status = "recovered"

        recovery_case.recovered_amount = (
            paid_amount
        )

        recovery_case.recovered_at = (
            recovery_case.recovered_at
            or datetime.now(timezone.utc)
        )

        return True