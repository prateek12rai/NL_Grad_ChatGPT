"""
Phase 3.4 — 512-token hard cap + 80-token overlap between chunks.

Free & fast: uses local tiktoken only (no API).
"""

from __future__ import annotations

import logging

from pipeline.chunking.models import ChunkDraft, TextUnit
from pipeline.chunking.segmentation.sentence_splitter import split_sentences
from pipeline.chunking.tokenization.overlap import (
    DEFAULT_OVERLAP_TOKENS,
    apply_overlap,
    overlap_tail_text,
)
from pipeline.chunking.tokenization.tokenizer import count_tokens, decode_tokens, encode_tokens

logger = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 512


def split_text_to_chunks(
    text: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> list[str]:
    """
    Split text into chunks each <= max_tokens at sentence boundaries.
    Oversized single sentences are split by token windows.
    """
    text = text.strip()
    if not text:
        return []

    if count_tokens(text) <= max_tokens:
        return [text]

    sentences = split_sentences(text)
    if not sentences:
        return _split_by_token_windows(text, max_tokens)

    chunks: list[str] = []
    current: list[str] = []

    def flush_current() -> None:
        nonlocal current
        if current:
            chunks.append(" ".join(current))
            current = []

    for sentence in sentences:
        if count_tokens(sentence) > max_tokens:
            flush_current()
            chunks.extend(_split_by_token_windows(sentence, max_tokens))
            continue

        candidate = " ".join(current + [sentence])
        if current and count_tokens(candidate) > max_tokens:
            flush_current()
            current = [sentence]
        else:
            current.append(sentence)

    flush_current()
    return [c for c in chunks if c.strip()]


def _split_by_token_windows(text: str, max_tokens: int) -> list[str]:
    """Token-window split for tables / oversized sentences."""
    ids = encode_tokens(text)
    chunks: list[str] = []
    start = 0
    while start < len(ids):
        end = min(start + max_tokens, len(ids))
        chunks.append(decode_tokens(ids[start:end]))
        start = end
    if len(chunks) > 1:
        logger.warning("oversized_sentence_split: %s token windows", len(chunks))
    return chunks


def _trim_to_token_budget(text: str, budget: int) -> str:
    """Trim text to fit token budget using sentence boundaries."""
    if count_tokens(text) <= budget:
        return text.strip()
    sentences = split_sentences(text)
    kept: list[str] = []
    for sentence in sentences:
        candidate = " ".join(kept + [sentence])
        if kept and count_tokens(candidate) > budget:
            break
        if count_tokens(sentence) > budget:
            ids = encode_tokens(sentence)[:budget]
            return decode_tokens(ids)
        kept.append(sentence)
    return " ".join(kept) if kept else decode_tokens(encode_tokens(text)[:budget])


def apply_overlap_within_budget(
    prev_chunk_text: str,
    next_chunk_text: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> str:
    """
    Apply overlap prefix but keep total chunk <= max_tokens (PRD hard cap).
    """
    tail = overlap_tail_text(prev_chunk_text, overlap_tokens)
    prefix_cost = count_tokens(tail)
    if prefix_cost >= max_tokens:
        return tail[: max(1, len(tail) // 2)]
    budget_for_new = max_tokens - prefix_cost
    trimmed = _trim_to_token_budget(next_chunk_text, budget_for_new)
    combined = apply_overlap(prev_chunk_text, trimmed, overlap_tokens)
    if count_tokens(combined) > max_tokens:
        combined = decode_tokens(encode_tokens(combined)[:max_tokens])
    return combined.strip()


def units_to_chunk_drafts(
    units: list[TextUnit],
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[ChunkDraft]:
    """
    Convert TextUnits (Phase 3.3) to ChunkDrafts with cap + overlap (Phase 3.4).
    """
    drafts: list[ChunkDraft] = []
    prev_exact: str | None = None

    for unit in units:
        raw_chunks = split_text_to_chunks(unit.text, max_tokens=max_tokens)
        for raw in raw_chunks:
            exact = raw
            if prev_exact is not None:
                exact = apply_overlap_within_budget(
                    prev_exact,
                    raw,
                    max_tokens=max_tokens,
                    overlap_tokens=overlap_tokens,
                )
            token_count = count_tokens(exact)
            drafts.append(
                ChunkDraft(
                    page_number=unit.page_number,
                    section_title=unit.section_title,
                    exact_context=exact,
                    token_count=token_count,
                )
            )
            prev_exact = exact

    return drafts


def pages_to_chunk_drafts(
    pages,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[ChunkDraft]:
    """Full chain: pages → units (3.3) → chunk drafts (3.4)."""
    from pipeline.chunking.segmentation import pages_to_units

    units = pages_to_units(pages)
    return units_to_chunk_drafts(units, max_tokens=max_tokens, overlap_tokens=overlap_tokens)
