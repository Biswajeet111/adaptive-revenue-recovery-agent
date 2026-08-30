import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.schemas.recovery_decision import RecoveryDecision
from backend.app.services.action_executor import RecoveryActionExecutor
from backend.app.services.ai_recovery_service import AIRecoveryService
from backend.app.services.decision_agent import RecoveryDecisionAgent
from backend.app.services.decision_safety_gate import DecisionSafetyGate
from backend.app.services.embedding_service import GeminiEmbeddingService
from backend.app.services.policy_retrieval_service import PolicyRetrievalService
from backend.app.services.razorpay_service import RazorpayService
from backend.app.services.recovery_service import RecoveryService


class RecoveryOrchestrator:
    """
    Coordinates the complete AI revenue-recovery pipeline.

    Flow:

        Recovery Action
              ↓
        State validation
              ↓
        Transaction context
              ↓
        Policy retrieval
              ↓
        AI decision
              ↓
        Deterministic safety gate
              ↓
        Audit provenance
              ↓
        Approved action
              ↓
        External execution

    The orchestrator coordinates the workflow.

    DecisionSafetyGate remains responsible for deciding
    whether an AI recommendation is safe to execute.
    """

    TERMINAL_CASE_STATES = {
        "recovered",
        "closed",
    }

    ACTIVE_ACTION_STATES = {
        "pending",
        "executing",
        "executed",
    }

    TERMINAL_TRANSACTION_STATES = {
        "captured",
        "paid",
        "successful",
    }

    def __init__(
        self,
        db: Session,
        dry_run: bool = False,
    ):
        self.db = db
        self.dry_run = dry_run

        self.recovery_service = RecoveryService(
            db=db
        )

        self.executor = RecoveryActionExecutor(
            RazorpayService()
        )

        embedding_service = (
            GeminiEmbeddingService()
        )

        retrieval_service = (
            PolicyRetrievalService(
                db=db,
                embedding_service=embedding_service,
            )
        )

        self.ai_service = AIRecoveryService(
            db=db,
            retrieval_service=retrieval_service,
            safety_gate=DecisionSafetyGate(),
        )

        self.decision_agent = (
            RecoveryDecisionAgent()
        )

    # =========================================================
    # EXECUTE RECOVERY ACTION
    # =========================================================

    def execute_action(
        self,
        action: RecoveryAction,
        recovery_case: RecoveryCase,
        transaction: Transaction,
    ) -> RecoveryAction:

        # =====================================================
        # 0. BASIC IDEMPOTENCY
        # =====================================================

        if action.executed_at is not None:
            return action

        if action.status != "pending":
            return action

        # =====================================================
        # 1. TRANSACTION STATE PROTECTION
        # =====================================================

        transaction_status = (
            transaction.status or ""
        ).lower()

        if (
            transaction_status
            in self.TERMINAL_TRANSACTION_STATES
        ):
            action.status = "failed"

            action.result = (
                "Recovery action stopped because the "
                "underlying transaction is already "
                f"in terminal payment state "
                f"'{transaction.status}'."
            )

            if recovery_case.status != "recovered":
                recovery_case.status = "recovered"

            self.db.flush()

            return action

        # =====================================================
        # 2. RECOVERY CASE STATE PROTECTION
        # =====================================================

        if (
            recovery_case.status
            in self.TERMINAL_CASE_STATES
        ):
            action.status = "failed"

            action.result = (
                "Recovery action stopped because the "
                "recovery case is already in terminal "
                f"status '{recovery_case.status}'."
            )

            self.db.flush()

            return action

        # =====================================================
        # 3. ACTIVE ACTION PROTECTION
        # =====================================================

        active_action = (
            self._find_other_active_action(
                action=action,
                recovery_case_id=recovery_case.id,
            )
        )

        if active_action is not None:
            action.status = "failed"

            action.result = (
                "Recovery action stopped because another "
                "active recovery action already exists for "
                f"recovery case {recovery_case.id}."
            )

            self.db.flush()

            return action

        # =====================================================
        # 4. AUTOMATED ATTEMPT LIMIT
        # =====================================================

        previous_attempts = (
            self.recovery_service
            .get_recovery_attempt_count(
                recovery_case.id
            )
        )

        if (
            previous_attempts
            >= self.recovery_service.MAX_AUTOMATED_ATTEMPTS
        ):
            action.action_type = "manual_review"
            action.status = "failed"

            action.result = (
                "Recovery automation stopped because the "
                "maximum automated recovery attempt limit "
                "has been reached. Escalated to manual review."
            )

            recovery_case.status = "manual_review"

            self.db.flush()

            return action

        # =====================================================
        # 5. BUILD CONTEXT
        # =====================================================

        context = self.ai_service.build_context(
            transaction=transaction,
            recovery_case=recovery_case,
        )

        # =====================================================
        # 6. RETRIEVE POLICY EVIDENCE
        # =====================================================

        evidence = (
            self.ai_service.retrieve_policy_evidence(
                transaction=transaction,
                recovery_case=recovery_case,
                limit=3,
            )
        )

        if not evidence:
            action.status = "failed"

            action.result = (
                "Recovery stopped because no policy "
                "evidence could be retrieved."
            )

            self.db.flush()

            return action

        # =====================================================
        # 7. FIND EXISTING AI DECISION
        # =====================================================

        existing_audit = self.db.scalar(
            select(AuditLog)
            .where(
                AuditLog.action
                == "recovery_decision"
            )
            .where(
                AuditLog.entity_type
                == "recovery_case"
            )
            .where(
                AuditLog.entity_id
                == str(recovery_case.id)
            )
            .order_by(
                AuditLog.id.desc()
            )
        )

        decision = None

        # =====================================================
        # 8. REUSE EXISTING AI DECISION
        # =====================================================

        if existing_audit is not None:

            try:
                audit_data = json.loads(
                    existing_audit.metadata_json
                    or "{}"
                )

                ai_data = audit_data.get(
                    "ai_decision",
                    {},
                )

                stored_context = audit_data.get(
                    "transaction_context",
                    {},
                )

                # ---------------------------------------------
                # Verify that the stored decision belongs to
                # the same transaction.
                # ---------------------------------------------

                same_transaction = (
                    str(
                        stored_context.get(
                            "transaction_id"
                        )
                    )
                    == str(transaction.id)
                )

                if not same_transaction:
                    print(
                        "Existing AI decision belongs to "
                        "another transaction. Generating "
                        "a new decision."
                    )

                else:
                    decision = RecoveryDecision(
                        classification=ai_data[
                            "classification"
                        ],
                        recoverability=ai_data[
                            "recoverability"
                        ],
                        recommended_action=ai_data[
                            "recommended_action"
                        ],
                        confidence=float(
                            ai_data[
                                "confidence"
                            ]
                        ),
                        reason=ai_data[
                            "reason"
                        ],
                        policy_references=(
                            ai_data.get(
                                "policy_references",
                                [],
                            )
                        ),
                    )

                    print(
                        "Existing AI recovery decision "
                        f"found for recovery case "
                        f"{recovery_case.id}. "
                        "Reusing decision."
                    )

            except (
                KeyError,
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ):
                print(
                    "Existing AI audit could not be "
                    "reconstructed. Generating a new "
                    "decision."
                )

                decision = None

        # =====================================================
        # 9. GENERATE AI DECISION
        # =====================================================

        if decision is None:
            decision = self.decision_agent.decide(
                transaction_context=context,
                policy_evidence=evidence,
                use_cache=True,
            )

        # =====================================================
        # 10. DETERMINISTIC SAFETY GATE
        # =====================================================

        try:
            validated_decision = (
                self.ai_service.validate_decision(
                    decision=decision,
                    transaction=transaction,
                    recovery_case=recovery_case,
                    evidence=evidence,
                )
            )

        except Exception as exc:

            action.status = "failed"

            action.result = (
                "AI recovery decision rejected by the "
                f"safety gate: {exc}"
            )

            recovery_case.status = "manual_review"

            self.db.flush()

            return action

        # =====================================================
        # 11. RECORD AI DECISION PROVENANCE
        # =====================================================

        if existing_audit is None:

            evidence_metadata = []

            for item in evidence:
                evidence_metadata.append(
                    {
                        "document_id": (
                            item.document.id
                        ),
                        "document_name": (
                            item.document.name
                        ),
                        "document_version": (
                            item.document.version
                        ),
                        "chunk_id": (
                            item.chunk.id
                        ),
                        "similarity": (
                            item.similarity
                        ),
                    }
                )

            audit_metadata = {
                "transaction_context": context,

                "ai_decision": {
                    "classification": (
                        decision.classification
                    ),
                    "recoverability": (
                        decision.recoverability
                    ),
                    "recommended_action": (
                        decision.recommended_action
                    ),
                    "confidence": (
                        decision.confidence
                    ),
                    "reason": (
                        decision.reason
                    ),
                    "policy_references": (
                        decision.policy_references
                    ),
                },

                "policy_evidence": (
                    evidence_metadata
                ),

                "safety_gate": {
                    "final_action": (
                        validated_decision
                        .recommended_action
                    ),
                    "final_confidence": (
                        validated_decision
                        .confidence
                    ),
                    "final_reason": (
                        validated_decision
                        .reason
                    ),
                },
            }

            audit_log = AuditLog(
                actor_type="ai_agent",
                action="recovery_decision",
                entity_type="recovery_case",
                entity_id=str(
                    recovery_case.id
                ),
                reason=(
                    validated_decision.reason
                ),
                metadata_json=json.dumps(
                    audit_metadata,
                    default=str,
                ),
            )

            self.db.add(
                audit_log
            )

            self.db.flush()

        # =====================================================
        # 12. APPLY FINAL SAFETY-APPROVED ACTION
        # =====================================================

        action.action_type = (
            validated_decision
            .recommended_action
        )

        # =====================================================
        # 13. MANUAL REVIEW
        # =====================================================

        if (
            validated_decision
            .recommended_action
            == "manual_review"
        ):

            action.status = "failed"

            action.result = (
                "Recovery escalated to manual review "
                "by the AI decision safety pipeline."
            )

            recovery_case.status = (
                "manual_review"
            )

            self.db.flush()

            return action

        # =====================================================
        # 14. EXECUTOR CAPABILITY CHECK
        # =====================================================

        if (
            action.action_type
            not in self.executor.SUPPORTED_ACTIONS
        ):
            action.status = "failed"

            action.result = (
                "AI selected an action that is not "
                "currently supported by the execution "
                "layer. Recovery was stopped safely."
            )

            self.db.flush()

            return action

        # =====================================================
        # 15. FINAL STATE CHECK BEFORE EXTERNAL EXECUTION
        # =====================================================

        # The transaction may have changed while the AI
        # decision was being generated.

        self.db.refresh(transaction)
        self.db.refresh(recovery_case)
        self.db.refresh(action)

        if (
            (
                transaction.status or ""
            ).lower()
            in self.TERMINAL_TRANSACTION_STATES
        ):
            action.status = "failed"

            action.result = (
                "Recovery stopped before external execution "
                "because the transaction reached a terminal "
                f"state '{transaction.status}'."
            )

            recovery_case.status = "recovered"

            self.db.flush()

            return action

        if (
            recovery_case.status
            in self.TERMINAL_CASE_STATES
        ):
            action.status = "failed"

            action.result = (
                "Recovery stopped before external execution "
                "because the recovery case reached terminal "
                f"status '{recovery_case.status}'."
            )

            self.db.flush()

            return action

        # =====================================================
        # 16. DRY RUN
        # =====================================================

        if self.dry_run:

            action.result = (
                "AI recovery decision approved. "
                "Dry-run mode prevented external "
                "payment execution."
            )

            self.db.flush()

            return action

        # =====================================================
        # 17. EXECUTE APPROVED ACTION
        # =====================================================

        executed_action = (
            self.executor.execute(
                action=action,
                recovery_case=recovery_case,
                transaction=transaction,
            )
        )

        self.db.flush()

        return executed_action

    # =========================================================
    # FIND OTHER ACTIVE ACTION
    # =========================================================

    def _find_other_active_action(
        self,
        *,
        action: RecoveryAction,
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
            .where(
                RecoveryAction.id
                != action.id
            )
            .where(
                RecoveryAction.status.in_(
                    list(
                        self.ACTIVE_ACTION_STATES
                    )
                )
            )
            .order_by(
                RecoveryAction.id.asc()
            )
        )

        return self.db.scalar(
            statement
        )