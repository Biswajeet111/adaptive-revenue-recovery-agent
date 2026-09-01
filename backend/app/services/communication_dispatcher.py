import json

from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.communication_recipient import (
    CommunicationRecipientResolver,
)
from backend.app.services.communication_service import (
    CommunicationService,
)
from backend.app.services.communication_trigger import (
    CommunicationTrigger,
)


class CommunicationDispatcher:
    """
    Converts recovery lifecycle events into
    policy-authorized customer communications.

    Responsibilities:
        1. Validate entity associations.
        2. Resolve customer recipient.
        3. Build lifecycle-specific variables.
        4. Delegate authorization to CommunicationService.
        5. Preserve communication idempotency.

    Communication policy and template decisions remain
    inside CommunicationService and its policy/template
    layers.
    """

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

    def __init__(
        self,
        communication_service: CommunicationService,
    ):
        self.communication_service = (
            communication_service
        )

    # =====================================================
    # DISPATCH
    # =====================================================

    def dispatch(
        self,
        *,
        trigger: CommunicationTrigger,
        transaction: Transaction,
        recovery_case: RecoveryCase,
        recovery_action: RecoveryAction,
        recipient_resolver: CommunicationRecipientResolver,
        customer_name: str = "Customer",
    ):
        """
        Dispatch one recovery lifecycle event.

        The dispatcher never directly decides whether
        communication is permitted. CommunicationService
        delegates that decision to CommunicationPolicyService.
        """

        # -------------------------------------------------
        # 1. ENTITY ASSOCIATION VALIDATION
        # -------------------------------------------------

        if (
            trigger.transaction_id
            != transaction.id
        ):
            raise ValueError(
                "Trigger transaction does not match "
                "provided transaction."
            )

        if (
            trigger.recovery_case_id
            != recovery_case.id
        ):
            raise ValueError(
                "Trigger recovery case does not match "
                "provided recovery case."
            )

        if (
            trigger.recovery_action_id
            != recovery_action.id
        ):
            raise ValueError(
                "Trigger recovery action does not match "
                "provided recovery action."
            )

        # -------------------------------------------------
        # 2. EVENT IDEMPOTENCY
        # -------------------------------------------------

        idempotency_key = (
            f"communication:"
            f"{trigger.event_type}:"
            f"transaction-{transaction.id}:"
            f"case-{recovery_case.id}:"
            f"action-{recovery_action.id}"
        )

        # -------------------------------------------------
        # 3. PAYMENT LINK CREATED
        # -------------------------------------------------

        if (
            trigger.event_type
            == self.PAYMENT_LINK_CREATED
        ):

            payment_link = (
                self._get_payment_link_url(
                    recovery_action
                )
            )

            recipient = (
                recipient_resolver.resolve(
                    transaction=transaction,
                    recovery_case=recovery_case,
                    channel="email",
                )
            )

            variables = {
                "customer_name": customer_name,
                "currency": transaction.currency,
                "amount": str(
                    transaction.amount
                ),
                "payment_link": payment_link,
                "expiry": self._get_expiry(
                    recovery_action
                ),
            }

            return self.communication_service.create(
                recovery_case=recovery_case,
                recovery_action=recovery_action,
                channel=recipient.channel,
                recipient=recipient.recipient,
                variables=variables,
                idempotency_key=idempotency_key,
                payment_link_created=True,
                recovery_confirmed=False,
            )

        # -------------------------------------------------
        # 4. PARTIAL PAYMENT RECEIVED
        # -------------------------------------------------

        if (
            trigger.event_type
            == self.PARTIAL_PAYMENT_RECEIVED
        ):

            recovered_amount = (
                trigger.recovered_amount
            )

            remaining_amount = (
                trigger.remaining_amount
            )

            if recovered_amount is None:
                raise ValueError(
                    "Partial-payment trigger is missing "
                    "recovered amount."
                )

            if remaining_amount is None:
                raise ValueError(
                    "Partial-payment trigger is missing "
                    "remaining amount."
                )

            payment_link = (
                self._get_payment_link_url(
                    recovery_action
                )
            )

            recipient = (
                recipient_resolver.resolve(
                    transaction=transaction,
                    recovery_case=recovery_case,
                    channel="email",
                )
            )

            variables = {
                "customer_name": customer_name,
                "currency": transaction.currency,
                "recovered_amount": str(
                    recovered_amount
                ),
                "remaining_amount": str(
                    remaining_amount
                ),
                "payment_link": payment_link,
            }

            return self.communication_service.create(
                recovery_case=recovery_case,
                recovery_action=recovery_action,
                channel=recipient.channel,
                recipient=recipient.recipient,
                variables=variables,
                idempotency_key=idempotency_key,
                payment_link_created=True,
                recovery_confirmed=False,
            )

        # -------------------------------------------------
        # 5. PAYMENT RECOVERED
        # -------------------------------------------------

        if (
            trigger.event_type
            == self.PAYMENT_RECOVERED
        ):

            recovered_amount = (
                recovery_case.recovered_amount
            )

            if recovered_amount is None:
                raise ValueError(
                    "Recovered case is missing "
                    "recovered amount."
                )

            recipient = (
                recipient_resolver.resolve(
                    transaction=transaction,
                    recovery_case=recovery_case,
                    channel="email",
                )
            )

            variables = {
                "customer_name": customer_name,
                "currency": transaction.currency,
                "amount": str(
                    recovered_amount
                ),
            }

            return self.communication_service.create(
                recovery_case=recovery_case,
                recovery_action=recovery_action,
                channel=recipient.channel,
                recipient=recipient.recipient,
                variables=variables,
                idempotency_key=idempotency_key,
                payment_link_created=True,
                recovery_confirmed=True,
            )

        # -------------------------------------------------
        # 6. EXPIRED PAYMENT LINK
        # -------------------------------------------------

        if (
            trigger.event_type
            == self.PAYMENT_LINK_EXPIRED
        ):

            raise ValueError(
                "No customer-facing template is currently "
                "authorized for expired Payment Links by "
                "Communication Policy v1.0."
            )

        # -------------------------------------------------
        # 7. CANCELLED PAYMENT LINK
        # -------------------------------------------------

        if (
            trigger.event_type
            == self.PAYMENT_LINK_CANCELLED
        ):

            raise ValueError(
                "No customer-facing template is currently "
                "authorized for cancelled Payment Links by "
                "Communication Policy v1.0."
            )

        # -------------------------------------------------
        # 8. UNKNOWN EVENT
        # -------------------------------------------------

        raise ValueError(
            "Unsupported communication trigger: "
            f"{trigger.event_type}"
        )

    # =====================================================
    # PAYMENT LINK METADATA
    # =====================================================

    @staticmethod
    def _load_metadata(
        recovery_action: RecoveryAction,
    ) -> dict:

        if not recovery_action.metadata_json:
            raise ValueError(
                "Recovery action has no metadata."
            )

        try:

            metadata = json.loads(
                recovery_action.metadata_json
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                "Recovery action metadata is invalid."
            ) from exc

        if not isinstance(metadata, dict):

            raise ValueError(
                "Recovery action metadata must be "
                "a JSON object."
            )

        return metadata

    @classmethod
    def _get_payment_link_url(
        cls,
        recovery_action: RecoveryAction,
    ) -> str:

        metadata = cls._load_metadata(
            recovery_action
        )

        payment_link = (
            metadata.get("short_url")
            or metadata.get("payment_link_url")
        )

        if not payment_link:

            raise ValueError(
                "Payment Link URL is missing "
                "from recovery action metadata."
            )

        return str(payment_link)

    @classmethod
    def _get_expiry(
        cls,
        recovery_action: RecoveryAction,
    ) -> str:

        metadata = cls._load_metadata(
            recovery_action
        )

        expiry = metadata.get(
            "expire_by"
        )

        if expiry is None:

            return (
                "the expiry time shown on the link"
            )

        return str(expiry)