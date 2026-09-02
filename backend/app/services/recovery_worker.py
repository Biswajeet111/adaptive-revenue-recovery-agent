import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.recovery_orchestrator import (
    RecoveryOrchestrator,
)


class RecoveryWorker:
    LEASE_SECONDS = 300
    MAX_ATTEMPTS = 3

    def __init__(
        self,
        db: Session,
        batch_size: int = 10,
        dry_run: bool = False,
    ):
        self.db = db
        self.batch_size = batch_size
        self.dry_run = dry_run

    # =========================================================
    # RECOVER STALE ACTIONS
    # =========================================================

    def recover_stale_actions(self) -> int:
        """
        Recover actions whose worker lease has expired.

        If the action has already exhausted its retry budget,
        it is permanently failed instead of being returned to
        the pending queue.
        """
        now = datetime.now(timezone.utc)

        statement = (
            update(RecoveryAction)
            .where(
                RecoveryAction.status == "executing",
                RecoveryAction.lease_until.is_not(None),
                RecoveryAction.lease_until < now,
            )
            .values(
                status="pending",
                lease_until=None,
            )
        )

        result = self.db.execute(statement)

        self.db.commit()

        pending_recovered = result.rowcount

        # -----------------------------------------------------
        # SAFETY: stale actions that exhausted retries must
        # never be returned to the executable queue.
        # -----------------------------------------------------

        exhausted_statement = (
            update(RecoveryAction)
            .where(
                RecoveryAction.status == "pending",
                RecoveryAction.attempt_count >= self.MAX_ATTEMPTS,
            )
            .values(
                status="failed",
                lease_until=None,
                result=(
                    "Recovery action permanently failed after "
                    f"{self.MAX_ATTEMPTS} attempts. "
                    "Worker lease expired after the final attempt."
                ),
            )
        )

        exhausted_result = self.db.execute(
            exhausted_statement
        )

        self.db.commit()

        return pending_recovered - exhausted_result.rowcount

    # =========================================================
    # DISCOVER PENDING ACTIONS
    # =========================================================

    def get_pending_action_ids(self) -> list[int]:
        now = datetime.now(timezone.utc)

        statement = (
            select(RecoveryAction.id)
            .where(
                RecoveryAction.status == "pending"
            )
            .where(
                (
                    RecoveryAction.scheduled_at.is_(None)
                )
                |
                (
                    RecoveryAction.scheduled_at <= now
                )
            )
            .where(
                RecoveryAction.attempt_count < self.MAX_ATTEMPTS
            )
            .order_by(
                RecoveryAction.id.asc()
            )
            .limit(self.batch_size)
        )

        return list(
            self.db.scalars(statement).all()
        )

    # =========================================================
    # ATOMIC CLAIM
    # =========================================================

    def claim_action(
        self,
        action_id: int,
    ) -> RecoveryAction | None:
        now = datetime.now(timezone.utc)

        lease_until = (
            now
            + timedelta(
                seconds=self.LEASE_SECONDS
            )
        )

        statement = (
            update(RecoveryAction)
            .where(
                RecoveryAction.id == action_id,
                RecoveryAction.status == "pending",
                RecoveryAction.attempt_count
                < self.MAX_ATTEMPTS,
            )
            .values(
                status="executing",
                attempt_count=(
                    RecoveryAction.attempt_count + 1
                ),
                last_attempt_at=now,
                lease_until=lease_until,
            )
            .returning(
                RecoveryAction.id
            )
        )

        claimed_id = self.db.scalar(
            statement
        )

        if claimed_id is None:
            self.db.rollback()
            return None

        self.db.commit()

        return self.db.scalar(
            select(RecoveryAction).where(
                RecoveryAction.id == claimed_id
            )
        )

    # =========================================================
    # FAILURE HANDLING
    # =========================================================

    def handle_failure(
        self,
        action_id: int,
        error: Exception,
    ) -> None:
        action = self.db.scalar(
            select(RecoveryAction).where(
                RecoveryAction.id == action_id
            )
        )

        if action is None:
            return

        action.lease_until = None

        if action.attempt_count >= self.MAX_ATTEMPTS:
            action.status = "failed"

            action.result = (
                "Recovery action permanently failed "
                f"after {action.attempt_count} attempts: "
                f"{error}"
            )

        else:
            action.status = "pending"

            action.result = (
                "Recovery action failed and will "
                f"be retried. Attempt "
                f"{action.attempt_count} of "
                f"{self.MAX_ATTEMPTS}: {error}"
            )

        self.db.commit()

    # =========================================================
    # PROCESS ONE ACTION
    # =========================================================

    def process_action(
        self,
        action_id: int,
    ) -> bool:
        action = self.claim_action(
            action_id
        )

        if action is None:
            print(
                f"Action {action_id} was already "
                "claimed by another worker."
            )

            return False

        print(
            f"Worker claimed recovery action "
            f"{action_id}"
        )

        recovery_case = self.db.scalar(
            select(RecoveryCase).where(
                RecoveryCase.id
                == action.recovery_case_id
            )
        )

        if recovery_case is None:
            self.handle_failure(
                action_id,
                ValueError(
                    "Recovery case not found."
                ),
            )

            return False

        transaction = self.db.scalar(
            select(Transaction).where(
                Transaction.id
                == recovery_case.transaction_id
            )
        )

        if transaction is None:
            self.handle_failure(
                action_id,
                ValueError(
                    "Transaction not found."
                ),
            )

            return False

        execution_started = time.perf_counter()

        try:
            orchestrator = RecoveryOrchestrator(
                db=self.db,
                dry_run=self.dry_run,
            )

            print(
                f"Worker executing recovery "
                f"action {action_id}"
            )

            orchestrator.execute_action(
                action=action,
                recovery_case=recovery_case,
                transaction=transaction,
                already_claimed=True,
            )

            execution_duration = (
                time.perf_counter()
                - execution_started
            )

            if self.dry_run:
                action.status = "pending"

                action.attempt_count = max(
                    0,
                    action.attempt_count - 1,
                )

                action.last_attempt_at = None
                action.lease_until = None

            else:
                action.lease_until = None

            self.db.commit()

            print(
                f"Recovery action {action_id} "
                "completed successfully."
            )

            print(
                f"Execution duration: "
                f"{execution_duration:.3f}s"
            )

            return True

        except Exception as exc:
            execution_duration = (
                time.perf_counter()
                - execution_started
            )

            self.db.rollback()

            self.handle_failure(
                action_id,
                exc,
            )

            print(
                f"Recovery action {action_id} "
                f"failed: {exc}"
            )

            print(
                f"Execution duration: "
                f"{execution_duration:.3f}s"
            )

            return False

    # =========================================================
    # ONE WORKER CYCLE
    # =========================================================

    def run_once(self) -> dict:
        cycle_started = time.perf_counter()

        try:
            stale_recovered = (
                self.recover_stale_actions()
            )

            action_ids = (
                self.get_pending_action_ids()
            )

        except Exception as exc:
            self.db.rollback()

            cycle_duration = (
                time.perf_counter()
                - cycle_started
            )

            print(
                "Worker cycle failed during "
                f"discovery/recovery: {exc}"
            )

            return {
                "found": 0,
                "stale_recovered": 0,
                "claimed": 0,
                "processed": 0,
                "failed": 0,
                "duration_seconds": round(
                    cycle_duration,
                    3,
                ),
                "error": str(exc),
            }

        claimed = 0
        processed = 0
        failed = 0

        for action_id in action_ids:
            print(
                f"Worker attempting to process "
                f"recovery action {action_id}"
            )

            success = self.process_action(
                action_id
            )

            if success:
                claimed += 1
                processed += 1

            else:
                action = self.db.scalar(
                    select(RecoveryAction).where(
                        RecoveryAction.id == action_id
                    )
                )

                if (
                    action is not None
                    and action.status == "failed"
                ):
                    failed += 1

        cycle_duration = (
            time.perf_counter()
            - cycle_started
        )

        result = {
            "found": len(action_ids),
            "stale_recovered": stale_recovered,
            "claimed": claimed,
            "processed": processed,
            "failed": failed,
            "duration_seconds": round(
                cycle_duration,
                3,
            ),
        }

        return result