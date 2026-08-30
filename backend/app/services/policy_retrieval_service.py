from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.policy_chunk import PolicyChunk
from backend.app.models.policy_document import PolicyDocument
from backend.app.services.embedding_service import (
    GeminiEmbeddingService,
)


@dataclass
class PolicyEvidence:
    chunk: PolicyChunk
    document: PolicyDocument
    similarity: float


class PolicyRetrievalService:

    def __init__(
        self,
        db: Session,
        embedding_service: GeminiEmbeddingService,
    ):
        self.db = db
        self.embedding_service = embedding_service

    def retrieve(
        self,
        query: str,
        limit: int = 3,
        min_similarity: float = 0.0,
    ) -> list[PolicyEvidence]:

        if not query.strip():
            raise ValueError(
                "Retrieval query cannot be empty."
            )

        if limit < 1:
            raise ValueError(
                "Retrieval limit must be at least 1."
            )

        if not 0.0 <= min_similarity <= 1.0:
            raise ValueError(
                "min_similarity must be between 0 and 1."
            )

        query_embedding = (
            self.embedding_service.embed(query)
        )

        distance = (
            PolicyChunk.embedding.cosine_distance(
                query_embedding
            )
        )

        statement = (
            select(
                PolicyChunk,
                PolicyDocument,
                distance.label("distance"),
            )
            .join(
                PolicyDocument,
                PolicyChunk.document_id
                == PolicyDocument.id,
            )
            .order_by(distance)
            .limit(limit)
        )

        rows = self.db.execute(statement).all()

        evidence: list[PolicyEvidence] = []

        for chunk, document, raw_distance in rows:

            similarity = max(
                0.0,
                min(
                    1.0,
                    1.0 - float(raw_distance),
                ),
            )

            if similarity < min_similarity:
                continue

            evidence.append(
                PolicyEvidence(
                    chunk=chunk,
                    document=document,
                    similarity=similarity,
                )
            )

        return evidence