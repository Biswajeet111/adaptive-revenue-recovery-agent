import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.communication import Communication
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.services.communication_policy import (
    CommunicationPolicyService,
)
from backend.app.services.communication_provider import (
    CommunicationProvider,
)
from backend.app.services.template_engine import (
    TemplateEngine,
)


class CommunicationService:

    def __init__(
        self,
        db: Session,
        template_engine: TemplateEngine | None = None,
        policy_service: (
            CommunicationPolicyService | None
        ) = None,
        providers: (
            dict[str, CommunicationProvider] | None
        ) = None,
    ):

        self.db = db

        self.template_engine = (
            template_engine
            or TemplateEngine()
        )

        self.policy = (
            policy_service
            or CommunicationPolicyService()
        )

        self.providers = providers or {}

    # =====================================================
    # CREATE COMMUNICATION
    # =====================================================

    def create(
        self,
        *,
        recovery_case: RecoveryCase,
        recovery_action: RecoveryAction,
        channel: str,
        recipient: str,
        variables: dict[str, object],
        idempotency_key: str,
        payment_link_created: bool = False,
        recovery_confirmed: bool = False,
    ) -> Communication:

        # -------------------------------------------------
        # POLICY
        # -------------------------------------------------

        decision = self.policy.evaluate(
            action_type=(
                recovery_action.action_type
            ),
            recovery_case_status=(
                recovery_case.status
            ),
            recovery_action_status=(
                recovery_action.status
            ),
            payment_link_created=(
                payment_link_created
            ),
            recovery_confirmed=(
                recovery_confirmed
            ),
            channel=channel,
        )

        if decision.decision != "allowed":

            raise ValueError(
                "Communication not authorized: "
                f"{decision.reason}"
            )

        if decision.channel != channel:

            raise ValueError(
                "Requested communication channel "
                "does not match policy-approved channel."
            )

        # -------------------------------------------------
        # VARIABLE POLICY
        # -------------------------------------------------

        self.policy.validate_variables(
            variables,
            decision.allowed_variables,
        )

        # -------------------------------------------------
        # TEMPLATE
        # -------------------------------------------------

        rendered = self.template_engine.render(
            name=decision.template_name,
            version=decision.template_version,
            channel=decision.channel,
            variables=variables,
        )

        # -------------------------------------------------
        # IDEMPOTENCY
        # -------------------------------------------------

        existing = self.db.scalar(
            select(Communication).where(
                Communication.idempotency_key
                == idempotency_key
            )
        )

        if existing is not None:
            return existing

        # -------------------------------------------------
        # CREATE RECORD
        # -------------------------------------------------

        communication = Communication(
            recovery_case_id=(
                recovery_case.id
            ),
            recovery_action_id=(
                recovery_action.id
            ),
            channel=(
                rendered.channel
            ),
            template_name=(
                rendered.name
            ),
            template_version=(
                rendered.version
            ),
            recipient=recipient,
            subject=rendered.subject,
            message=rendered.body,
            status="pending",
            idempotency_key=idempotency_key,
            metadata_json=json.dumps(
                {
                    "policy": (
                        CommunicationPolicyService.POLICY_NAME
                    ),
                    "policy_version": (
                        CommunicationPolicyService.POLICY_VERSION
                    ),
                    "policy_reason": (
                        decision.reason
                    ),
                }
            ),
        )

        self.db.add(communication)

        try:

            self.db.commit()

        except IntegrityError:

            self.db.rollback()

            existing = self.db.scalar(
                select(Communication).where(
                    Communication.idempotency_key
                    == idempotency_key
                )
            )

            if existing is not None:
                return existing

            raise

        self.db.refresh(
            communication
        )

        return communication

    # =====================================================
    # SEND COMMUNICATION
    # =====================================================

    def send(
        self,
        communication: Communication,
    ) -> Communication:

        if communication.status == "sent":
            return communication

        if communication.status == "delivered":
            return communication

        provider = self.providers.get(
            communication.channel
        )

        if provider is None:

            communication.status = "failed"

            communication.failed_at = (
                datetime.now(timezone.utc)
            )

            communication.failure_reason = (
                "No provider configured for "
                f"channel '{communication.channel}'."
            )

            self.db.commit()

            return communication

        communication.status = "sending"

        self.db.commit()

        try:

            result = provider.send(
                recipient=(
                    communication.recipient
                ),
                subject=(
                    communication.subject
                ),
                message=(
                    communication.message
                ),
                idempotency_key=(
                    communication.idempotency_key
                ),
            )

            if not result.success:

                communication.status = "failed"

                communication.failed_at = (
                    datetime.now(timezone.utc)
                )

                communication.failure_reason = (
                    result.failure_reason
                    or "Provider rejected communication."
                )

                self.db.commit()

                return communication

            communication.status = "sent"

            communication.provider = (
                result.provider
            )

            communication.provider_message_id = (
                result.provider_message_id
            )

            communication.sent_at = (
                datetime.now(timezone.utc)
            )

            self.db.commit()

            return communication

        except Exception as exc:

            communication.status = "failed"

            communication.failed_at = (
                datetime.now(timezone.utc)
            )

            communication.failure_reason = str(
                exc
            )

            self.db.commit()

            return communication

    # =====================================================
    # MARK DELIVERED
    # =====================================================

    def mark_delivered(
        self,
        communication: Communication,
    ) -> Communication:

        if communication.status == "delivered":
            return communication

        if communication.status != "sent":

            raise ValueError(
                "Only sent communications can "
                "be marked as delivered."
            )

        communication.status = "delivered"

        communication.delivered_at = (
            datetime.now(timezone.utc)
        )

        self.db.commit()

        return communication