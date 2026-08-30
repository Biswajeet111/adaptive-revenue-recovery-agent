from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.recovery_policy import RecoveryPolicy


class RecoveryService:
    """
    Controls the lifecycle of recovery cases and actions.

    RecoveryService is deterministic. It does not make AI
    decisions and does not call external payment providers.
    """

    MAX_AUTOMATED_ATTEMPTS = 2

    ACTIVE_ACTION_STATUSES = {
        "pending",
        "executing",
        "executed",
    }

    TERMINAL_CASE_STATUSES = {
        "recovered",
        "closed",
    }

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.policy = RecoveryPolicy()

    # =========================================================
    # CREATE INITIAL RECOVERY CASE
    # =========================================================

    def create_case_for_transaction(
        self,
        transaction: Transaction,
    ) -> RecoveryCase:

        # -----------------------------------------------------
        # Never create another case for the same transaction.
        # -----------------------------------------------------

        existing = self.db.scalar(
            select(RecoveryCase).where(
                RecoveryCase.transaction_id
                == transaction.id
            )
        )

        if existing:
            return existing

        # -----------------------------------------------------
        # Deterministic baseline decision
        # -----------------------------------------------------

        decision = self.policy.evaluate(
            failure_code=transaction.failure_code,
            failure_reason=transaction.failure_reason,
            payment_method=transaction.payment_method,
            amount=transaction.amount,
        )

        # -----------------------------------------------------
        # Create recovery case
        # -----------------------------------------------------

        recovery_case = RecoveryCase(
            transaction_id=transaction.id,
            failure_code=transaction.failure_code,
            failure_reason=transaction.failure_reason,
            classification=decision.classification,
            recoverability=decision.recoverability,
            risk_score=decision.risk_score,
            revenue_at_risk=Decimal(
                transaction.amount
            ),
            recommended_action=(
                decision.recommended_action
            ),
            status="open",
            reason=decision.reason,
        )

        self.db.add(
            recovery_case
        )

        self.db.flush()

        # -----------------------------------------------------
        # Create first action
        # -----------------------------------------------------

        self._create_action(
            recovery_case=recovery_case,
            action_type=decision.recommended_action,
        )

        self.db.flush()

        return recovery_case

    # =========================================================
    # CREATE NEXT RECOVERY ACTION
    # =========================================================

    def create_next_recovery_action(
        self,
        recovery_case: RecoveryCase,
        action_type: str,
    ) -> RecoveryAction:

        # -----------------------------------------------------
        # 1. Terminal case protection
        # -----------------------------------------------------

        if (
            recovery_case.status
            in self.TERMINAL_CASE_STATUSES
        ):

            raise ValueError(
                f"Recovery case {recovery_case.id} "
                f"is already in terminal status "
                f"'{recovery_case.status}'. "
                "No further recovery action is allowed."
            )

        # -----------------------------------------------------
        # 2. Active action protection
        # -----------------------------------------------------

        if self.has_active_action(
            recovery_case.id
        ):

            raise ValueError(
                f"Recovery case {recovery_case.id} "
                "already has an active recovery action."
            )

        # -----------------------------------------------------
        # 3. Attempt limit
        # -----------------------------------------------------

        completed_attempts = (
            self.get_recovery_attempt_count(
                recovery_case.id
            )
        )

        if (
            completed_attempts
            >= self.MAX_AUTOMATED_ATTEMPTS
        ):

            raise ValueError(
                f"Recovery case {recovery_case.id} "
                "has reached the maximum automated "
                f"recovery attempt limit of "
                f"{self.MAX_AUTOMATED_ATTEMPTS}."
            )

        # -----------------------------------------------------
        # 4. Manual review is not an executable payment
        # -----------------------------------------------------

        if action_type == "manual_review":

            action = self._create_action(
                recovery_case=recovery_case,
                action_type="manual_review",
            )

            recovery_case.status = (
                "manual_review"
            )

            self.db.flush()

            return action

        # -----------------------------------------------------
        # 5. Validate action
        # -----------------------------------------------------

        allowed_actions = {
            "delayed_retry",
            "request_payment_method_update",
            "alternative_payment_method",
            "manual_review",
        }

        if action_type not in allowed_actions:

            raise ValueError(
                f"Unsupported recovery action: "
                f"{action_type}"
            )

        # -----------------------------------------------------
        # 6. Create action
        # -----------------------------------------------------

        action = self._create_action(
            recovery_case=recovery_case,
            action_type=action_type,
        )

        self.db.flush()

        return action

    # =========================================================
    # ATTEMPT COUNT
    # =========================================================

    def get_recovery_attempt_count(
        self,
        recovery_case_id: int,
    ) -> int:

        statement = (
            select(
                func.count(
                    RecoveryAction.id
                )
            )
            .where(
                RecoveryAction.recovery_case_id
                == recovery_case_id
            )
            .where(
                RecoveryAction.status.in_(
                    [
                        "executing",
                        "executed",
                        "successful",
                        "failed",
                    ]
                )
            )
        )

        return int(
            self.db.scalar(
                statement
            )
            or 0
        )

    # =========================================================
    # ACTIVE ACTION
    # =========================================================

    def has_active_action(
        self,
        recovery_case_id: int,
    ) -> bool:

        statement = (
            select(
                RecoveryAction
            )
            .where(
                RecoveryAction.recovery_case_id
                == recovery_case_id
            )
            .where(
                RecoveryAction.status.in_(
                    list(
                        self.ACTIVE_ACTION_STATUSES
                    )
                )
            )
        )

        return (
            self.db.scalar(
                statement
            )
            is not None
        )

    # =========================================================
    # GET CURRENT ACTION
    # =========================================================

    def get_current_action(
        self,
        recovery_case_id: int,
    ) -> RecoveryAction | None:

        statement = (
            select(
                RecoveryAction
            )
            .where(
                RecoveryAction.recovery_case_id
                == recovery_case_id
            )
            .order_by(
                RecoveryAction.id.desc()
            )
        )

        return self.db.scalar(
            statement
        )

    # =========================================================
    # INTERNAL ACTION CREATION
    # =========================================================

    def _create_action(
        self,
        recovery_case: RecoveryCase,
        action_type: str,
    ) -> RecoveryAction:

        action = RecoveryAction(
            recovery_case_id=recovery_case.id,
            action_type=action_type,
            channel=self._channel_for_action(
                action_type
            ),
            status="pending",
        )

        self.db.add(
            action
        )

        return action

    # =========================================================
    # CHANNEL MAPPING
    # =========================================================

    @staticmethod
    def _channel_for_action(
        action_type: str,
    ) -> str:

        channels = {
            "delayed_retry": "payment",
            "request_payment_method_update": "payment",
            "alternative_payment_method": "payment",
            "manual_review": "support",
        }

        return channels.get(
            action_type,
            "support",
        )