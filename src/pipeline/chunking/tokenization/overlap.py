"""80-token overlap between consecutive chunks (architecture §10.3)."""

from __future__ import annotations

from pipeline.chunking.tokenization.tokenizer import (
    count_tokens,
    decode_tokens,
    encode_tokens,
)

DEFAULT_OVERLAP_TOKENS = 80


def overlap_tail_text(text: str, overlap_tokens: int = DEFAULT_OVERLAP_TOKENS) -> str:
    """Last N tokens of text, decoded back to string."""
    if not text or overlap_tokens <= 0:
        return ""
    ids = encode_tokens(text)
    if len(ids) <= overlap_tokens:
        return text
    return decode_tokens(ids[-overlap_tokens:])


def apply_overlap(
    prev_chunk_text: str,
    next_chunk_text: str,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> str:
    """Prefix next chunk with tail of previous chunk."""
    tail = overlap_tail_text(prev_chunk_text, overlap_tokens)
    if not tail:
        return next_chunk_text.strip()
    if not next_chunk_text.strip():
        return tail
    return f"{tail}\n{next_chunk_text.strip()}"
