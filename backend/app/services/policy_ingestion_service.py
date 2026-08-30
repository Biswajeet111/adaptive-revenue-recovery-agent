import hashlib
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.policy_document import PolicyDocument
from backend.app.models.policy_chunk import PolicyChunk
from backend.app.services.embedding_service import (
    GeminiEmbeddingService,
)


class PolicyIngestionService:

    def __init__(
        self,
        db: Session,
        embedding_service: GeminiEmbeddingService,
    ):
        self.db = db
        self.embedding_service = embedding_service

    def ingest_file(
        self,
        file_path: str | Path,
        version: str = "1.0",
    ) -> PolicyDocument:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Policy file not found: {path}"
            )

        content = path.read_text(
            encoding="utf-8"
        ).strip()

        if not content:
            raise ValueError(
                f"Policy file is empty: {path}"
            )

        content_hash = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

        existing = self.db.scalar(
            select(PolicyDocument).where(
                PolicyDocument.content_hash
                == content_hash
            )
        )

        if existing:
            return existing

        name = path.stem.replace(
            "_",
            " ",
        ).title()

        document = PolicyDocument(
            name=name,
            version=version,
            source=str(path),
            content_hash=content_hash,
            content=content,
        )

        self.db.add(document)
        self.db.flush()

        chunks = self._chunk_document(content)

        for index, chunk in enumerate(chunks):

            embedding = (
                self.embedding_service.embed(
                    chunk
                )
            )

            policy_chunk = PolicyChunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk,
                metadata_json=json.dumps(
                    {
                        "document_name": name,
                        "version": version,
                        "source": str(path),
                        "chunk_index": index,
                    }
                ),
                embedding=embedding,
            )

            self.db.add(policy_chunk)

        self.db.flush()

        return document

    @staticmethod
    def _chunk_document(
        content: str,
    ) -> list[str]:

        lines = content.splitlines()

        chunks: list[str] = []
        current: list[str] = []

        for line in lines:

            if line.startswith("## ") and current:
                chunk = "\n".join(
                    current
                ).strip()

                if chunk:
                    chunks.append(chunk)

                current = []

            current.append(line)

        if current:
            chunk = "\n".join(
                current
            ).strip()

            if chunk:
                chunks.append(chunk)

        return chunks