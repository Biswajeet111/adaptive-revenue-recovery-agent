import threading

from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.recovery_action import RecoveryAction
from backend.app.services.recovery_worker import RecoveryWorker


TEST_ACTION_ID = 9


def claim_worker(
    worker_name: str,
    barrier: threading.Barrier,
    results: list,
):

    db = SessionLocal()

    try:

        worker = RecoveryWorker(
            db=db,
            batch_size=1,
            dry_run=True,
        )

        barrier.wait()

        action = worker.claim_action(
            TEST_ACTION_ID
        )

        if action is None:

            results.append(
                (
                    worker_name,
                    "REJECTED",
                )
            )

            return

        results.append(
            (
                worker_name,
                "CLAIMED",
            )
        )

    except Exception as exc:

        results.append(
            (
                worker_name,
                f"ERROR: {exc}",
            )
        )

    finally:
        db.close()


def main():

    db = SessionLocal()

    try:

        print(
            "=== PHASE 10 CONCURRENT WORKER TEST ==="
        )

        action = db.scalar(
            select(RecoveryAction).where(
                RecoveryAction.id
                == TEST_ACTION_ID
            )
        )

        if action is None:
            raise RuntimeError(
                f"Recovery Action {TEST_ACTION_ID} "
                "not found."
            )

        # Ensure a clean fixture.

        action.status = "pending"
        action.executed_at = None
        action.result = None

        db.commit()

        print(
            f"Testing Recovery Action: "
            f"{TEST_ACTION_ID}"
        )

        print(
            f"Initial status: "
            f"{action.status}"
        )

    finally:
        db.close()

    barrier = threading.Barrier(2)

    results = []

    worker_a = threading.Thread(
        target=claim_worker,
        args=(
            "Worker A",
            barrier,
            results,
        ),
    )

    worker_b = threading.Thread(
        target=claim_worker,
        args=(
            "Worker B",
            barrier,
            results,
        ),
    )

    worker_a.start()
    worker_b.start()

    worker_a.join()
    worker_b.join()

    print()

    for worker_name, result in results:

        print(
            f"{worker_name}: {result}"
        )

    claimed = [
        worker
        for worker, result in results
        if result == "CLAIMED"
    ]

    rejected = [
        worker
        for worker, result in results
        if result == "REJECTED"
    ]

    if len(claimed) != 1:

        raise AssertionError(
            "Expected exactly one worker "
            f"to claim the action. "
            f"Claimed: {claimed}"
        )

    if len(rejected) != 1:

        raise AssertionError(
            "Expected exactly one worker "
            f"to be rejected. "
            f"Rejected: {rejected}"
        )

    db = SessionLocal()

    try:

        action = db.scalar(
            select(RecoveryAction).where(
                RecoveryAction.id
                == TEST_ACTION_ID
            )
        )

        print()

        print(
            f"Final database status: "
            f"{action.status}"
        )

        if action.status != "executing":

            raise AssertionError(
                "Successfully claimed action "
                "must remain executing."
            )

        print(
            "Exactly one worker owns the action."
        )

        # Restore fixture.

        action.status = "pending"
        action.executed_at = None
        action.result = None

        db.commit()

        print(
            "Test action restored to pending."
        )

        print()

        print(
            "=== PHASE 10 CONCURRENT WORKER TEST PASSED ==="
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()