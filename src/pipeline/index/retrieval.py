"""Retrieval with similarity scores for relevance gating."""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.embeddings import BgeEmbeddingClient, l2_normalize
from pipeline.index.chroma_store import ChromaStore
from pipeline.index.retriever import parse_chunk_metadata
from shared.schemas import ChunkMetadata
from shared.config import settings


@dataclass(frozen=True)
class ScoredChunk:
    chunk: ChunkMetadata
    distance: float

    @property
    def similarity(self) -> float:
        """Cosine similarity (1 - Chroma cosine distance)."""
        return max(0.0, 1.0 - self.distance)


def _chunk_document_id(chunk_id: str) -> str:
    if "::" in chunk_id:
        return chunk_id.split("::", 1)[0]
    return chunk_id


def retrieve_scored(
    query: str,
    *,
    top_k: int | None = None,
    store: ChromaStore | None = None,
    embed_client: BgeEmbeddingClient | None = None,
    max_distance: float | None = None,
    document_id: str | None = None,
) -> list[ScoredChunk]:
    """Return chunks with distances; filter by ``max_distance`` when set."""
    chroma = store or ChromaStore()
    client = embed_client or BgeEmbeddingClient()
    k = top_k or settings.rag_top_k
    limit = max_distance if max_distance is not None else settings.rag_max_distance
    # Mock embeddings are not semantically meaningful — skip strict gating in tests/dev
    if settings.embed_mock:
        limit = 2.0

    if chroma.count() == 0:
        return []

    query_vec = l2_normalize(client.embed_query(query))
    n_results = min(k, chroma.count())
    results = chroma.query_by_embedding(query_vec, n_results=n_results)
    metadatas = results.get("metadatas") or [[]]
    distances = results.get("distances") or [[]]
    if not metadatas[0]:
        return []

    hits: list[ScoredChunk] = []
    for meta, dist in zip(metadatas[0], distances[0]):
        if dist <= limit:
            chunk = parse_chunk_metadata(meta)
            if document_id and _chunk_document_id(chunk.chunk_id) != document_id:
                continue
            hits.append(ScoredChunk(chunk=chunk, distance=dist))
    return hits
