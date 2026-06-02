"""tiktoken helpers for chunk bounds (architecture §10.1)."""

from __future__ import annotations

import tiktoken

_ENCODING_NAME = "cl100k_base"
_encoder: tiktoken.Encoding | None = None


def _encoder_instance() -> tiktoken.Encoding:
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding(_ENCODING_NAME)
    return _encoder


def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(_encoder_instance().encode(text))


def encode_tokens(text: str) -> list[int]:
    return _encoder_instance().encode(text)


def decode_tokens(token_ids: list[int]) -> str:
    return _encoder_instance().decode(token_ids)
