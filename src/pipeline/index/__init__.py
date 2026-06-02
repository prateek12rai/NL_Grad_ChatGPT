"""Phase 4 — Chroma index (local vector store)."""

from pipeline.index.chroma_store import (
    COLLECTION_METADATA,
    ChromaStore,
    get_chroma_client,
    get_medical_collection,
)
from pipeline.index.mapper import build_upsert_payload, chunk_to_chroma_metadata
from pipeline.index.orchestrator import IndexOrchestrator, IndexResult
from pipeline.index.retriever import parse_chunk_metadata, retrieve
from pipeline.index.verify import VerifyReport, verify_chroma_index

__all__ = [
    "COLLECTION_METADATA",
    "ChromaStore",
    "get_chroma_client",
    "get_medical_collection",
    "build_upsert_payload",
    "chunk_to_chroma_metadata",
    "IndexOrchestrator",
    "IndexResult",
    "retrieve",
    "parse_chunk_metadata",
    "verify_chroma_index",
    "VerifyReport",
]
