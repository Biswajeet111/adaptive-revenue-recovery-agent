from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.ai_recovery_service import (
    AIRecoveryService,
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
        recovery_case = db.scalar(
            select(RecoveryCase)
            .where(RecoveryCase.id == 3)
        )

        if recovery_case is None:
            raise RuntimeError(
                "Recovery case 3 was not found."
            )

        transaction = db.scalar(
            select(Transaction)
            .where(
                Transaction.id
                == recovery_case.transaction_id
            )
        )

        if transaction is None:
            raise RuntimeError(
                "Transaction for recovery case "
                "3 was not found."
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

        safety_gate = (
            DecisionSafetyGate()
        )

        service = AIRecoveryService(
            db=db,
            retrieval_service=retrieval_service,
            safety_gate=safety_gate,
        )

        context = service.build_context(
            transaction=transaction,
            recovery_case=recovery_case,
        )

        print(
            "=== TRANSACTION CONTEXT ==="
        )

        for key, value in context.items():
            print(
                f"{key}: {value}"
            )

        print()
        print(
            "=== POLICY EVIDENCE ==="
        )

        evidence = (
            service.retrieve_policy_evidence(
                transaction=transaction,
                recovery_case=recovery_case,
                limit=3,
            )
        )

        for index, item in enumerate(
            evidence,
            start=1,
        ):
            print()
            print(
                f"Evidence {index}"
            )
            print(
                f"Document: "
                f"{item.document.name}"
            )
            print(
                f"Version: "
                f"{item.document.version}"
            )
            print(
                f"Similarity: "
                f"{item.similarity:.4f}"
            )

        print()
        print(
            "AI Recovery Service context and "
            "policy retrieval are working."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()