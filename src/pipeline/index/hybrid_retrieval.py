"""Choose vector or lexical retrieval based on index/query embedding compatibility."""

from __future__ import annotations

import logging

from pipeline.index.context_select import select_context_chunks
from pipeline.index.index_profile import index_has_live_embeddings, query_embedding_compatible
from pipeline.index.lexical import retrieve_lexical
from pipeline.index.manifest_search import retrieve_from_manifest
from pipeline.index.retrieval import ScoredChunk, retrieve_scored
from pipeline.index.chroma_store import ChromaStore
from pipeline.embeddings import BgeEmbeddingClient
from shared.config import settings

logger = logging.getLogger(__name__)


def retrieval_mode(store: ChromaStore | None = None) -> str:
    if query_embedding_compatible(store):
        return "vector"
    if index_has_live_embeddings(store):
        return "lexical"
    return "vector"


def retrieve_for_rag(
    query: str,
    *,
    top_k: int | None = None,
    store: ChromaStore | None = None,
    embed_client: BgeEmbeddingClient | None = None,
    analysis=None,
    document_id: str | None = None,
) -> tuple[list[ScoredChunk], str]:
    """
    Retrieve ranked chunks, then narrow to diverse context set.

    Returns (context_chunks, mode) where mode is ``vector`` or ``lexical``.
    """
    chroma = store or ChromaStore()
    k = top_k or settings.rag_top_k
    fetch_k = max(k * 2, 12)

    if document_id:
        hits = retrieve_lexical(query, top_k=fetch_k, document_id=document_id)
        if not hits:
            hits = retrieve_scored(
                query,
                top_k=fetch_k,
                store=chroma,
                embed_client=embed_client,
                document_id=document_id,
            )
        context = select_context_chunks(hits, min_similarity=0.0)
        return context, "document"

    if analysis is not None and getattr(analysis, "enumeration", False):
        if getattr(analysis, "source_org", None) or getattr(analysis, "target_date", None):
            manifest_hits = retrieve_from_manifest(
                source_org=getattr(analysis, "source_org", None),
                target_date=getattr(analysis, "target_date", None),
                max_documents=min(5, settings.rag_max_citations),
            )
            if manifest_hits:
                return manifest_hits, "manifest"

    mode = retrieval_mode(chroma)

    if mode == "lexical":
        logger.info("rag_retrieval mode=lexical (embed_mock=%s, live_index=True)", settings.embed_mock)
        hits = retrieve_lexical(query, top_k=fetch_k, document_id=document_id)
    else:
        hits = retrieve_scored(
            query,
            top_k=fetch_k,
            store=chroma,
            embed_client=embed_client,
            document_id=document_id,
        )

    if mode == "lexical":
        context = select_context_chunks(hits, min_similarity=0.0)
    else:
        context = select_context_chunks(hits)
        if not context and index_has_live_embeddings(chroma):
            logger.warning("rag_retrieval vector_miss; falling back to lexical")
            hits = retrieve_lexical(query, top_k=fetch_k)
            context = select_context_chunks(hits, min_similarity=0.0)
            mode = "lexical"

    return context, mode
