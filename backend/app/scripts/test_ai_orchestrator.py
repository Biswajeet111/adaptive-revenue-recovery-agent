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
        # =====================================================
        # 1. Find newest pending recovery action
        # =====================================================

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
            raise RuntimeError(
                "No pending recovery action found."
            )

        # =====================================================
        # 2. Find recovery case
        # =====================================================

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

        # =====================================================
        # 3. Find transaction
        # =====================================================

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

        # =====================================================
        # 4. Run orchestrator in DRY-RUN mode
        # =====================================================

        print(
            "=== PHASE 3 AI ORCHESTRATOR DRY RUN ==="
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
            f"{action.id}"
        )

        print(
            f"Initial Action Type: "
            f"{action.action_type}"
        )

        print(
            f"Initial Status: "
            f"{action.status}"
        )

        print()

        orchestrator = RecoveryOrchestrator(
            db=db,
            dry_run=True,
        )

        result = orchestrator.execute_action(
            action=action,
            recovery_case=recovery_case,
            transaction=transaction,
        )

        db.commit()

        # =====================================================
        # 5. Display result
        # =====================================================

        print(
            "=== RESULT ==="
        )

        print(
            f"Final Action Type: "
            f"{result.action_type}"
        )

        print(
            f"Final Status: "
            f"{result.status}"
        )

        print(
            f"Result: "
            f"{result.result}"
        )

        # =====================================================
        # 6. Verify dry-run safety
        # =====================================================

        if result.status != "pending":
            raise RuntimeError(
                "DRY RUN FAILED: "
                "Recovery action status changed "
                f"to '{result.status}'."
            )

        if not result.result:
            raise RuntimeError(
                "DRY RUN FAILED: "
                "No result was recorded."
            )

        if "Dry-run mode prevented" not in result.result:
            raise RuntimeError(
                "DRY RUN FAILED: "
                "Expected external execution "
                "to be prevented."
            )

        print()
        print(
            "DRY RUN PASSED."
        )

        print(
            "No Razorpay payment link was created."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()