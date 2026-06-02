"""Creative follow-up questions — one per article, diverse framing, Nature portfolio only."""

from __future__ import annotations

import hashlib
import time

from api.rag.suggestions import QuerySuggestion
from pipeline.index.catalog import load_manifest_documents
from shared.document_titles import resolve_document_title
from shared.schemas import SourceOrg

# Diverse question frames (rotated per request so "You might also ask" stays fresh)
_QUESTION_FRAMES: tuple[str, ...] = (
    "For the Nature medical-research article on {topic} (published {date}), what were the primary outcomes and how strong was the evidence?",
    "In the {date} Nature paper about {topic}, what study design and patient population did the authors use?",
    "What clinical or policy implications does the Nature study on {topic} ({date}) draw for healthcare practice?",
    "How do the authors of the {date} article on {topic} discuss limitations, bias, and generalizability?",
    "What novel methods or interventions does the Nature research on {topic} ({date}) evaluate compared with prior work?",
    "Summarize screening, diagnostic, or treatment conclusions from the Nature article on {topic} ({date}).",
    "What sample size, endpoints, and statistical results are reported in the {date} Nature study of {topic}?",
    "Does the {date} Nature paper on {topic} report harms, safety signals, or adverse events — and what were they?",
)


def _topic_snippet(title: str, max_len: int = 48) -> str:
    t = title.strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 3].rstrip() + "…"


def _frame_index(document_id: str, rotation_seed: str) -> int:
    digest = hashlib.sha256(f"{document_id}:{rotation_seed}".encode()).hexdigest()
    return int(digest[:8], 16) % len(_QUESTION_FRAMES)


def _creative_question(doc: dict, rotation_seed: str) -> str:
    title = resolve_document_title(
        str(doc.get("document_title", "")),
        str(doc.get("source_url", "")),
        "",
    )
    pub = str(doc.get("publication_date", ""))[:10]
    topic = _topic_snippet(title, 56)
    doc_id = str(doc.get("document_id", ""))
    frame = _QUESTION_FRAMES[_frame_index(doc_id, rotation_seed)]
    return frame.format(topic=topic, date=pub or "recent")


def build_corpus_follow_ups(
    limit: int = 2,
    *,
    exclude_document_ids: set[str] | None = None,
    rotation_seed: str | None = None,
    newest_first: bool = False,
) -> list[QuerySuggestion]:
    """
    Up to ``limit`` follow-ups — each maps to exactly one ``document_id`` (one citation when answered).
    ``rotation_seed`` changes which question frame is used (fresh suggestions per query).
    When ``newest_first`` is True, pick the most recent articles deterministically
    (used for the "top 3 articles" not-found fallback) instead of a per-seed shuffle.
    """
    exclude = exclude_document_ids or set()
    seed = rotation_seed if rotation_seed is not None else str(time.time_ns())

    docs = sorted(
        load_manifest_documents(),
        key=lambda d: (str(d.get("publication_date", "")), str(d.get("ingested_at", ""))),
        reverse=True,
    )
    if not newest_first:
        # Shuffle pick order slightly per seed so we don't always suggest the same two newest
        order_key = lambda d: hashlib.sha256(
            f"{seed}:{d.get('document_id', '')}".encode()
        ).hexdigest()
        docs = sorted(docs, key=order_key)

    seen_ids: set[str] = set()
    out: list[QuerySuggestion] = []

    for doc in docs:
        doc_id = str(doc.get("document_id", ""))
        if not doc_id or doc_id in seen_ids or doc_id in exclude:
            continue
        org = str(doc.get("source_org", ""))
        url = str(doc.get("source_url", "")).lower()
        if org != SourceOrg.NATURE.value and "nature.com/articles" not in url:
            continue
        title = resolve_document_title(
            str(doc.get("document_title", "")),
            str(doc.get("source_url", "")),
            "",
        )
        lower_title = title.lower()
        if len(title) < 12 or "dhr" in lower_title or "htain" in lower_title or "icmr" in lower_title:
            continue
        seen_ids.add(doc_id)
        pub = str(doc.get("publication_date", ""))[:10]
        label = f"{_topic_snippet(title)} · {pub}"
        out.append(
            QuerySuggestion(
                label=label,
                query=_creative_question(doc, seed),
                chunk_id=doc_id,
                source_org=SourceOrg.NATURE.value,
                document_id=doc_id,
            )
        )
        if len(out) >= limit:
            break

    return out
