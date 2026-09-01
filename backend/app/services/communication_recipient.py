from dataclasses import dataclass

from backend.app.config import settings
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction


@dataclass(frozen=True)
class CommunicationRecipient:
    channel: str
    recipient: str


class CommunicationRecipientResolver:
    """
    Resolves the customer destination for recovery
    communication.

    Customer contact data is intentionally kept outside
    the financial Transaction model.

    Phase 11 uses the configured recovery notification
    address. This can later be replaced by a Customer /
    Account lookup without changing the recovery pipeline.
    """

    def __init__(
        self,
        *,
        default_email: str | None = None,
    ):
        self.default_email = (
            default_email
            if default_email is not None
            else settings.recovery_notification_email
        )

    def resolve(
        self,
        *,
        transaction: Transaction,
        recovery_case: RecoveryCase,
        channel: str = "email",
    ) -> CommunicationRecipient:

        if channel != "email":
            raise ValueError(
                f"Unsupported communication channel: "
                f"{channel}"
            )

        if not self.default_email:
            raise ValueError(
                "No customer email is available for "
                f"transaction {transaction.id}."
            )

        return CommunicationRecipient(
            channel="email",
            recipient=self.default_email,
        )