from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.recovery_action import RecoveryAction
from backend.app.services.recovery_orchestrator import (
    RecoveryOrchestrator,
)


def main():
    db = SessionLocal()

    try:
        # ---------------------------------------------------------
        # Find a pending action
        # ---------------------------------------------------------

        action = db.scalar(
            select(RecoveryAction)
            .where(
                RecoveryAction.status == "pending"
            )
            .order_by(
                RecoveryAction.id.asc()
            )
        )

        if action is None:
            print(
                "No pending recovery action exists."
            )
            print(
                "Create a fresh AI test case first."
            )
            return

        action_id = action.id

        print(
            "=== PHASE 8 ATOMIC ACTION CLAIM TEST ==="
        )

        print(
            f"Testing Recovery Action: {action_id}"
        )

        print(
            f"Initial status: {action.status}"
        )

        # ---------------------------------------------------------
        # Create orchestrator
        # ---------------------------------------------------------

        orchestrator = RecoveryOrchestrator(
            db=db,
            dry_run=True,
        )

        # ---------------------------------------------------------
        # Worker A claims action
        # ---------------------------------------------------------

        worker_a = orchestrator._claim_action(
            action
        )

        if not worker_a:
            raise AssertionError(
                "TEST FAILED: Worker A could not "
                "claim the pending action."
            )

        db.commit()

        db.refresh(action)

        print(
            "Worker A claim: SUCCESS"
        )

        print(
            f"Status after Worker A: "
            f"{action.status}"
        )

        if action.status != "executing":
            raise AssertionError(
                "TEST FAILED: Action did not transition "
                "from pending to executing."
            )

        # ---------------------------------------------------------
        # Worker B attempts same action
        # ---------------------------------------------------------

        worker_b = orchestrator._claim_action(
            action
        )

        if worker_b:
            raise AssertionError(
                "TEST FAILED: Worker B incorrectly "
                "claimed an already executing action."
            )

        db.rollback()

        db.refresh(action)

        print(
            "Worker B claim: REJECTED"
        )

        print(
            f"Final status: {action.status}"
        )

        if action.status != "executing":
            raise AssertionError(
                "TEST FAILED: Action state changed "
                "unexpectedly after Worker B attempt."
            )

        # ---------------------------------------------------------
        # Confirm no duplicate execution timestamp
        # ---------------------------------------------------------

        if action.executed_at is not None:
            raise AssertionError(
                "TEST FAILED: Action received an "
                "execution timestamp during claim."
            )

        # ---------------------------------------------------------
        # Restore test action to pending
        #
        # This is important because this script does not execute
        # Razorpay. It leaves the database clean for the next test.
        # ---------------------------------------------------------

        action.status = "pending"

        db.commit()

        db.refresh(action)

        if action.status != "pending":
            raise AssertionError(
                "TEST FAILED: Could not restore "
                "test action to pending state."
            )

        print()
        print(
            "=== PHASE 8 ATOMIC CLAIM TEST PASSED ==="
        )

        print(
            "Worker A: pending -> executing"
        )

        print(
            "Worker B: rejected"
        )

        print(
            "No Razorpay execution occurred."
        )

        print(
            "Test action restored to pending."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()