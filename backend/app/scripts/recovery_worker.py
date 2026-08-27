from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.recovery_orchestrator import (
    RecoveryOrchestrator,
)


def claim_pending_action(db):
    statement = (
        select(RecoveryAction)
        .where(
            RecoveryAction.status == "pending"
        )
        .order_by(RecoveryAction.id.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )

    return db.scalar(statement)


def process_one_action() -> bool:
    db = SessionLocal()

    try:
        action = claim_pending_action(db)

        if action is None:
            db.rollback()
            return False

        recovery_case = db.scalar(
            select(RecoveryCase).where(
                RecoveryCase.id
                == action.recovery_case_id
            )
        )

        if recovery_case is None:
            action.status = "failed"
            action.result = (
                "Recovery case not found."
            )
            db.commit()
            return True

        transaction = db.scalar(
            select(Transaction).where(
                Transaction.id
                == recovery_case.transaction_id
            )
        )

        if transaction is None:
            action.status = "failed"
            action.result = (
                "Transaction not found."
            )
            db.commit()
            return True

        print(
            f"Claimed recovery action "
            f"{action.id} "
            f"for transaction "
            f"{transaction.id}"
        )

        orchestrator = RecoveryOrchestrator(db)

        try:
            orchestrator.execute_action(
                action=action,
                recovery_case=recovery_case,
                transaction=transaction,
            )

            db.commit()

            print(
                f"Recovery action {action.id} "
                f"completed with status: "
                f"{action.status}"
            )

        except Exception as exc:
            db.rollback()

            # The execution failure has to be persisted
            # in a separate transaction.
            failure_db = SessionLocal()

            try:
                failed_action = failure_db.scalar(
                    select(RecoveryAction).where(
                        RecoveryAction.id
                        == action.id
                    )
                )

                if failed_action is not None:
                    failed_action.status = "failed"
                    failed_action.result = (
                        f"Recovery execution failed: "
                        f"{exc}"
                    )

                    failure_db.commit()

            finally:
                failure_db.close()

            print(
                f"Recovery action {action.id} "
                f"failed: {exc}"
            )

        return True

    finally:
        db.close()


def main():
    print(
        "Recovery worker started."
    )

    processed = process_one_action()

    if not processed:
        print(
            "No pending recovery actions found."
        )

    print(
        "Recovery worker finished."
    )


if __name__ == "__main__":
    main()