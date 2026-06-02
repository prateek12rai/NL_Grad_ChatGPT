"""Detect how the local Chroma index was built (live BGE vs mock)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from shared.config import settings

if TYPE_CHECKING:
    from pipeline.index.chroma_store import ChromaStore

_STATS_PATH = Path("data/chroma_stats.json")
_LIVE_MODEL_PREFIX = "BAAI/"


def read_index_stats() -> dict | None:
    path = Path(settings.chunk_index_path).parent.parent / "chroma_stats.json"
    if not path.is_file():
        path = _STATS_PATH
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def index_has_live_embeddings(store: ChromaStore | None = None) -> bool:
    """True when the open Chroma collection matches a live BGE production index."""
    from pipeline.index.chroma_store import ChromaStore

    chroma = store or ChromaStore()
    if chroma.count() == 0:
        return False
    meta = chroma.collection.metadata or {}
    model = str(meta.get("embedding_model", ""))
    if not model.startswith(_LIVE_MODEL_PREFIX):
        return False
    stats = read_index_stats()
    if not stats:
        return chroma.count() > 0
    stats_vectors = int(stats.get("total_vectors", 0) or 0)
    if stats_vectors <= 0:
        return False
    if abs(chroma.count() - stats_vectors) > max(20, int(stats_vectors * 0.05)):
        return False
    return True


def query_embedding_compatible(store: ChromaStore | None = None) -> bool:
    """
    True when query-time embeddings match the indexed vectors.

    Mock query vectors against a live BGE index produce meaningless rankings.
    """
    if settings.embed_mock:
        return not index_has_live_embeddings(store)
    return bool(settings.huggingface_api_token)
