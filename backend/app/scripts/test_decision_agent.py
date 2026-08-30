from backend.app.database import SessionLocal
from backend.app.services.decision_agent import (
    RecoveryDecisionAgent,
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
        embedding_service = (
            GeminiEmbeddingService()
        )

        retrieval_service = (
            PolicyRetrievalService(
                db=db,
                embedding_service=embedding_service,
            )
        )

        query = (
            "A customer payment was declined by "
            "the bank. What recovery action should "
            "the system take?"
        )

        evidence = retrieval_service.retrieve(
            query=query,
            limit=3,
        )

        agent = RecoveryDecisionAgent()

        decision = agent.decide(
            transaction_context={
                "transaction_id": 999,
                "amount": 100.00,
                "currency": "INR",
                "failure_code": "BAD_REQUEST_ERROR",
                "failure_reason": (
                    "Payment was declined by the bank."
                ),
                "payment_method": "netbanking",
                "previous_recovery_attempts": 0,
            },
            policy_evidence=evidence,
        )

        print()
        print("=== RECOVERY DECISION ===")
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

    finally:
        db.close()


if __name__ == "__main__":
    main()