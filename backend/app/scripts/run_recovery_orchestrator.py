from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.recovery_orchestrator import (
    RecoveryOrchestrator,
)


def main():
    db = SessionLocal()

    try:
        action = db.scalar(
            select(RecoveryAction)
            .where(
                RecoveryAction.status == "pending"
            )
            .order_by(RecoveryAction.id.asc())
        )

        if action is None:
            print("No pending recovery action found.")
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
            f"Executing recovery action "
            f"{action.id} for transaction "
            f"{transaction.id}"
        )

        orchestrator = RecoveryOrchestrator(db)

        orchestrator.execute_action(
            action=action,
            recovery_case=recovery_case,
            transaction=transaction,
        )

        db.commit()

        print(
            "Recovery orchestration completed."
        )
        print(
            f"Action status: {action.status}"
        )
        print(
            f"Result: {action.result}"
        )
        print(
            f"Metadata: {action.metadata_json}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()