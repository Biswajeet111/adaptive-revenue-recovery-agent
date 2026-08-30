from datetime import datetime
from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.models.transaction import Transaction
from backend.app.services.recovery_service import RecoveryService


def main():
    db = SessionLocal()

    try:
        # =====================================================
        # Generate a unique synthetic order ID
        # =====================================================

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        test_order_id = (
            f"AI_TEST_BANK_DECLINED_{timestamp}"
        )

        # =====================================================
        # Create failed transaction
        # =====================================================

        transaction = Transaction(
            razorpay_order_id=test_order_id,
            razorpay_payment_id=None,
            amount=Decimal("100.00"),
            currency="INR",
            status="failed",
            payment_method="netbanking",
            failure_code="BANK_DECLINED",
            failure_reason=(
                "The payment was declined by "
                "the issuing bank."
            ),
        )

        db.add(transaction)
        db.flush()

        # =====================================================
        # Create recovery case + initial action
        # =====================================================

        recovery_service = RecoveryService(
            db
        )

        recovery_case = (
            recovery_service
            .create_case_for_transaction(
                transaction
            )
        )

        action = (
            recovery_service
            .get_current_action(
                recovery_case.id
            )
        )

        db.commit()

        # =====================================================
        # Output
        # =====================================================

        print(
            "AI test case created successfully."
        )

        print(
            f"Transaction ID: "
            f"{transaction.id}"
        )

        print(
            f"Test Order ID: "
            f"{transaction.razorpay_order_id}"
        )

        print(
            f"Recovery Case ID: "
            f"{recovery_case.id}"
        )

        if action:
            print(
                f"Recovery Action ID: "
                f"{action.id}"
            )

            print(
                f"Initial Action Type: "
                f"{action.action_type}"
            )

            print(
                f"Initial Action Status: "
                f"{action.status}"
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()