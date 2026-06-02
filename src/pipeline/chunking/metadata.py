"""
Phase 3.5 — stable chunk_id and ChunkRecord assembly.

Free & fast: local hashing only; no API calls.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from pipeline.chunking.models import ChunkDraft
from pipeline.chunking.tokenization import pages_to_chunk_drafts
from shared.chunk_content import is_explicit_ui_noise, is_placeholder_context, sanitize_display_context
from shared.schemas import ChunkRecord, DocumentRecord, SourceOrg, VerificationStatus


def format_chunk_id(document_id: str, page_number: int, chunk_index: int) -> str:
    """``{document_id}::p{page:04d}::c{index:04d}`` (architecture §11.1)."""
    return f"{document_id}::p{page_number:04d}::c{chunk_index:04d}"


def safe_document_filename(document_id: str) -> str:
    """Filesystem-safe name: ``sha256:abc`` → ``sha256_abc``."""
    return document_id.replace(":", "_")


def publication_year_from_date(publication_date: str) -> int:
    """``YYYY-MM-DD`` → year int (architecture §11.3)."""
    return int(publication_date.split("-", 1)[0])


def content_hash(exact_context: str) -> str:
    """SHA-256 hex digest of verbatim chunk text."""
    return hashlib.sha256(exact_context.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_source_org(value: SourceOrg | str) -> SourceOrg:
    if isinstance(value, SourceOrg):
        return value
    return SourceOrg(value)


def _chunk_indices_per_page(drafts: list[ChunkDraft]) -> list[int]:
    """1-based chunk_index, reset per page (architecture §11.1)."""
    counters: dict[int, int] = {}
    indices: list[int] = []
    for draft in drafts:
        counters[draft.page_number] = counters.get(draft.page_number, 0) + 1
        indices.append(counters[draft.page_number])
    return indices


def drafts_to_chunk_records(
    document: DocumentRecord,
    drafts: list[ChunkDraft],
    *,
    created_at: str | None = None,
) -> list[ChunkRecord]:
    """Attach manifest metadata and stable IDs to Phase 3.4 drafts."""
    if not drafts:
        return []

    stamp = created_at or utc_now_iso()
    year = publication_year_from_date(document.publication_date)
    source_org = _resolve_source_org(document.source_org)
    source_url = str(document.source_url)
    indices = _chunk_indices_per_page(drafts)

    records: list[ChunkRecord] = []
    for draft, chunk_index in zip(drafts, indices, strict=True):
        exact = sanitize_display_context(draft.exact_context)
        if not exact or is_placeholder_context(exact) or is_explicit_ui_noise(exact):
            continue
        records.append(
            ChunkRecord(
                chunk_id=format_chunk_id(document.document_id, draft.page_number, chunk_index),
                document_id=document.document_id,
                source_org=source_org,
                source_url=source_url,
                document_title=document.document_title,
                publication_year=year,
                page_number=draft.page_number,
                chunk_index=chunk_index,
                exact_context=exact,
                token_count=draft.token_count,
                char_count=len(exact),
                verification_status=VerificationStatus.UNVERIFIED,
                content_hash=content_hash(exact),
                created_at=stamp,
            )
        )
    return records


def document_to_chunk_records(
    document: DocumentRecord,
    local_path,
    *,
    created_at: str | None = None,
) -> list[ChunkRecord]:
    """Extract → segment → tokenize → ChunkRecord (Phases 3.1–3.5)."""
    from pathlib import Path

    from pipeline.chunking.extractors import extract_document

    path = Path(local_path)
    result = extract_document(path, document.content_type)
    drafts = pages_to_chunk_drafts(result.pages)
    return drafts_to_chunk_records(document, drafts, created_at=created_at)
