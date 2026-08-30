from backend.app.database import SessionLocal
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
            "What should the system do when a "
            "customer's payment is declined by the bank?"
        )

        results = retrieval_service.retrieve(
            query=query,
            limit=3,
        )

        print(
            f"Retrieved {len(results)} policy evidence items."
        )

        for index, evidence in enumerate(
            results,
            start=1,
        ):
            print()
            print(
                f"--- Evidence {index} ---"
            )

            print(
                f"Document: {evidence.document.name}"
            )

            print(
                f"Version: {evidence.document.version}"
            )

            print(
                f"Chunk ID: {evidence.chunk.id}"
            )

            print(
                f"Similarity: "
                f"{evidence.similarity:.4f}"
            )

            print(
                "Content:"
            )

            print(
                evidence.chunk.content
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()