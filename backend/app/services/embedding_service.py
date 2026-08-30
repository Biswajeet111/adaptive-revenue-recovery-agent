from google import genai
from google.genai import types

from backend.app.config import settings


class GeminiEmbeddingService:

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )
        self.model = settings.gemini_embedding_model

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError(
                "Cannot generate an embedding for empty text."
            )

        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=1536,
            ),
        )

        if not response.embeddings:
            raise ValueError(
                "Gemini returned no embedding."
            )

        values = response.embeddings[0].values

        if not values:
            raise ValueError(
                "Gemini returned an empty embedding."
            )

        if len(values) != 1536:
            raise ValueError(
                f"Expected 1536-dimensional embedding, "
                f"received {len(values)} dimensions."
            )

        return list(values)