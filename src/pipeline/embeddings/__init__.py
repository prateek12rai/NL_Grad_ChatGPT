"""Phase 4 — embeddings (HF BGE) and helpers."""

from pipeline.embeddings.bge_client import (
    BgeEmbeddingClient,
    DEFAULT_DIMENSION,
    DEFAULT_MODEL_ID,
    PASSAGE_PREFIX,
    QUERY_PREFIX,
    mock_embedding_vector,
)
from pipeline.embeddings.batch_planner import plan_batches
from pipeline.embeddings.exceptions import (
    EmbeddingAuthError,
    EmbeddingError,
    EmbeddingRateLimitError,
)
from pipeline.embeddings.normalize import (
    L2_TOLERANCE,
    is_unit_vector,
    l2_norm,
    l2_normalize,
    l2_normalize_batch,
)

__all__ = [
    "BgeEmbeddingClient",
    "DEFAULT_DIMENSION",
    "DEFAULT_MODEL_ID",
    "PASSAGE_PREFIX",
    "QUERY_PREFIX",
    "mock_embedding_vector",
    "plan_batches",
    "EmbeddingError",
    "EmbeddingAuthError",
    "EmbeddingRateLimitError",
    "L2_TOLERANCE",
    "l2_norm",
    "l2_normalize",
    "l2_normalize_batch",
    "is_unit_vector",
]
