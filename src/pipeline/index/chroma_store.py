"""
Phase 4.3 — Chroma PersistentClient + medical collection (architecture §9).
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection

from pipeline.embeddings.normalize import is_unit_vector
from pipeline.index.mapper import build_upsert_payload
from shared.config import settings
from shared.schemas import ChunkRecord

_BASE_COLLECTION_METADATA: dict[str, str] = {
    "hnsw:space": "cosine",
    "schema_version": "1",
}

# Backwards-compatible export (embedding metadata is dynamic in get_medical_collection)
COLLECTION_METADATA = _BASE_COLLECTION_METADATA


def get_chroma_client(path: Path | str | None = None) -> chromadb.PersistentClient:
    """Local disk client — ``CHROMA_PATH`` overrides default ``./chroma_db``."""
    if path is not None:
        resolved = Path(path).resolve()
    else:
        resolved = settings.chroma_path_resolved
    resolved.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(resolved))


def get_medical_collection(
    client: chromadb.PersistentClient | None = None,
    *,
    name: str | None = None,
) -> Collection:
    """PRD collection ``india_medical_local`` with cosine HNSW space."""
    chroma = client or get_chroma_client()
    embedding_model = (
        f"mock:{settings.embed_model_id}" if settings.embed_mock else settings.embed_model_id
    )
    metadata = dict(_BASE_COLLECTION_METADATA)
    metadata.update({"embedding_model": embedding_model, "embed_mock": str(settings.embed_mock).lower()})
    return chroma.get_or_create_collection(
        name=name or settings.chroma_collection_name,
        metadata=metadata,
    )


class ChromaStore:
    """Thin wrapper for upsert/read against the medical collection."""

    def __init__(self, path: Path | str | None = None) -> None:
        self._client = get_chroma_client(path)
        self._collection = get_medical_collection(self._client)

    @property
    def client(self) -> chromadb.PersistentClient:
        return self._client

    @property
    def collection(self) -> Collection:
        return self._collection

    @property
    def collection_name(self) -> str:
        return self._collection.name

    def count(self) -> int:
        return self._collection.count()

    def upsert_chunk(
        self,
        chunk: ChunkRecord,
        embedding: list[float],
        *,
        require_unit_vector: bool = True,
    ) -> None:
        self.upsert_chunks([chunk], [embedding], require_unit_vector=require_unit_vector)

    def upsert_chunks(
        self,
        chunks: list[ChunkRecord],
        embeddings: list[list[float]],
        *,
        require_unit_vector: bool = True,
    ) -> None:
        if require_unit_vector:
            for vector in embeddings:
                if not is_unit_vector(vector):
                    raise ValueError(
                        "Embeddings must be L2-normalized before Chroma upsert (Phase 4.2)"
                    )
        payload = build_upsert_payload(chunks, embeddings)
        if payload["ids"]:
            self._collection.upsert(**payload)

    def get_chunk_metadata(self, chunk_id: str) -> dict | None:
        result = self._collection.get(ids=[chunk_id], include=["metadatas"])
        ids = result.get("ids") or []
        if not ids:
            return None
        metadatas = result.get("metadatas") or []
        return metadatas[0] if metadatas else None

    def chunk_exists(self, chunk_id: str) -> bool:
        return self.get_chunk_metadata(chunk_id) is not None

    def list_chunk_ids(self) -> list[str]:
        result = self._collection.get(include=[])
        return list(result.get("ids") or [])

    def delete_ids(self, chunk_ids: list[str]) -> int:
        if not chunk_ids:
            return 0
        self._collection.delete(ids=chunk_ids)
        return len(chunk_ids)

    def delete_for_document_ids(self, document_ids: list[str]) -> int:
        """Remove all vectors whose ``chunk_id`` starts with ``{document_id}::``."""
        if not document_ids:
            return 0
        prefixes = tuple(f"{doc_id}::" for doc_id in document_ids)
        to_delete = [cid for cid in self.list_chunk_ids() if cid.startswith(prefixes)]
        return self.delete_ids(to_delete)

    def query_by_embedding(
        self,
        query_embedding: list[float],
        *,
        n_results: int = 5,
    ) -> dict:
        """Similarity search — offline local only (Phase 5 preview)."""
        if not is_unit_vector(query_embedding):
            raise ValueError("Query embedding must be L2-normalized")
        return self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["metadatas", "documents", "distances"],
        )
