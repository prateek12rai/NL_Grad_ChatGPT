"""
Phase 4.1 — Hugging Face BGE-large embedding client.

Uses ``huggingface_hub.InferenceClient`` for live calls; ``EMBED_MOCK=true`` for tests.
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

from pipeline.embeddings.batch_planner import plan_batches
from pipeline.embeddings.exceptions import (
    EmbeddingAuthError,
    EmbeddingError,
    EmbeddingRateLimitError,
)
from shared.config import settings

logger = logging.getLogger(__name__)

PASSAGE_PREFIX = "passage: "
QUERY_PREFIX = "query: "
DEFAULT_MODEL_ID = "BAAI/bge-large-en-v1.5"
DEFAULT_DIMENSION = 1024
MAX_RETRIES = 3
RETRY_BASE_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 60


def _prefixed_passage(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith(PASSAGE_PREFIX):
        return stripped
    return f"{PASSAGE_PREFIX}{stripped}"


def _prefixed_query(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith(QUERY_PREFIX):
        return stripped
    return f"{QUERY_PREFIX}{stripped}"


def mock_embedding_vector(text: str, dimension: int | None = None) -> list[float]:
    """
    Deterministic vector from SHA-256(text) — architecture §7.5 mock mode.
    Not L2-normalized (Phase 4.2 applies normalization before Chroma write).
    """
    dim = dimension or settings.bge_dimension or DEFAULT_DIMENSION
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    while len(values) < dim:
        for byte in seed:
            values.append((byte / 127.5) - 1.0)
            if len(values) >= dim:
                break
        seed = hashlib.sha256(seed).digest()
    return values[:dim]


def _parse_single_embedding(response: Any) -> list[float]:
    """Normalize HF feature-extraction response shapes to a flat float list."""
    if isinstance(response, list):
        if not response:
            raise EmbeddingError("Empty embedding response from Hugging Face")
        if isinstance(response[0], (int, float)):
            return [float(x) for x in response]
        if isinstance(response[0], list):
            return [float(x) for x in response[0]]
    raise EmbeddingError(f"Unexpected embedding response type: {type(response)!r}")


def _parse_batch_embeddings(response: Any, expected: int) -> list[list[float]]:
    if isinstance(response, list) and response:
        if isinstance(response[0], (int, float)):
            if expected != 1:
                raise EmbeddingError("Expected batch embeddings but received a single vector")
            return [_parse_single_embedding(response)]
        if isinstance(response[0], list):
            if isinstance(response[0][0], (int, float)):
                return [_parse_single_embedding(row) for row in response]
    raise EmbeddingError(f"Unexpected batch embedding response: {type(response)!r}")


class BgeEmbeddingClient:
    """BAAI/bge-large-en-v1.5 via Hugging Face Inference API (architecture §7)."""

    def __init__(
        self,
        api_token: str | None = None,
        model_id: str | None = None,
        *,
        mock: bool | None = None,
        dimension: int | None = None,
    ) -> None:
        self.model_id = model_id or settings.embed_model_id or DEFAULT_MODEL_ID
        self.api_token = api_token if api_token is not None else settings.huggingface_api_token
        self.mock = settings.embed_mock if mock is None else mock
        self.dimension = dimension or settings.bge_dimension or DEFAULT_DIMENSION
        self._client: Any | None = None

        if not self.mock and not self.api_token:
            raise EmbeddingAuthError(
                "HUGGINGFACE_API_TOKEN is required for live embedding (or set EMBED_MOCK=true)"
            )

    def _get_inference_client(self) -> Any:
        if self._client is None:
            from huggingface_hub import InferenceClient

            self._client = InferenceClient(
                model=self.model_id,
                token=self.api_token,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        return self._client

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        """Batch embed passage texts with ``passage: `` prefix (architecture §7.1)."""
        if not texts:
            return []
        prefixed = [_prefixed_passage(t) for t in texts]
        batches = plan_batches(prefixed)
        vectors: list[list[float]] = []
        for batch in batches:
            vectors.extend(self._embed_batch(batch))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        """Single query embedding with ``query: `` prefix — used in Phase 5."""
        return self._embed_batch([_prefixed_query(text)])[0]

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self.mock:
            return [mock_embedding_vector(t, self.dimension) for t in texts]
        return self._embed_batch_live(texts)

    def _embed_batch_live(self, texts: list[str]) -> list[list[float]]:
        client = self._get_inference_client()
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = client.feature_extraction(texts)
                vectors = _parse_batch_embeddings(response, expected=len(texts))
                if len(vectors) != len(texts):
                    raise EmbeddingError(
                        f"HF returned {len(vectors)} vectors for {len(texts)} inputs"
                    )
                for vector in vectors:
                    if len(vector) != self.dimension:
                        logger.warning(
                            "bge_dimension_mismatch: expected %s got %s — update bge_dimension",
                            self.dimension,
                            len(vector),
                        )
                        self.dimension = len(vector)
                return vectors
            except Exception as exc:
                last_error = exc
                if _is_auth_error(exc):
                    raise EmbeddingAuthError(str(exc)) from exc
                if _is_retryable(exc) and attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_SECONDS * (2**attempt)
                    logger.warning(
                        "hf_embed_retry attempt=%s delay=%.1fs error=%s",
                        attempt + 1,
                        delay,
                        exc,
                    )
                    time.sleep(delay)
                    continue
                break

        if last_error and _is_retryable(last_error):
            raise EmbeddingRateLimitError(str(last_error)) from last_error
        raise EmbeddingError(str(last_error)) from last_error


def _is_auth_error(exc: Exception) -> bool:
    message = str(exc).lower()
    if "401" in message or "unauthorized" in message:
        return True
    try:
        from huggingface_hub.utils import HfHubHTTPError

        if isinstance(exc, HfHubHTTPError) and exc.response is not None:
            return exc.response.status_code == 401
    except ImportError:
        pass
    return False


def _is_retryable(exc: Exception) -> bool:
    message = str(exc).lower()
    if any(token in message for token in ("429", "503", "rate limit", "loading")):
        return True
    try:
        from huggingface_hub.utils import HfHubHTTPError

        if isinstance(exc, HfHubHTTPError) and exc.response is not None:
            return exc.response.status_code in (429, 503)
    except ImportError:
        pass
    return False
