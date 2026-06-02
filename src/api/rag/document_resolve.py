"""Match user queries to manifest documents (clarification follow-ups)."""

from __future__ import annotations

import re
from datetime import date, datetime

from pipeline.index.catalog import load_manifest_documents

_STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "into",
        "using",
        "based",
        "about",
        "want",
        "main",
        "findings",
        "published",
        "article",
        "nature",
        "paper",
        "study",
        "research",
    }
)

_DATE_PATTERNS = (
    re.compile(r"published:\s*(\d{1,2}\s+\w+\s+\d{4})", re.I),
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
    re.compile(r"\b(\d{1,2}\s+\w+\s+\d{4})\b"),
)

_DATE_FORMATS = (
    "%d %B %Y",
    "%d %b %Y",
    "%Y-%m-%d",
)


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]{4,}", text.lower())
    return {w for w in words if w not in _STOPWORDS}


def extract_publication_date(query: str) -> date | None:
    for pattern in _DATE_PATTERNS:
        match = pattern.search(query)
        if not match:
            continue
        raw = match.group(1).strip()
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
    return None


def title_match_score(title: str, query: str) -> float:
    """Fraction of significant title tokens found in the query (0–1)."""
    title_tokens = _tokenize(title)
    if not title_tokens:
        return 0.0
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0.0
    overlap = title_tokens & query_tokens
    return len(overlap) / len(title_tokens)


def resolve_document_id_from_query(
    query: str,
    *,
    min_score: float = 0.48,
    min_gap: float = 0.06,
) -> str | None:
    """Best manifest document_id if the query names an indexed article."""
    query_date = extract_publication_date(query)
    scored: list[tuple[str, float]] = []
    for doc in load_manifest_documents():
        title = str(doc.get("document_title", "") or "")
        if not title:
            continue
        score = title_match_score(title, query)
        pub = str(doc.get("publication_date", ""))[:10]
        if query_date and pub == query_date.isoformat():
            score = min(1.0, score + 0.12)
        doc_id = str(doc.get("document_id", ""))
        if doc_id:
            scored.append((doc_id, score))
    if not scored:
        return None
    scored.sort(key=lambda x: x[1], reverse=True)
    best_id, best_score = scored[0]
    second_score = scored[1][1] if len(scored) > 1 else 0.0
    if best_score < min_score:
        return None
    if len(scored) > 1 and (best_score - second_score) < min_gap:
        return None
    return best_id
