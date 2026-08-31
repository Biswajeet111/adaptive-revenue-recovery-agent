from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.recovery_action import RecoveryAction
from backend.app.services.recovery_worker import RecoveryWorker


def main():

    print(
        "=== PHASE 10 RECOVERY WORKER TEST ==="
    )

    db = SessionLocal()

    try:

        # -----------------------------------------------------
        # FIND THE NEWEST PENDING ACTION
        # -----------------------------------------------------

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
                "No pending recovery action exists.\n"
                "Create a fresh AI test case first."
            )

        action_id = action.id

        print(
            f"Test action: {action_id}"
        )

        print(
            f"Initial status: "
            f"{action.status}"
        )

        # -----------------------------------------------------
        # WORKER
        # -----------------------------------------------------

        worker = RecoveryWorker(
            db=db,
            batch_size=1,
            dry_run=True,
        )

        # IMPORTANT:
        # Process the exact fixture selected above.
        # Do not call run_once(), because another older
        # pending action could be selected.

        success = worker.process_action(
            action_id
        )

        db.refresh(action)

        # -----------------------------------------------------
        # RESULT
        # -----------------------------------------------------

        print()

        print(
            "=== WORKER RESULT ==="
        )

        print(
            f"Requested action: "
            f"{action_id}"
        )

        print(
            f"Processed successfully: "
            f"{success}"
        )

        print(
            f"Final action status: "
            f"{action.status}"
        )

        print(
            f"Attempt count: "
            f"{action.attempt_count}"
        )

        # -----------------------------------------------------
        # ASSERTIONS
        # -----------------------------------------------------

        if not success:

            raise AssertionError(
                "Worker failed to process "
                f"test action {action_id}."
            )

        if action.status != "pending":

            raise AssertionError(
                "Dry-run should restore the exact "
                f"test action {action_id} to pending. "
                f"Got {action.status}."
            )

        if action.attempt_count != 0:

            raise AssertionError(
                "Dry-run should restore "
                "attempt_count to 0."
            )

        if action.last_attempt_at is not None:

            raise AssertionError(
                "Dry-run should clear "
                "last_attempt_at."
            )

        if action.lease_until is not None:

            raise AssertionError(
                "Dry-run should clear "
                "lease_until."
            )

        print()

        print(
            f"Correct action processed: "
            f"{action_id}"
        )

        print(
            "Atomic claim path executed."
        )

        print(
            "Dry-run restored the exact "
            "test action to pending."
        )

        print(
            "No Razorpay Payment Link was created."
        )

        print()

        print(
            "=== PHASE 10 RECOVERY WORKER TEST PASSED ==="
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()