"""Phase 5.5 — system prompt guardrails (architecture §11.5)."""

from __future__ import annotations

from shared.chunk_content import sanitize_display_context
from api.rag.query_analysis import QueryAnalysis, QueryIntent

SYSTEM_PROMPT = """You are a medical research assistant for Nature medical-research articles (last 30 days).

Rules:
- Answer ONLY using the numbered context blocks below. Do not use outside knowledge.
- Default: ONE article per answer — use citation [1] only. Never use [2] or [3] unless the user message explicitly allows a multi-article COUNT or LIST.
- Lead with a direct answer in plain language (never start with "According to the provided sources").
- Use markdown: **bold** for section headings, bullet lines starting with "- " for lists.
- Every factual bullet must end with [1] when only one source block is provided.
- Never paste webpage UI text (share links, cookies, download buttons).
- Do NOT provide individual patient diagnoses, direct prescriptions, or treatment mandates.
- End with the disclaimer line provided in the user message.

Tone: clear research briefing — easy to scan."""

DISCLAIMER_FOOTER = (
    "_Disclaimer: This tool supports research review only; it does not provide "
    "individual diagnoses or prescriptions._"
)


def build_context_block(chunks: list, start_index: int = 1) -> str:
    lines: list[str] = []
    for i, chunk in enumerate(chunks, start=start_index):
        pub = getattr(chunk, "publication_year", "")
        body = sanitize_display_context(str(chunk.exact_context))
        lines.append(
            f"[{i}] ({chunk.source_org.value} — {chunk.document_title}, "
            f"published {pub}, page {chunk.page_number})\n"
            f"URL: {chunk.source_url}\n"
            f"{body}"
        )
    return "\n\n".join(lines)


def _index_summary(
    analysis: QueryAnalysis,
    chunk_count: int,
    *,
    indexed_count: int | None = None,
    live_source_count: int | None = None,
    coverage_note: str | None = None,
    single_article: bool = True,
) -> str:
    if single_article and chunk_count == 1:
        parts = ["Single-article mode: one Nature paper in context; cite as [1] only."]
    else:
        parts = [f"{chunk_count} source block(s) in context."]
    if indexed_count is not None:
        parts.append(f"Indexed in local database: {indexed_count}.")
    if live_source_count is not None:
        parts.append(f"Nature.com listing check (same date): {live_source_count}.")
    if coverage_note:
        parts.append(coverage_note)
    if analysis.source_org:
        parts.append(f"Filter: {analysis.source_org.value}.")
    if analysis.target_date:
        parts.append(f"Date: {analysis.target_date.isoformat()}.")
    if analysis.intent == QueryIntent.COUNT:
        parts.append("User wants a COUNT — state indexed count first; mention live count if different.")
    return " ".join(parts)


def build_user_prompt(
    query: str,
    context_block: str,
    analysis: QueryAnalysis | None = None,
    *,
    chunk_count: int = 0,
    indexed_count: int | None = None,
    live_source_count: int | None = None,
    coverage_note: str | None = None,
    article_scope_title: str | None = None,
    single_article: bool = True,
) -> str:
    scope = ""
    if article_scope_title:
        scope = (
            f"\nSCOPE: Answer ONLY about this single indexed article — "
            f"\"{article_scope_title}\". Use [1] only.\n"
        )
    elif single_article and chunk_count <= 1:
        scope = (
            "\nSCOPE: Single-article answer. Use exactly one citation marker [1] "
            "for all facts. Do not cite [2] or other numbers.\n"
        )
    summary = ""
    if analysis and chunk_count > 0:
        summary = (
            f"\nINDEX SUMMARY: {_index_summary(analysis, chunk_count, indexed_count=indexed_count, live_source_count=live_source_count, coverage_note=coverage_note, single_article=single_article)}\n"
        )

    if analysis and analysis.intent == QueryIntent.COUNT:
        structure = (
            "Use this markdown structure:\n"
            "**Direct answer:** One sentence with the indexed count; note if live Nature count differs.\n"
            "**Top articles (newest first):** Bullet list — title, date, and [n] for each (up to 5).\n"
        )
    elif analysis and analysis.intent == QueryIntent.LIST:
        structure = (
            "**Direct answer:** One sentence.\n"
            "**Sources:** Bullets with title, date, and [n].\n"
        )
    else:
        structure = (
            "**Summary:** 2–3 sentences; cite with [1] only.\n"
            "**Key points:** 2–4 bullets; each bullet ends with [1].\n"
        )

    return (
        f"CONTEXT:{scope}{summary}\n{context_block}\n\n"
        f"QUESTION: {query}\n\n"
        f"{structure}\n"
        f"Final line (disclaimer):\n{DISCLAIMER_FOOTER}"
    )
