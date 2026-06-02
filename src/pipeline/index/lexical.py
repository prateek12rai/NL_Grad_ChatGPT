"""Keyword retrieval over chunk JSONL when vector search is unavailable or mismatched."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pipeline.index.retriever import parse_chunk_metadata
from pipeline.index.retrieval import ScoredChunk
from shared.chunk_content import is_placeholder_context, is_ui_boilerplate, sanitize_display_context
from shared.config import settings
from shared.document_titles import is_low_quality_title, resolve_document_title
from shared.schemas import ChunkMetadata, SourceOrg, VerificationStatus

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}", re.I)
_STOP = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "what",
        "when",
        "where",
        "which",
        "about",
        "does",
        "have",
        "been",
        "were",
        "are",
        "was",
        "how",
    }
)


@dataclass(frozen=True)
class _LexRow:
    chunk: ChunkMetadata
    document_id: str
    tf: dict[str, float]
    doc_len: float


def _tokenize(text: str) -> list[str]:
    tokens = [t.lower() for t in _TOKEN_RE.findall(text)]
    return [t for t in tokens if t not in _STOP]


@lru_cache(maxsize=1)
def _load_lexical_rows() -> tuple[_LexRow, ...]:
    index_path = Path(settings.chunk_index_path)
    if not index_path.is_file():
        return ()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    chunk_dir = Path(settings.chunk_output_dir)
    rows: list[_LexRow] = []

    for doc in index.get("documents", []):
        chunk_file = doc.get("chunk_file")
        if not chunk_file:
            continue
        path = Path(chunk_file)
        if not path.is_file():
            path = chunk_dir / path.name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            text = sanitize_display_context(str(rec.get("exact_context", "")).strip())
            if not text or is_placeholder_context(text) or is_ui_boilerplate(text):
                continue
            raw_title = str(rec.get("document_title", ""))
            source_url = str(rec.get("source_url", ""))
            title = resolve_document_title(raw_title, source_url, text)
            if is_low_quality_title(title) and len(text) < 60:
                continue
            meta = ChunkMetadata(
                chunk_id=str(rec["chunk_id"]),
                source_org=SourceOrg(rec["source_org"]),
                source_url=source_url,
                document_title=title,
                publication_year=int(rec.get("publication_year", 0)),
                page_number=int(rec.get("page_number", 1)),
                exact_context=text,
                verification_status=VerificationStatus(
                    rec.get("verification_status", VerificationStatus.UNVERIFIED.value)
                ),
            )
            tokens = _tokenize(f"{title} {text}")
            if not tokens:
                continue
            tf: dict[str, float] = {}
            for tok in tokens:
                tf[tok] = tf.get(tok, 0.0) + 1.0
            rows.append(
                _LexRow(
                    chunk=meta,
                    document_id=str(rec.get("document_id", "")),
                    tf=tf,
                    doc_len=float(len(tokens)),
                )
            )
    return tuple(rows)


def retrieve_lexical(
    query: str,
    *,
    top_k: int | None = None,
    document_id: str | None = None,
) -> list[ScoredChunk]:
    """BM25-style scoring over local chunk files (no Chroma query vector)."""
    rows = _load_lexical_rows()
    if document_id:
        rows = tuple(r for r in rows if r.document_id == document_id)
    if not rows:
        return []

    k = top_k or settings.rag_top_k
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    n_docs = len(rows)
    avg_dl = sum(r.doc_len for r in rows) / n_docs
    df: dict[str, int] = {}
    for row in rows:
        for term in set(row.tf):
            df[term] = df.get(term, 0) + 1

    k1, b = 1.5, 0.75
    scored: list[tuple[float, _LexRow]] = []

    for row in rows:
        score = 0.0
        for term in q_tokens:
            if term not in row.tf:
                continue
            idf = math.log(1.0 + (n_docs - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5))
            tf = row.tf[term]
            denom = tf + k1 * (1.0 - b + b * row.doc_len / avg_dl)
            score += idf * (tf * (k1 + 1.0)) / denom
        if score > 0:
            scored.append((score, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    hits: list[ScoredChunk] = []
    for rank, (score, row) in enumerate(scored[:k], start=1):
        # Map lexical score to pseudo-distance for shared thresholds (higher score = lower distance)
        distance = max(0.01, 1.0 / (1.0 + score))
        hits.append(ScoredChunk(chunk=row.chunk, distance=distance))
    return hits
