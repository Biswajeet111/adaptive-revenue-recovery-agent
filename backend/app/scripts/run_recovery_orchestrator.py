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
        # ---------------------------------------------------------
        # Select the newest pending recovery action
        # ---------------------------------------------------------

        action = db.scalar(
            select(RecoveryAction)
            .where(
                RecoveryAction.status == "pending"
            )
            .order_by(
                RecoveryAction.id.desc()
            )
        )

        if action is None:
            print(
                "No pending recovery action found."
            )
            return

        # ---------------------------------------------------------
        # Load recovery case
        # ---------------------------------------------------------

        recovery_case = db.scalar(
            select(RecoveryCase)
            .where(
                RecoveryCase.id
                == action.recovery_case_id
            )
        )

        if recovery_case is None:
            raise ValueError(
                f"Recovery case {action.recovery_case_id} "
                "not found."
            )

        # ---------------------------------------------------------
        # Load transaction
        # ---------------------------------------------------------

        transaction = db.scalar(
            select(Transaction)
            .where(
                Transaction.id
                == recovery_case.transaction_id
            )
        )

        if transaction is None:
            raise ValueError(
                f"Transaction "
                f"{recovery_case.transaction_id} "
                "not found."
            )

        # ---------------------------------------------------------
        # Display selected recovery target
        # ---------------------------------------------------------

        print(
            "=== RECOVERY ORCHESTRATOR ==="
        )

        print(
            f"Transaction: "
            f"{transaction.id}"
        )

        print(
            f"Razorpay Order ID: "
            f"{transaction.razorpay_order_id}"
        )

        print(
            f"Recovery Case: "
            f"{recovery_case.id}"
        )

        print(
            f"Recovery Action: "
            f"{action.id}"
        )

        print(
            f"Action Type: "
            f"{action.action_type}"
        )

        print(
            f"Action Status: "
            f"{action.status}"
        )

        print()

        # ---------------------------------------------------------
        # Safety confirmation
        # ---------------------------------------------------------

        if recovery_case.status in {
            "recovered",
            "closed",
        }:
            print(
                "Recovery case is already in a "
                f"terminal state: {recovery_case.status}"
            )
            return

        if transaction.status in {
            "captured",
            "paid",
            "successful",
        }:
            print(
                "Transaction is already in a "
                f"terminal payment state: "
                f"{transaction.status}"
            )
            return

        # ---------------------------------------------------------
        # Execute orchestrator
        # ---------------------------------------------------------

        print(
            "Starting AI recovery orchestration..."
        )

        orchestrator = RecoveryOrchestrator(
            db=db,
            dry_run=False,
        )

        executed_action = (
            orchestrator.execute_action(
                action=action,
                recovery_case=recovery_case,
                transaction=transaction,
            )
        )

        db.commit()

        # ---------------------------------------------------------
        # Result
        # ---------------------------------------------------------

        print()
        print(
            "=== RECOVERY ORCHESTRATION COMPLETED ==="
        )

        print(
            f"Transaction: "
            f"{transaction.id}"
        )

        print(
            f"Recovery Case: "
            f"{recovery_case.id}"
        )

        print(
            f"Recovery Action: "
            f"{executed_action.id}"
        )

        print(
            f"Action Type: "
            f"{executed_action.action_type}"
        )

        print(
            f"Action Status: "
            f"{executed_action.status}"
        )

        print(
            f"Result: "
            f"{executed_action.result}"
        )

        print(
            f"Metadata: "
            f"{executed_action.metadata_json}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()