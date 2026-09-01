from dataclasses import dataclass
from decimal import Decimal

from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction


@dataclass(frozen=True)
class CommunicationTrigger:
    event_type: str
    recovery_case_id: int
    recovery_action_id: int
    transaction_id: int
    payment_link_created: bool = False
    recovery_confirmed: bool = False
    recovered_amount: Decimal | None = None
    remaining_amount: Decimal | None = None


class CommunicationTriggerService:

    PAYMENT_LINK_CREATED = (
        "payment_link_created"
    )

    PARTIAL_PAYMENT_RECEIVED = (
        "partial_payment_received"
    )

    PAYMENT_RECOVERED = (
        "payment_recovered"
    )

    PAYMENT_LINK_EXPIRED = (
        "payment_link_expired"
    )

    PAYMENT_LINK_CANCELLED = (
        "payment_link_cancelled"
    )

    def payment_link_created(
        self,
        *,
        transaction: Transaction,
        recovery_case: RecoveryCase,
        recovery_action: RecoveryAction,
    ) -> CommunicationTrigger:

        return CommunicationTrigger(
            event_type=self.PAYMENT_LINK_CREATED,
            recovery_case_id=recovery_case.id,
            recovery_action_id=recovery_action.id,
            transaction_id=transaction.id,
            payment_link_created=True,
            recovery_confirmed=False,
        )

    def partial_payment_received(
        self,
        *,
        transaction: Transaction,
        recovery_case: RecoveryCase,
        recovery_action: RecoveryAction,
        recovered_amount: Decimal,
        remaining_amount: Decimal,
    ) -> CommunicationTrigger:

        return CommunicationTrigger(
            event_type=self.PARTIAL_PAYMENT_RECEIVED,
            recovery_case_id=recovery_case.id,
            recovery_action_id=recovery_action.id,
            transaction_id=transaction.id,
            payment_link_created=True,
            recovery_confirmed=False,
            recovered_amount=recovered_amount,
            remaining_amount=remaining_amount,
        )

    def payment_recovered(
        self,
        *,
        transaction: Transaction,
        recovery_case: RecoveryCase,
        recovery_action: RecoveryAction,
    ) -> CommunicationTrigger:

        return CommunicationTrigger(
            event_type=self.PAYMENT_RECOVERED,
            recovery_case_id=recovery_case.id,
            recovery_action_id=recovery_action.id,
            transaction_id=transaction.id,
            payment_link_created=True,
            recovery_confirmed=True,
            recovered_amount=(
                recovery_case.recovered_amount
            ),
            remaining_amount=Decimal("0"),
        )

    def payment_link_expired(
        self,
        *,
        transaction: Transaction,
        recovery_case: RecoveryCase,
        recovery_action: RecoveryAction,
    ) -> CommunicationTrigger:

        return CommunicationTrigger(
            event_type=self.PAYMENT_LINK_EXPIRED,
            recovery_case_id=recovery_case.id,
            recovery_action_id=recovery_action.id,
            transaction_id=transaction.id,
            payment_link_created=True,
            recovery_confirmed=False,
        )

    def payment_link_cancelled(
        self,
        *,
        transaction: Transaction,
        recovery_case: RecoveryCase,
        recovery_action: RecoveryAction,
    ) -> CommunicationTrigger:

        return CommunicationTrigger(
            event_type=self.PAYMENT_LINK_CANCELLED,
            recovery_case_id=recovery_case.id,
            recovery_action_id=recovery_action.id,
            transaction_id=transaction.id,
            payment_link_created=True,
            recovery_confirmed=False,
        )