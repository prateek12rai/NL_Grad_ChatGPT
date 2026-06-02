"""Manifest-backed retrieval for count/list questions (source + date filters)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from pipeline.index.catalog import list_catalog_documents
from pipeline.index.context_select import enrich_chunk_title
from pipeline.index.retrieval import ScoredChunk
from shared.chunk_content import is_placeholder_context, is_ui_boilerplate
from shared.config import settings
from shared.document_titles import resolve_document_title
from shared.schemas import ChunkMetadata, SourceOrg, VerificationStatus


def _best_chunk_for_document(document_id: str, doc_meta: dict) -> ChunkMetadata | None:
    index_path = Path(settings.chunk_index_path)
    if not index_path.is_file():
        return None
    index = json.loads(index_path.read_text(encoding="utf-8"))
    chunk_dir = Path(settings.chunk_output_dir)
    chunk_file = None
    for entry in index.get("documents", []):
        if entry.get("document_id") == document_id:
            chunk_file = entry.get("chunk_file")
            break
    if not chunk_file:
        return None
    path = Path(chunk_file)
    if not path.is_file():
        path = chunk_dir / path.name
    if not path.is_file():
        return None

    best: ChunkMetadata | None = None
    best_score = -1.0

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        text = str(rec.get("exact_context", "")).strip()
        if not text or is_placeholder_context(text) or is_ui_boilerplate(text):
            continue
        title = resolve_document_title(
            str(rec.get("document_title", "")),
            str(rec.get("source_url", doc_meta.get("source_url", ""))),
            text,
        )
        # Prefer substantive passages (abstracts, summaries)
        score = float(len(text))
        if "abstract" in text[:200].lower():
            score += 500
        if score > best_score:
            best_score = score
            best = ChunkMetadata(
                chunk_id=str(rec["chunk_id"]),
                source_org=SourceOrg(rec["source_org"]),
                source_url=str(rec.get("source_url", doc_meta.get("source_url", ""))),
                document_title=title,
                publication_year=int(rec.get("publication_year", 0))
                or int(str(doc_meta.get("publication_date", "2026"))[:4]),
                page_number=int(rec.get("page_number", 1)),
                exact_context=text[:2000],
                verification_status=VerificationStatus.UNVERIFIED,
            )
    return enrich_chunk_title(best) if best else None


def retrieve_from_manifest(
    *,
    source_org: SourceOrg | None = None,
    target_date: date | None = None,
    max_documents: int = 6,
) -> list[ScoredChunk]:
    """
    One representative chunk per manifest document matching filters.
    """
    docs = list_catalog_documents(source_org=source_org, target_date=target_date)
    hits: list[ScoredChunk] = []
    for doc in docs:
        document_id = str(doc["document_id"])
        chunk = _best_chunk_for_document(document_id, doc)
        if chunk:
            hits.append(ScoredChunk(chunk=chunk, distance=0.01 * len(hits)))
        if len(hits) >= max_documents:
            break
    return hits


