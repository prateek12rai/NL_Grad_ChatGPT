"""
Suggested questions from verified chunks only (click → POST /query with same text).
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.index.chroma_store import ChromaStore
from pipeline.index.retrieval import _chunk_document_id
from shared.schemas import SourceOrg


@dataclass(frozen=True)
class QuerySuggestion:
    label: str
    query: str
    chunk_id: str
    source_org: str
    document_id: str = ""


def _question_for_topic(title: str, source_org: str) -> str:
    org = source_org
    return (
        f"What does verified {org} guidance in '{title}' state about clinical management "
        f"and key recommendations?"
    )


def build_verified_query_suggestions(
    store: ChromaStore | None = None,
    limit: int = 3,
) -> list[QuerySuggestion]:
    """
    Up to ``limit`` suggestions from distinct verified documents in Chroma.
    """
    chroma = store or ChromaStore()
    if chroma.count() == 0:
        return []

    try:
        result = chroma.collection.get(
            where={"verification_status": "verified"},
            include=["metadatas"],
        )
    except Exception:
        result = chroma.collection.get(include=["metadatas"])

    metadatas = result.get("metadatas") or []
    ids = result.get("ids") or []

    seen_docs: set[str] = set()
    suggestions: list[QuerySuggestion] = []

    for chunk_id, meta in zip(ids, metadatas):
        if not meta:
            continue
        if meta.get("verification_status") != "verified":
            continue
        doc_key = str(meta.get("document_id") or meta.get("document_title") or chunk_id)
        if doc_key in seen_docs:
            continue
        seen_docs.add(doc_key)
        title = str(meta.get("document_title") or "this document")
        org = str(meta.get("source_org") or SourceOrg.ICMR.value)
        resolved_chunk_id = str(meta.get("chunk_id") or chunk_id)
        document_id = str(meta.get("document_id") or _chunk_document_id(resolved_chunk_id))
        suggestions.append(
            QuerySuggestion(
                label=f"{org}: {title[:72]}",
                query=_question_for_topic(title, org),
                chunk_id=resolved_chunk_id,
                source_org=org,
                document_id=document_id,
            )
        )
        if len(suggestions) >= limit:
            break

    return suggestions


def format_suggestions_block(suggestions: list[QuerySuggestion]) -> str:
    """Plain-text block under the Pinky Promise message (UI renders buttons from JSON)."""
    if not suggestions:
        return (
            "\n\nNo verified topics are indexed yet. Verify sources in the HITL console, "
            "then try again."
        )
    lines = ["\n\nTry one of these verified topics:"]
    for i, s in enumerate(suggestions, start=1):
        lines.append(f"{i}. {s.label}")
    return "\n".join(lines)
