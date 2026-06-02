"""Batch sizing for HF embed requests (architecture §7.4, §14)."""

from __future__ import annotations

from shared.config import settings

DEFAULT_BATCH_SIZE = 16
MAX_CHARS_PER_REQUEST = 24_000


def plan_batches(
    texts: list[str],
    *,
    batch_size: int | None = None,
    max_chars: int | None = None,
) -> list[list[str]]:
    """
    Split texts into HF-safe batches by count and total character budget.
    """
    if not texts:
        return []

    size_limit = batch_size or settings.embed_batch_size or DEFAULT_BATCH_SIZE
    char_limit = max_chars or settings.embed_max_chars_per_request or MAX_CHARS_PER_REQUEST

    batches: list[list[str]] = []
    current: list[str] = []
    current_chars = 0

    for text in texts:
        text_len = len(text)
        if text_len > char_limit:
            if current:
                batches.append(current)
                current = []
                current_chars = 0
            batches.append([text])
            continue

        would_exceed = current and (
            len(current) >= size_limit or current_chars + text_len > char_limit
        )
        if would_exceed:
            batches.append(current)
            current = []
            current_chars = 0

        current.append(text)
        current_chars += text_len

    if current:
        batches.append(current)

    return batches
