import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.models.webhook_event import WebhookEvent
from backend.app.services.communication_dispatcher import (
    CommunicationDispatcher,
)
from backend.app.services.communication_recipient import (
    CommunicationRecipientResolver,
)
from backend.app.services.communication_service import (
    CommunicationService,
)
from backend.app.services.communication_trigger import (
    CommunicationTriggerService,
)
from backend.app.services.reconciliation_service import (
    ReconciliationService,
)
from backend.app.services.razorpay_service import (
    RazorpayService,
)


class WebhookService:
    """
    Processes persisted Razorpay webhook events.

    Responsibilities:

        1. Resolve the affected recovery action.
        2. Resolve the recovery case.
        3. Resolve the original transaction.
        4. Reconcile provider payment events.
        5. Preserve Payment Link lifecycle metadata.
        6. Trigger policy-authorized communication.
        7. Maintain webhook event idempotency.

    Financial reconciliation remains inside
    ReconciliationService.

    Customer communication authorization remains inside
    CommunicationService / CommunicationPolicyService.
    """

    def __init__(
        self,
        db: Session,
        enable_communications: bool = False,
    ):
        self.db = db

        self.enable_communications = (
            enable_communications
        )

        self.communication_service = (
            CommunicationService(
                db=db,
            )
        )

        self.communication_dispatcher = (
            CommunicationDispatcher(
                self.communication_service,
            )
        )

        self.communication_trigger_service = (
            CommunicationTriggerService()
        )

        # CommunicationRecipientResolver is intentionally
        # created lazily only when communication is required.
        #
        # This prevents unrelated webhook processing from
        # requiring recovery notification configuration.

    # =========================================================
    # WEBHOOK EVENT STORAGE
    # =========================================================

    def event_exists(
        self,
        event_id: str,
    ) -> bool:

        statement = select(
            WebhookEvent
        ).where(
            WebhookEvent.event_id
            == event_id
        )

        return (
            self.db.scalar(statement)
            is not None
        )

    def get_event(
        self,
        event_id: str,
    ) -> WebhookEvent | None:

        statement = select(
            WebhookEvent
        ).where(
            WebhookEvent.event_id
            == event_id
        )

        return self.db.scalar(
            statement
        )

    def store_event(
        self,
        *,
        event_id: str,
        event_type: str,
        payload: dict,
        signature: str,
    ) -> WebhookEvent:

        existing = self.get_event(
            event_id
        )

        if existing is not None:
            return existing

        event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            payload=json.dumps(
                payload
            ),
            signature=signature,
            processed=False,
        )

        self.db.add(event)

        self.db.flush()

        return event

    # =========================================================
    # PAYMENT EVENT PROCESSING
    # =========================================================

    def process_payment_event(
        self,
        event: WebhookEvent,
    ) -> None:

        if event.processed:
            return

        payload = self._load_payload(
            event
        )

        payment = self._extract_payment(
            payload
        )

        if event.event_type == "payment.failed":

            self._process_payment_failed(
                payment
            )

        elif event.event_type == "payment.authorized":

            self._process_payment_authorized(
                payment
            )

        elif event.event_type == "payment.captured":

            self._process_payment_captured(
                payment
            )

        else:

            raise ValueError(
                "Unsupported payment event: "
                f"{event.event_type}"
            )

        self._mark_processed(
            event
        )

    # =========================================================
    # PAYMENT LINK EVENT PROCESSING
    # =========================================================

    def process_payment_link_event(
        self,
        event: WebhookEvent,
    ) -> None:

        if event.processed:
            return

        payload = self._load_payload(
            event
        )

        payment_link = (
            self._extract_payment_link(
                payload
            )
        )

        payment = (
            self._extract_payment(
                payload,
                required=False,
            )
        )

        # -----------------------------------------------------
        # Payment Link ID
        # -----------------------------------------------------

        payment_link_id = (
            payment_link.get("id")
        )

        if not payment_link_id:

            raise ValueError(
                "Payment Link event does not "
                "contain a Payment Link ID."
            )

        # -----------------------------------------------------
        # Find recovery action
        # -----------------------------------------------------

        action = self._find_recovery_action(
            payment_link_id
        )

        if action is None:

            raise ValueError(
                "Recovery action not found for "
                f"Payment Link {payment_link_id}."
            )

        # -----------------------------------------------------
        # Find recovery case
        # -----------------------------------------------------

        statement = select(
            RecoveryCase
        ).where(
            RecoveryCase.id
            == action.recovery_case_id
        )

        recovery_case = self.db.scalar(
            statement
        )

        if recovery_case is None:

            raise ValueError(
                f"Recovery case not found for "
                f"action {action.id}."
            )

        # -----------------------------------------------------
        # Find original transaction
        # -----------------------------------------------------

        statement = select(
            Transaction
        ).where(
            Transaction.id
            == recovery_case.transaction_id
        )

        transaction = self.db.scalar(
            statement
        )

        if transaction is None:

            raise ValueError(
                f"Transaction not found for "
                f"recovery case "
                f"{recovery_case.id}."
            )

        # -----------------------------------------------------
        # Reconciliation service
        # -----------------------------------------------------

        reconciliation_service = (
            ReconciliationService(
                RazorpayService()
            )
        )

        # =====================================================
        # PAYMENT LINK PAID
        # =====================================================

        if (
            event.event_type
            == "payment_link.paid"
        ):

            if not payment:

                raise ValueError(
                    "Payment Link reports paid, "
                    "but payment entity is missing."
                )

            # Preserve customer-facing URL before
            # reconciliation can replace action metadata.
            payment_link_url = (
                self._get_payment_link_url(
                    action
                )
            )

            recovery_result = (
                reconciliation_service
                .reconcile_payment_link(
                    action=action,
                    recovery_case=recovery_case,
                    transaction=transaction,
                    payment=payment,
                    payment_link=payment_link,
                )
            )

            # Reconciliation is authoritative for
            # execution metadata, but the Payment Link URL
            # is durable lifecycle information.
            self._restore_payment_link_url(
                action=action,
                payment_link_url=(
                    payment_link_url
                ),
            )

            # -------------------------------------------------
            # Only confirmed recovery may create a
            # recovery-success communication.
            # -------------------------------------------------

            if recovery_result is True:

                if self.enable_communications:

                    recovery_trigger = (
                        self.communication_trigger_service
                        .payment_recovered(
                            transaction=transaction,
                            recovery_case=recovery_case,
                            recovery_action=action,
                        )
                    )

                    recipient_resolver = (
                        CommunicationRecipientResolver()
                    )

                    self.communication_dispatcher.dispatch(
                        trigger=recovery_trigger,
                        transaction=transaction,
                        recovery_case=recovery_case,
                        recovery_action=action,
                        recipient_resolver=(
                            recipient_resolver
                        ),
                    )

        # =====================================================
        # PAYMENT LINK PARTIALLY PAID
        # =====================================================

        elif (
            event.event_type
            == "payment_link.partially_paid"
        ):

            if not payment:

                raise ValueError(
                    "Payment Link reports partial payment, "
                    "but payment entity is missing."
                )

            # -------------------------------------------------
            # Preserve URL BEFORE reconciliation.
            # -------------------------------------------------

            payment_link_url = (
                self._get_payment_link_url(
                    action
                )
            )

            reconciliation_service.reconcile_payment_link(
                action=action,
                recovery_case=recovery_case,
                transaction=transaction,
                payment=payment,
                payment_link=payment_link,
            )

            # -------------------------------------------------
            # Reconciliation is authoritative for the
            # cumulative recovered amount.
            #
            # However, reconciliation may replace the action
            # metadata. Restore the durable customer-facing
            # Payment Link URL before communication.
            # -------------------------------------------------

            self._restore_payment_link_url(
                action=action,
                payment_link_url=(
                    payment_link_url
                ),
            )

            recovered_amount = (
                recovery_case.recovered_amount
            )

            expected_amount = (
                transaction.amount
            )

            if recovered_amount is None:

                raise ValueError(
                    "Partial recovery completed without "
                    "a recovered amount."
                )

            remaining_amount = (
                expected_amount
                - recovered_amount
            )

            if self.enable_communications:

                partial_trigger = (
                    self.communication_trigger_service
                    .partial_payment_received(
                        transaction=transaction,
                        recovery_case=recovery_case,
                        recovery_action=action,
                        recovered_amount=(
                            recovered_amount
                        ),
                        remaining_amount=(
                            remaining_amount
                        ),
                    )
                )

                recipient_resolver = (
                    CommunicationRecipientResolver()
                )

                self.communication_dispatcher.dispatch(
                    trigger=partial_trigger,
                    transaction=transaction,
                    recovery_case=recovery_case,
                    recovery_action=action,
                    recipient_resolver=(
                        recipient_resolver
                    ),
                )

        # =====================================================
        # PAYMENT LINK EXPIRED
        # =====================================================

        elif (
            event.event_type
            == "payment_link.expired"
        ):

            action.status = "failed"

            action.result = (
                "Razorpay Payment Link expired."
            )

            # -------------------------------------------------
            # A Payment Link expiration means recovery was
            # not completed.
            # -------------------------------------------------

            if (
                recovery_case.recovered_amount
                is None
            ):

                recovery_case.status = (
                    "partially_recovered"
                )

            else:

                recovery_case.status = (
                    "partially_recovered"
                )

            recovery_case.recovered_at = None

        # =====================================================
        # PAYMENT LINK CANCELLED
        # =====================================================

        elif (
            event.event_type
            == "payment_link.cancelled"
        ):

            action.status = "failed"

            action.result = (
                "Razorpay Payment Link cancelled."
            )

            recovery_case.status = (
                "partially_recovered"
            )

            recovery_case.recovered_at = None

        else:

            raise ValueError(
                "Unsupported Payment Link event: "
                f"{event.event_type}"
            )

        # =====================================================
        # MARK WEBHOOK PROCESSED
        # =====================================================

        self._mark_processed(
            event
        )

    # =========================================================
    # PAYMENT FAILED
    # =========================================================

    def _process_payment_failed(
        self,
        payment: dict,
    ) -> None:

        payment_id = payment.get(
            "id"
        )

        order_id = payment.get(
            "order_id"
        )

        if not order_id:
            return

        statement = select(
            Transaction
        ).where(
            Transaction.razorpay_order_id
            == order_id
        )

        transaction = self.db.scalar(
            statement
        )

        if transaction is None:
            return

        transaction.status = "failed"

        transaction.razorpay_payment_id = (
            payment_id
        )

        transaction.payment_method = (
            payment.get("method")
        )

        transaction.failure_code = (
            payment.get("error_code")
        )

        transaction.failure_reason = (
            payment.get("error_description")
        )

    # =========================================================
    # PAYMENT AUTHORIZED
    # =========================================================

    def _process_payment_authorized(
        self,
        payment: dict,
    ) -> None:

        payment_id = payment.get(
            "id"
        )

        order_id = payment.get(
            "order_id"
        )

        if not order_id:
            return

        statement = select(
            Transaction
        ).where(
            Transaction.razorpay_order_id
            == order_id
        )

        transaction = self.db.scalar(
            statement
        )

        if transaction is None:
            return

        transaction.status = "authorized"

        transaction.razorpay_payment_id = (
            payment_id
        )

        transaction.payment_method = (
            payment.get("method")
        )

    # =========================================================
    # PAYMENT CAPTURED
    # =========================================================

    def _process_payment_captured(
        self,
        payment: dict,
    ) -> None:

        payment_id = payment.get(
            "id"
        )

        order_id = payment.get(
            "order_id"
        )

        if not order_id:
            return

        statement = select(
            Transaction
        ).where(
            Transaction.razorpay_order_id
            == order_id
        )

        transaction = self.db.scalar(
            statement
        )

        if transaction is None:
            return

        transaction.status = "captured"

        transaction.razorpay_payment_id = (
            payment_id
        )

        transaction.payment_method = (
            payment.get("method")
        )

        transaction.failure_code = None

        transaction.failure_reason = None

    # =========================================================
    # FIND RECOVERY ACTION
    # =========================================================

    def _find_recovery_action(
        self,
        payment_link_id: str,
    ) -> RecoveryAction | None:

        # Payment Link ID is stored inside action metadata.
        actions = self.db.scalars(
            select(
                RecoveryAction
            )
        ).all()

        for action in actions:

            if not action.metadata_json:
                continue

            try:

                metadata = json.loads(
                    action.metadata_json
                )

            except json.JSONDecodeError:

                continue

            if not isinstance(
                metadata,
                dict,
            ):
                continue

            stored_payment_link_id = (
                metadata.get(
                    "payment_link_id"
                )
            )

            if (
                stored_payment_link_id
                == payment_link_id
            ):

                return action

        return None

    # =========================================================
    # PAYMENT LINK URL
    # =========================================================

    @staticmethod
    def _get_payment_link_url(
        action: RecoveryAction,
    ) -> str:

        if not action.metadata_json:

            raise ValueError(
                "Recovery action has no "
                "Payment Link metadata."
            )

        try:

            metadata = json.loads(
                action.metadata_json
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                "Recovery action metadata is invalid."
            ) from exc

        if not isinstance(
            metadata,
            dict,
        ):

            raise ValueError(
                "Recovery action metadata must "
                "be a JSON object."
            )

        payment_link_url = (
            metadata.get("short_url")
            or metadata.get(
                "payment_link_url"
            )
        )

        if not payment_link_url:

            raise ValueError(
                "Payment Link URL is missing "
                "from recovery action metadata."
            )

        return str(
            payment_link_url
        )

    # =========================================================
    # PRESERVE PAYMENT LINK URL
    # =========================================================

    @classmethod
    def _restore_payment_link_url(
        cls,
        *,
        action: RecoveryAction,
        payment_link_url: str | None,
    ) -> None:

        if not payment_link_url:
            return

        metadata = {}

        if action.metadata_json:

            try:

                loaded = json.loads(
                    action.metadata_json
                )

                if isinstance(
                    loaded,
                    dict,
                ):

                    metadata = loaded

            except json.JSONDecodeError:

                metadata = {}

        metadata["short_url"] = (
            payment_link_url
        )

        action.metadata_json = json.dumps(
            metadata
        )

        # Do not commit here.
        #
        # Webhook endpoint owns the transaction boundary
        # and commits only after successful processing.

        cls._flush_action(
            action
        )

    @staticmethod
    def _flush_action(
        action: RecoveryAction,
    ) -> None:
        """
        Kept intentionally small so URL preservation updates
        are flushed through the owning SQLAlchemy session.
        """

        # SQLAlchemy tracks the modified object automatically.
        # No independent transaction is created here.
        return

    # =========================================================
    # PAYLOAD HELPERS
    # =========================================================

    @staticmethod
    def _load_payload(
        event: WebhookEvent,
    ) -> dict:

        try:

            payload = json.loads(
                event.payload
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ) as exc:

            raise ValueError(
                "Webhook event payload is invalid."
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):

            raise ValueError(
                "Webhook event payload must "
                "be a JSON object."
            )

        return payload

    @staticmethod
    def _extract_payment_link(
        payload: dict,
    ) -> dict:

        try:

            payment_link = (
                payload[
                    "payload"
                ][
                    "payment_link"
                ][
                    "entity"
                ]
            )

        except (
            KeyError,
            TypeError,
        ) as exc:

            raise ValueError(
                "Webhook payload does not contain "
                "a valid Payment Link entity."
            ) from exc

        if not isinstance(
            payment_link,
            dict,
        ):

            raise ValueError(
                "Payment Link entity must "
                "be a JSON object."
            )

        return payment_link

    @staticmethod
    def _extract_payment(
        payload: dict,
        required: bool = True,
    ) -> dict | None:

        try:

            payment = (
                payload[
                    "payload"
                ][
                    "payment"
                ][
                    "entity"
                ]
            )

        except (
            KeyError,
            TypeError,
        ):

            if required:

                raise ValueError(
                    "Webhook payload does not contain "
                    "a valid payment entity."
                )

            return None

        if not isinstance(
            payment,
            dict,
        ):

            raise ValueError(
                "Payment entity must "
                "be a JSON object."
            )

        return payment

    # =========================================================
    # MARK EVENT PROCESSED
    # =========================================================

    def _mark_processed(
        self,
        event: WebhookEvent,
    ) -> None:

        event.processed = True

        event.processed_at = (
            datetime.now(
                timezone.utc
            )
        )

        self.db.flush()