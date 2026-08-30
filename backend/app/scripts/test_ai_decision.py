from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.ai_recovery_service import (
    AIRecoveryService,
)
from backend.app.services.decision_agent import (
    RecoveryDecisionAgent,
)
from backend.app.services.decision_safety_gate import (
    DecisionSafetyGate,
)
from backend.app.services.embedding_service import (
    GeminiEmbeddingService,
)
from backend.app.services.policy_retrieval_service import (
    PolicyRetrievalService,
)


def main():

    db = SessionLocal()

    try:
        # =====================================================
        # 1. Find newest open recovery case
        # =====================================================

        recovery_case = db.scalar(
            select(RecoveryCase)
            .where(
                RecoveryCase.status == "open"
            )
            .order_by(
                RecoveryCase.id.desc()
            )
        )

        if recovery_case is None:
            raise RuntimeError(
                "No open recovery case was found."
            )

        # =====================================================
        # 2. Find transaction
        # =====================================================

        transaction = db.scalar(
            select(Transaction)
            .where(
                Transaction.id
                == recovery_case.transaction_id
            )
        )

        if transaction is None:
            raise RuntimeError(
                "Transaction for the selected "
                "recovery case was not found."
            )

        # =====================================================
        # 3. Initialize AI services
        # =====================================================

        embedding_service = (
            GeminiEmbeddingService()
        )

        retrieval_service = (
            PolicyRetrievalService(
                db=db,
                embedding_service=embedding_service,
            )
        )

        safety_gate = DecisionSafetyGate()

        ai_service = AIRecoveryService(
            db=db,
            retrieval_service=retrieval_service,
            safety_gate=safety_gate,
        )

        # =====================================================
        # 4. Retrieve policy evidence
        # =====================================================

        evidence = (
            ai_service.retrieve_policy_evidence(
                transaction=transaction,
                recovery_case=recovery_case,
                limit=3,
            )
        )

        if not evidence:
            raise RuntimeError(
                "No policy evidence was retrieved."
            )

        # =====================================================
        # 5. Build AI transaction context
        # =====================================================

        context = ai_service.build_context(
            transaction=transaction,
            recovery_case=recovery_case,
        )

        print(
            "=== AI RECOVERY CONTEXT ==="
        )

        for key, value in context.items():
            print(
                f"{key}: {value}"
            )

        print()
        print(
            "=== POLICY EVIDENCE ==="
        )

        for index, item in enumerate(
            evidence,
            start=1,
        ):
            print(
                f"{index}. "
                f"{item.document.name} "
                f"v{item.document.version} "
                f"(similarity="
                f"{item.similarity:.4f})"
            )

        # =====================================================
        # 6. Obtain AI decision
        # =====================================================

        print()
        print(
            "=== GROQ DECISION ==="
        )

        agent = RecoveryDecisionAgent()

        decision = agent.decide(
            transaction_context=context,
            policy_evidence=evidence,
            use_cache=True,
        )

        print(
            f"Classification: "
            f"{decision.classification}"
        )

        print(
            f"Recoverability: "
            f"{decision.recoverability}"
        )

        print(
            f"Recommended action: "
            f"{decision.recommended_action}"
        )

        print(
            f"Confidence: "
            f"{decision.confidence}"
        )

        print(
            f"Reason: "
            f"{decision.reason}"
        )

        print(
            "Policy references:"
        )

        for reference in (
            decision.policy_references
        ):
            print(
                f"  - {reference}"
            )

        # =====================================================
        # 7. Deterministic safety gate
        # =====================================================

        print()
        print(
            "=== SAFETY GATE ==="
        )

        validated = (
            ai_service.validate_decision(
                decision=decision,
                transaction=transaction,
                recovery_case=recovery_case,
                evidence=evidence,
            )
        )

        print(
            f"Final action: "
            f"{validated.recommended_action}"
        )

        print(
            f"Final confidence: "
            f"{validated.confidence}"
        )

        print(
            f"Final reason: "
            f"{validated.reason}"
        )

        print()
        print(
            "AI RECOVERY DECISION PIPELINE PASSED."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()