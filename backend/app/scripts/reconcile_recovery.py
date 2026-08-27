from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.razorpay_service import RazorpayService
from backend.app.services.reconciliation_service import (
    ReconciliationService,
)


def main():
    db = SessionLocal()

    try:
        action = db.scalar(
            select(RecoveryAction)
            .where(
                RecoveryAction.status == "executed"
            )
            .order_by(
                RecoveryAction.id.asc()
            )
        )

        if action is None:
            print(
                "No executed recovery action "
                "requires reconciliation."
            )
            return

        recovery_case = db.scalar(
            select(RecoveryCase)
            .where(
                RecoveryCase.id
                == action.recovery_case_id
            )
        )

        if recovery_case is None:
            raise ValueError(
                "Recovery case not found."
            )

        transaction = db.scalar(
            select(Transaction)
            .where(
                Transaction.id
                == recovery_case.transaction_id
            )
        )

        if transaction is None:
            raise ValueError(
                "Transaction not found."
            )

        print(
            f"Reconciling action {action.id} "
            f"for transaction {transaction.id}"
        )

        service = ReconciliationService(
            RazorpayService()
        )

        recovered = service.reconcile_payment_link(
            action=action,
            recovery_case=recovery_case,
            transaction=transaction,
        )

        db.commit()

        if recovered:
            print(
                "Recovery successfully confirmed."
            )
            print(
                f"Recovered amount: "
                f"₹{recovery_case.recovered_amount}"
            )
            print(
                f"Transaction status: "
                f"{transaction.status}"
            )
            print(
                f"Recovery case status: "
                f"{recovery_case.status}"
            )
            print(
                f"Recovery action status: "
                f"{action.status}"
            )
        else:
            print(
                "Recovery has not been confirmed."
            )
            print(
                f"Payment action status: "
                f"{action.status}"
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()