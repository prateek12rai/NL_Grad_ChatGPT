"""
Phase 4.5 / Phase 5 preview — offline retrieval from local Chroma (architecture §12).
"""

from __future__ import annotations

from pipeline.embeddings import BgeEmbeddingClient, l2_normalize
from pipeline.index.chroma_store import ChromaStore
from shared.schemas import ChunkMetadata, SourceOrg, VerificationStatus


def parse_chunk_metadata(meta: dict) -> ChunkMetadata:
    """Build ``ChunkMetadata`` from Chroma metadata dict."""
    return ChunkMetadata(
        chunk_id=str(meta["chunk_id"]),
        source_org=SourceOrg(meta["source_org"]),
        source_url=str(meta["source_url"]),
        document_title=str(meta["document_title"]),
        publication_year=int(meta["publication_year"]),
        page_number=int(meta["page_number"]),
        exact_context=str(meta["exact_context"]),
        verification_status=VerificationStatus(meta["verification_status"]),
    )


def retrieve(
    query: str,
    *,
    top_k: int = 8,
    store: ChromaStore | None = None,
    embed_client: BgeEmbeddingClient | None = None,
) -> list[ChunkMetadata]:
    """
    Local similarity search — no remote vector DB at query time.

    Uses ``query: `` BGE prefix + L2-normalized query embedding.
    """
    chroma = store or ChromaStore()
    client = embed_client or BgeEmbeddingClient()
    query_vec = l2_normalize(client.embed_query(query))
    n_results = min(top_k, max(chroma.count(), 1))
    if chroma.count() == 0:
        return []

    results = chroma.query_by_embedding(query_vec, n_results=n_results)
    metadatas = results.get("metadatas") or [[]]
    if not metadatas or not metadatas[0]:
        return []
    return [parse_chunk_metadata(m) for m in metadatas[0]]
