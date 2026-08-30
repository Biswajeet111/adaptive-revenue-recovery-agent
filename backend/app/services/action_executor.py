import json
import time
from datetime import datetime, timezone

from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.razorpay_service import RazorpayService


class RecoveryActionExecutor:

    SUPPORTED_ACTIONS = {
        "alternative_payment_method",
    }

    def __init__(
        self,
        razorpay_service: RazorpayService,
    ):
        self.razorpay = razorpay_service

    def execute(
        self,
        action: RecoveryAction,
        recovery_case: RecoveryCase,
        transaction: Transaction,
    ) -> RecoveryAction:

        if action.status != "pending":
            raise ValueError(
                f"Action {action.id} is not pending."
            )

        if action.action_type not in self.SUPPORTED_ACTIONS:
            raise ValueError(
                f"Unsupported action type: "
                f"{action.action_type}"
            )

        amount_paise = int(
            transaction.amount * 100
        )

        reference_id = (
            f"RR-{transaction.id}-{int(time.time())}"
        )

        description = (
            f"Payment recovery for transaction "
            f"{transaction.razorpay_order_id}"
        )

        expire_by = int(time.time()) + (
            24 * 60 * 60
        )

        action.status = "executing"

        try:
            payment_link = (
                self.razorpay.create_payment_link(
                    amount=amount_paise,
                    currency=transaction.currency,
                    reference_id=reference_id,
                    description=description,
                    expire_by=expire_by,
                )
            )

            action.status = "executed"

            action.executed_at = datetime.now(
                timezone.utc
            )

            action.result = (
                "Razorpay Payment Link created successfully."
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
                    "status": (
                        payment_link.get("status")
                    ),
                    "reference_id": (
                        payment_link.get("reference_id")
                    ),
                    "expire_by": (
                        payment_link.get("expire_by")
                    ),
                }
            )

            return action

        except Exception as exc:

            action.status = "failed"

            action.result = (
                f"Payment Link creation failed: {exc}"
            )

            raise