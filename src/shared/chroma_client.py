"""Local Chroma PersistentClient helper — delegates to Phase 4.3 pipeline.index."""

from __future__ import annotations

from chromadb.api.models.Collection import Collection

from pipeline.index.chroma_store import (
    COLLECTION_METADATA,
    get_chroma_client,
    get_medical_collection,
)
from shared.config import settings

COLLECTION_NAME = settings.chroma_collection_name


def get_or_create_collection() -> Collection:
    """Backward-compatible entry for Phase 1 health check and API."""
    return get_medical_collection()


def chroma_health_check() -> str:
    """Verify local collection is reachable."""
    get_or_create_collection()
    return "reachable"


__all__ = [
    "COLLECTION_NAME",
    "COLLECTION_METADATA",
    "get_chroma_client",
    "get_or_create_collection",
    "chroma_health_check",
]
