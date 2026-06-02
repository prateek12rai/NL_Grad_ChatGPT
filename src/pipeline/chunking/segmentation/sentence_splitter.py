"""Sentence splitting with medical abbreviation guards (architecture §9.2)."""

from __future__ import annotations

import re

# Placeholders for protected periods
_PLACEHOLDERS: list[tuple[str, str]] = [
    ("Dr.", "__DR__"),
    ("dr.", "__DR__"),
    ("e.g.", "__EG__"),
    ("i.e.", "__IE__"),
    ("No.", "__NO__"),
    ("no.", "__NO__"),
    ("vs.", "__VS__"),
    ("etc.", "__ETC__"),
    ("Fig.", "__FIG__"),
    ("fig.", "__FIG__"),
    ("Mr.", "__MR__"),
    ("Mrs.", "__MR__"),
    ("Prof.", "__PROF__"),
]

# Split after sentence-ending punctuation; abbreviations already placeholder-protected
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=\S)")


def split_sentences(text: str) -> list[str]:
    """Split text into sentences; preserve paragraph breaks as empty markers."""
    if not text.strip():
        return []

    sentences: list[str] = []
    paragraphs = re.split(r"\n\s*\n", text.strip())

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        protected = para
        for literal, token in _PLACEHOLDERS:
            protected = protected.replace(literal, token)
        parts = _SENTENCE_END.split(protected)
        for part in parts:
            restored = part.strip()
            for literal, token in _PLACEHOLDERS:
                restored = restored.replace(token, literal)
            if restored:
                sentences.append(restored)
    return sentences
