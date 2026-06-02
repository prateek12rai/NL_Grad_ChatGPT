"""Text normalization rules — architecture §7.4."""

from __future__ import annotations

import re
import unicodedata

# Control chars except newline and tab
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# Horizontal whitespace (not \n)
_HORIZONTAL_SPACE = re.compile(r"[^\S\n]+")


def normalize_page_text(text: str) -> str:
    """
    Apply PRD Phase 3.1 normalization:
    NFC, CRLF, collapse spaces, strip controls, strip ends.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL_CHARS.sub("", text)
    text = _HORIZONTAL_SPACE.sub(" ", text)
    # Trim trailing spaces per line while keeping paragraph breaks
    lines = [ln.strip() for ln in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()
