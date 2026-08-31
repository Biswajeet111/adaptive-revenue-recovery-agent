from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.recovery_action import RecoveryAction
from backend.app.services.recovery_worker import RecoveryWorker


TEST_ACTION_ID = 9


def main():

    db = SessionLocal()

    try:

        print(
            "=== PHASE 10 RETRY / LEASE TEST ==="
        )

        action = db.scalar(
            select(RecoveryAction).where(
                RecoveryAction.id == TEST_ACTION_ID
            )
        )

        if action is None:
            raise RuntimeError(
                f"Recovery Action {TEST_ACTION_ID} "
                "not found."
            )

        # -----------------------------------------------------
        # TEST 1 — RETRYABLE FAILURE
        # -----------------------------------------------------

        action.status = "executing"
        action.attempt_count = 1
        action.last_attempt_at = (
            datetime.now(timezone.utc)
        )
        action.lease_until = (
            datetime.now(timezone.utc)
            + timedelta(minutes=5)
        )

        db.commit()

        worker = RecoveryWorker(
            db=db,
            dry_run=True,
        )

        worker.handle_failure(
            TEST_ACTION_ID,
            RuntimeError(
                "Simulated temporary Razorpay failure."
            ),
        )

        db.refresh(action)

        if action.status != "pending":
            raise AssertionError(
                "Retryable failure should return "
                "action to pending."
            )

        if action.lease_until is not None:
            raise AssertionError(
                "Retryable failure should clear "
                "the worker lease."
            )

        print(
            "TEST 1 PASSED: Retryable failure "
            "returned action to pending."
        )

        # -----------------------------------------------------
        # TEST 2 — MAX ATTEMPTS
        # -----------------------------------------------------

        action.status = "executing"
        action.attempt_count = (
            worker.MAX_ATTEMPTS
        )
        action.last_attempt_at = (
            datetime.now(timezone.utc)
        )
        action.lease_until = (
            datetime.now(timezone.utc)
            + timedelta(minutes=5)
        )

        db.commit()

        worker.handle_failure(
            TEST_ACTION_ID,
            RuntimeError(
                "Simulated permanent failure."
            ),
        )

        db.refresh(action)

        if action.status != "failed":
            raise AssertionError(
                "Maximum attempts should permanently "
                "fail the action."
            )

        if action.lease_until is not None:
            raise AssertionError(
                "Permanent failure should clear "
                "the worker lease."
            )

        print(
            "TEST 2 PASSED: Maximum attempts "
            "enforced."
        )

        # -----------------------------------------------------
        # TEST 3 — STALE LEASE RECOVERY
        # -----------------------------------------------------

        action.status = "executing"
        action.attempt_count = 1
        action.last_attempt_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=10)
        )
        action.lease_until = (
            datetime.now(timezone.utc)
            - timedelta(minutes=5)
        )

        db.commit()

        recovered = (
            worker.recover_stale_actions()
        )

        db.refresh(action)

        if recovered < 1:
            raise AssertionError(
                "Expected stale action to be recovered."
            )

        if action.status != "pending":
            raise AssertionError(
                "Expired executing action should "
                "return to pending."
            )

        if action.lease_until is not None:
            raise AssertionError(
                "Recovered stale action should "
                "have no lease."
            )

        print(
            "TEST 3 PASSED: Expired worker lease "
            "returned action to pending."
        )

        # -----------------------------------------------------
        # RESTORE FIXTURE
        # -----------------------------------------------------

        action.status = "pending"
        action.attempt_count = 0
        action.last_attempt_at = None
        action.lease_until = None
        action.executed_at = None
        action.result = None

        db.commit()

        print(
            "Test action restored to clean pending state."
        )

        print()
        print(
            "=== PHASE 10 RETRY / LEASE TEST PASSED ==="
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()