"""Embedding pipeline errors (architecture-phase-4-embedding.md §16)."""


class EmbeddingError(Exception):
    """Base embedding failure."""


class EmbeddingAuthError(EmbeddingError):
    """Invalid or missing Hugging Face API token."""


class EmbeddingRateLimitError(EmbeddingError):
    """Rate limit or model loading (429 / 503) after retries exhausted."""
