from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog
from backend.app.models.communication import Communication
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.models.webhook_event import WebhookEvent


class OperationsService:
    """
    Read-only operational visibility over the recovery system.

    This service intentionally performs no recovery execution,
    reconciliation, communication dispatch, webhook processing,
    or AI/API calls.
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(self) -> dict:
        return {
            "transactions": self._status_counts(
                Transaction,
                Transaction.status,
            ),
            "recovery_cases": self._status_counts(
                RecoveryCase,
                RecoveryCase.status,
            ),
            "recovery_actions": self._status_counts(
                RecoveryAction,
                RecoveryAction.status,
            ),
            "webhooks": self._status_counts(
                WebhookEvent,
                WebhookEvent.processed,
            ),
            "communications": self._status_counts(
                Communication,
                Communication.status,
            ),
        }

    # =========================================================
    # PHASE 12 — SYSTEM METRICS
    # =========================================================

    def metrics(self) -> dict:
        """
        Return business-level operational metrics.

        This method is strictly read-only and performs no
        recovery, AI, provider, webhook, or communication
        operations.
        """

        transaction_counts = self._status_counts(
            Transaction,
            Transaction.status,
        )

        recovery_case_counts = self._status_counts(
            RecoveryCase,
            RecoveryCase.status,
        )

        recovery_action_counts = self._status_counts(
            RecoveryAction,
            RecoveryAction.status,
        )

        webhook_counts = self._status_counts(
            WebhookEvent,
            WebhookEvent.processed,
        )

        communication_counts = self._status_counts(
            Communication,
            Communication.status,
        )

        # -----------------------------------------------------
        # TRANSACTION METRICS
        # -----------------------------------------------------

        failed_payments = transaction_counts.get(
            "failed",
            0,
        )

        captured_payments = transaction_counts.get(
            "captured",
            0,
        )

        # -----------------------------------------------------
        # RECOVERY CASE METRICS
        # -----------------------------------------------------

        total_recovery_cases = self._count(
            RecoveryCase
        )

        open_recovery_cases = recovery_case_counts.get(
            "open",
            0,
        )

        recovered_cases = recovery_case_counts.get(
            "recovered",
            0,
        )

        partial_recoveries = self._count_partial_recoveries()

        manual_review_cases = recovery_case_counts.get(
            "manual_review",
            0,
        )

        # -----------------------------------------------------
        # FINANCIAL METRICS
        # -----------------------------------------------------

        revenue_at_risk = self._sum(
            RecoveryCase.revenue_at_risk
        )

        recovered_revenue = self._sum_recovered_revenue()

        recovery_rate = self._percentage(
            recovered_revenue,
            revenue_at_risk,
        )

        # -----------------------------------------------------
        # WEBHOOK METRICS
        # -----------------------------------------------------

        processed_webhooks = webhook_counts.get(
            "True",
            0,
        )

        unprocessed_webhooks = webhook_counts.get(
            "False",
            0,
        )

        # -----------------------------------------------------
        # COMMUNICATION METRICS
        # -----------------------------------------------------

        communication_failures = communication_counts.get(
            "failed",
            0,
        )

        communication_pending = communication_counts.get(
            "pending",
            0,
        )

        # -----------------------------------------------------
        # RETURN OPERATIONAL VIEW
        # -----------------------------------------------------

        return {
            "transactions": {
                "total": self._count(
                    Transaction
                ),
                "failed": failed_payments,
                "captured": captured_payments,
                "status_counts": transaction_counts,
            },

            "recovery": {
                "total_cases": total_recovery_cases,
                "open_cases": open_recovery_cases,
                "recovered_cases": recovered_cases,
                "partial_recoveries": partial_recoveries,
                "manual_review_cases": manual_review_cases,
                "revenue_at_risk": self._money(
                    revenue_at_risk
                ),
                "recovered_revenue": self._money(
                    recovered_revenue
                ),
                "recovery_rate_percent": recovery_rate,
                "status_counts": recovery_case_counts,
            },

            "recovery_actions": {
                "status_counts": recovery_action_counts,
                "pending": recovery_action_counts.get(
                    "pending",
                    0,
                ),
                "executing": recovery_action_counts.get(
                    "executing",
                    0,
                ),
                "executed": recovery_action_counts.get(
                    "executed",
                    0,
                ),
                "successful": recovery_action_counts.get(
                    "successful",
                    0,
                ),
                "failed": recovery_action_counts.get(
                    "failed",
                    0,
                ),
            },

            "webhooks": {
                "processed": processed_webhooks,
                "unprocessed": unprocessed_webhooks,
                "total": (
                    processed_webhooks
                    + unprocessed_webhooks
                ),
                "status_counts": webhook_counts,
            },

            "communications": {
                "pending": communication_pending,
                "failed": communication_failures,
                "status_counts": communication_counts,
            },
        }

    # =========================================================
    # RECOVERY CASES
    # =========================================================

    def list_recovery_cases(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:

        cases = self.db.scalars(
            select(RecoveryCase)
            .order_by(RecoveryCase.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()

        return [
            self._recovery_case_summary(case)
            for case in cases
        ]

    def get_recovery_case(
        self,
        case_id: int,
    ) -> dict | None:

        case = self.db.get(
            RecoveryCase,
            case_id,
        )

        if case is None:
            return None

        actions = self.db.scalars(
            select(RecoveryAction)
            .where(
                RecoveryAction.recovery_case_id
                == case.id
            )
            .order_by(RecoveryAction.id.asc())
        ).all()

        communications = self.db.scalars(
            select(Communication)
            .where(
                Communication.recovery_case_id
                == case.id
            )
            .order_by(Communication.id.asc())
        ).all()

        return {
            "case": self._recovery_case_summary(case),
            "actions": [
                self._recovery_action_summary(action)
                for action in actions
            ],
            "communications": [
                self._communication_summary(
                    communication
                )
                for communication in communications
            ],
        }

    # =========================================================
    # RECOVERY ACTION
    # =========================================================

    def get_recovery_action(
        self,
        action_id: int,
    ) -> dict | None:

        action = self.db.get(
            RecoveryAction,
            action_id,
        )

        if action is None:
            return None

        return self._recovery_action_summary(
            action
        )

    # =========================================================
    # WEBHOOKS
    # =========================================================

    def list_webhooks(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:

        events = self.db.scalars(
            select(WebhookEvent)
            .order_by(WebhookEvent.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()

        return [
            {
                "id": event.id,
                "event_id": event.event_id,
                "event_type": event.event_type,
                "processed": event.processed,
                "received_at": event.received_at,
                "processed_at": event.processed_at,
            }
            for event in events
        ]

    # =========================================================
    # AUDIT LOGS
    # =========================================================

    def list_audit_logs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:

        logs = self.db.scalars(
            select(AuditLog)
            .order_by(AuditLog.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()

        return [
            {
                "id": log.id,
                "actor_type": log.actor_type,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "reason": log.reason,
                "created_at": log.created_at,
            }
            for log in logs
        ]

    # =========================================================
    # COMMUNICATIONS
    # =========================================================

    def list_communications(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:

        communications = self.db.scalars(
            select(Communication)
            .order_by(Communication.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()

        return [
            self._communication_summary(
                communication
            )
            for communication in communications
        ]

    # =========================================================
    # INTERNAL METRIC HELPERS
    # =========================================================

    def _count(self, model) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(model)
            )
            or 0
        )

    def _sum(self, column) -> Decimal:
        value = self.db.scalar(
            select(func.coalesce(func.sum(column), 0))
        )

        return Decimal(str(value or 0))

    def _sum_recovered_revenue(self) -> Decimal:
        """
        Sum only the recovered amount recorded against
        recovery cases.

        RecoveryCase.recovered_amount is the authoritative
        financial recovery value maintained by reconciliation.
        """

        return self._sum(
            RecoveryCase.recovered_amount
        )

    def _count_partial_recoveries(self) -> int:
        """
        Count cases where some, but not all, revenue has
        been recovered.

        A recovered amount of zero or NULL is not considered
        a partial recovery.
        """

        return int(
            self.db.scalar(
                select(func.count())
                .select_from(RecoveryCase)
                .where(
                    RecoveryCase.recovered_amount.is_not(None),
                    RecoveryCase.recovered_amount > 0,
                    RecoveryCase.recovered_amount
                    < RecoveryCase.revenue_at_risk,
                )
            )
            or 0
        )

    @staticmethod
    def _money(value: Decimal) -> str:
        return format(
            value.quantize(Decimal("0.01")),
            "f",
        )

    @staticmethod
    def _percentage(
        numerator: Decimal,
        denominator: Decimal,
    ) -> float:

        if denominator <= 0:
            return 0.0

        percentage = (
            numerator
            / denominator
            * Decimal("100")
        )

        return float(
            percentage.quantize(
                Decimal("0.01")
            )
        )

    # =========================================================
    # STATUS COUNTS
    # =========================================================

    def _status_counts(
        self,
        model,
        column,
    ) -> dict:

        rows = self.db.execute(
            select(
                column,
                func.count(),
            )
            .select_from(model)
            .group_by(column)
        ).all()

        return {
            str(status): count
            for status, count in rows
        }

    # =========================================================
    # SERIALIZATION HELPERS
    # =========================================================

    @staticmethod
    def _recovery_case_summary(
        case: RecoveryCase,
    ) -> dict:

        return {
            "id": case.id,
            "transaction_id": case.transaction_id,
            "classification": case.classification,
            "recoverability": case.recoverability,
            "risk_score": str(case.risk_score),
            "revenue_at_risk": str(
                case.revenue_at_risk
            ),
            "recommended_action": (
                case.recommended_action
            ),
            "status": case.status,
            "recovered_amount": (
                str(case.recovered_amount)
                if case.recovered_amount is not None
                else None
            ),
            "recovered_at": case.recovered_at,
            "created_at": case.created_at,
            "updated_at": case.updated_at,
        }

    @staticmethod
    def _recovery_action_summary(
        action: RecoveryAction,
    ) -> dict:

        return {
            "id": action.id,
            "recovery_case_id": (
                action.recovery_case_id
            ),
            "action_type": action.action_type,
            "channel": action.channel,
            "status": action.status,
            "scheduled_at": action.scheduled_at,
            "executed_at": action.executed_at,
            "attempt_count": action.attempt_count,
            "last_attempt_at": action.last_attempt_at,
            "lease_until": action.lease_until,
            "result": action.result,
            "created_at": action.created_at,
        }

    @staticmethod
    def _communication_summary(
        communication: Communication,
    ) -> dict:

        return {
            "id": communication.id,
            "recovery_case_id": (
                communication.recovery_case_id
            ),
            "recovery_action_id": (
                communication.recovery_action_id
            ),
            "channel": communication.channel,
            "template_name": (
                communication.template_name
            ),
            "template_version": (
                communication.template_version
            ),
            "status": communication.status,
            "provider": communication.provider,
            "provider_message_id": (
                communication.provider_message_id
            ),
            "sent_at": communication.sent_at,
            "delivered_at": communication.delivered_at,
            "failed_at": communication.failed_at,
            "failure_reason": (
                communication.failure_reason
            ),
            "created_at": communication.created_at,
            "updated_at": communication.updated_at,
        }