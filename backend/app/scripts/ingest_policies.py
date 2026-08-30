from pathlib import Path

from backend.app.database import SessionLocal
from backend.app.services.embedding_service import (
    GeminiEmbeddingService,
)
from backend.app.services.policy_ingestion_service import (
    PolicyIngestionService,
)


def main():

    db = SessionLocal()

    try:
        embedding_service = (
            GeminiEmbeddingService()
        )

        ingestion_service = (
            PolicyIngestionService(
                db=db,
                embedding_service=embedding_service,
            )
        )

        policies_dir = (
            Path(__file__).resolve().parents[3]
            / "policies"
        )

        policy_files = sorted(
            policies_dir.glob("*.md")
        )

        if not policy_files:
            raise RuntimeError(
                "No policy files found."
            )

        for policy_file in policy_files:

            print(
                f"Ingesting: {policy_file.name}"
            )

            document = (
                ingestion_service.ingest_file(
                    file_path=policy_file,
                    version="1.0",
                )
            )

            print(
                f"  Document ID: {document.id}"
            )

        db.commit()

        print(
            "Policy ingestion completed successfully."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()