from sqlalchemy.orm import Session

from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.action_executor import (
    RecoveryActionExecutor,
)
from backend.app.services.razorpay_service import (
    RazorpayService,
)


class RecoveryOrchestrator:

    def __init__(self, db: Session):
        self.db = db
        self.executor = RecoveryActionExecutor(
            RazorpayService()
        )

    def execute_action(
        self,
        action: RecoveryAction,
        recovery_case: RecoveryCase,
        transaction: Transaction,
    ) -> RecoveryAction:

        if action.status != "pending":
            return action

        executed_action = self.executor.execute(
            action=action,
            recovery_case=recovery_case,
            transaction=transaction,
        )

        self.db.flush()

        return executed_action