"""Single-article RAG policy — one citation per answer unless count/list intent."""

from __future__ import annotations

import re

from pipeline.index.retrieval import ScoredChunk, _chunk_document_id
from shared.schemas import SourceOrg

from api.rag.constants import CLARIFICATION_MESSAGE
from api.rag.query_analysis import QueryAnalysis, QueryIntent
from api.rag.relevance_gate import is_corpus_enumeration_query


def is_multi_article_intent(analysis: QueryAnalysis, query: str = "") -> bool:
    """Count/list queries may legitimately reference multiple documents."""
    return is_corpus_enumeration_query(query or analysis.raw_query, analysis)


def distinct_documents_in_hits(hits: list[ScoredChunk], top_n: int = 6) -> list[str]:
    order: list[str] = []
    for hit in hits[:top_n]:
        doc_id = _chunk_document_id(hit.chunk.chunk_id)
        if doc_id not in order:
            order.append(doc_id)
    return order


def retrieval_is_ambiguous(
    hits: list[ScoredChunk],
    analysis: QueryAnalysis,
    *,
    document_id: str | None,
) -> bool:
    if document_id or is_multi_article_intent(analysis, analysis.raw_query):
        return False
    if len(distinct_documents_in_hits(hits)) <= 1:
        return False
    # Second document within competitive score band → ask user to narrow
    if len(hits) < 2:
        return False
    best = hits[0].distance
    second_doc = None
    for hit in hits[1:6]:
        doc = _chunk_document_id(hit.chunk.chunk_id)
        if doc == _chunk_document_id(hits[0].chunk.chunk_id):
            continue
        second_doc = hit
        break
    if second_doc is None:
        return False
    # Lexical: low distance = good; vector: same — only ambiguous when scores are close
    if second_doc.distance <= best * 1.15 + 0.08:
        return True
    return False


def select_single_article_chunks(
    hits: list[ScoredChunk],
    *,
    max_chunks: int = 3,
) -> list:
    """Keep chunks from the single best-matching article only."""
    if not hits:
        return []
    best_doc = _chunk_document_id(hits[0].chunk.chunk_id)
    chunks: list = []
    for hit in hits:
        if _chunk_document_id(hit.chunk.chunk_id) != best_doc:
            continue
        chunks.append(hit.chunk)
        if len(chunks) >= max_chunks:
            break
    return chunks


def enforce_single_citation_answer(answer: str) -> str:
    """Strip [2]+ markers so UI shows one source when policy is single-article."""
    if "[2]" not in answer and "[3]" not in answer:
        return answer
    cleaned = re.sub(r"\s*\[(?:[2-9]|\d{2,})\]", "", answer)
    cleaned = re.sub(
        r"(Key points:|Summary:)([^\n]*)",
        lambda m: m.group(1) + re.sub(r"\[1\]", "", m.group(2)).strip() + " [1]",
        cleaned,
        count=1,
    )
    return cleaned


def build_clarification_answer() -> str:
    return (
        CLARIFICATION_MESSAGE
        + "\n\n_Disclaimer: This tool supports research review only; it does not provide "
        "individual diagnoses or prescriptions._"
    )


def nature_chunk_ok(chunk) -> bool:
    org = str(getattr(chunk, "source_org", "") or "")
    url = str(getattr(chunk, "source_url", "") or "").lower()
    if org == SourceOrg.NATURE.value:
        return True
    return "nature.com/articles" in url
