from backend.app.services.embedding_service import (
    GeminiEmbeddingService,
)


def main():
    service = GeminiEmbeddingService()

    text = """
    A bank-declined payment may be recoverable through
    an alternative payment method when an immediate retry
    is unlikely to succeed.
    """

    embedding = service.embed(text)

    print("Embedding generated successfully.")
    print(f"Dimensions: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")


if __name__ == "__main__":
    main()