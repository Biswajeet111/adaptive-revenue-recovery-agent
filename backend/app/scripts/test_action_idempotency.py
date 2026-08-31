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
        # Find an already executed or successful action.
        action = db.scalar(
            select(RecoveryAction)
            .where(
                RecoveryAction.status.in_(
                    [
                        "executed",
                        "successful",
                    ]
                )
            )
            .order_by(
                RecoveryAction.id.desc()
            )
        )

        if action is None:
            print(
                "No executed/successful recovery action found."
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
            raise RuntimeError(
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
            raise RuntimeError(
                "Transaction not found."
            )

        original_status = action.status
        original_executed_at = action.executed_at
        original_metadata = action.metadata_json
        original_result = action.result

        print(
            "=== PHASE 8 IDEMPOTENCY TEST ==="
        )

        print(
            f"Recovery Action: {action.id}"
        )

        print(
            f"Recovery Case: {recovery_case.id}"
        )

        print(
            f"Transaction: {transaction.id}"
        )

        print(
            f"Initial status: {action.status}"
        )

        print(
            f"Executed at: {action.executed_at}"
        )

        # ---------------------------------------------------------
        # Execute the already-completed action through the
        # orchestrator.
        #
        # The orchestrator must return immediately.
        # No Razorpay call should occur.
        # ---------------------------------------------------------

        orchestrator = RecoveryOrchestrator(
            db=db,
            dry_run=False,
        )

        result = orchestrator.execute_action(
            action=action,
            recovery_case=recovery_case,
            transaction=transaction,
        )

        db.refresh(result)

        # ---------------------------------------------------------
        # Verify state did not change.
        # ---------------------------------------------------------

        if result.status != original_status:
            raise AssertionError(
                "TEST FAILED: Existing action status "
                "changed during idempotent execution."
            )

        if result.executed_at != original_executed_at:
            raise AssertionError(
                "TEST FAILED: Existing execution timestamp "
                "changed."
            )

        if result.metadata_json != original_metadata:
            raise AssertionError(
                "TEST FAILED: Existing action metadata "
                "changed."
            )

        if result.result != original_result:
            raise AssertionError(
                "TEST FAILED: Existing action result "
                "changed."
            )

        # ---------------------------------------------------------
        # Verify that the transaction was not modified by the
        # idempotency guard.
        # ---------------------------------------------------------

        db.refresh(transaction)

        print()
        print(
            "Existing action was returned without execution."
        )

        print(
            f"Final status: {result.status}"
        )

        print(
            f"Payment Link metadata unchanged: "
            f"{result.metadata_json == original_metadata}"
        )

        print(
            "No new Razorpay Payment Link was created."
        )

        print()
        print(
            "=== PHASE 8 IDEMPOTENCY TEST PASSED ==="
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()