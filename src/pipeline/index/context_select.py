"""Select diverse, high-quality chunks for LLM context."""

from __future__ import annotations

from pipeline.index.retrieval import ScoredChunk
from shared.config import settings
from shared.document_titles import is_low_quality_title, resolve_document_title


def enrich_chunk_title(chunk):
    """Return chunk metadata with a readable title when ingest used placeholders."""
    resolved = resolve_document_title(
        chunk.document_title,
        chunk.source_url,
        chunk.exact_context,
    )
    if resolved == chunk.document_title:
        return chunk
    return chunk.model_copy(update={"document_title": resolved})


def is_low_quality_chunk(chunk) -> bool:
    enriched = enrich_chunk_title(chunk)
    if is_low_quality_title(enriched.document_title):
        return True
    if len((chunk.exact_context or "").strip()) < 40:
        return True
    return False


def select_context_chunks(
    hits: list[ScoredChunk],
    *,
    max_chunks: int | None = None,
    max_per_document: int | None = None,
    min_similarity: float | None = None,
) -> list[ScoredChunk]:
    """
    Keep the best chunks with at most ``max_per_document`` per source document.
    """
    cap = max_chunks or settings.rag_context_chunks
    per_doc = max_per_document or settings.rag_max_per_document
    min_sim = (
        min_similarity
        if min_similarity is not None
        else settings.rag_min_similarity
    )

    selected: list[ScoredChunk] = []
    per_doc_count: dict[str, int] = {}

    for hit in hits:
        if hit.similarity < min_sim and not settings.embed_mock:
            continue
        chunk = enrich_chunk_title(hit.chunk)
        if is_low_quality_chunk(chunk):
            continue
        doc_key = chunk.chunk_id.split("::")[0] if "::" in chunk.chunk_id else chunk.document_title
        doc_key = doc_key or chunk.chunk_id
        if per_doc_count.get(doc_key, 0) >= per_doc:
            continue
        selected.append(ScoredChunk(chunk=chunk, distance=hit.distance))
        per_doc_count[doc_key] = per_doc_count.get(doc_key, 0) + 1
        if len(selected) >= cap:
            break

    return selected
