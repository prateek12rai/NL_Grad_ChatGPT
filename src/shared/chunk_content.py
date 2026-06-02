"""Resolve real chunk text (skip legacy mock placeholders in Chroma)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from shared.config import settings

_MOCK_PLACEHOLDER = re.compile(
    r"mock\s+ingest\s+content|fixture\s+content\s+for",
    re.I,
)

_UI_BOILERPLATE = re.compile(
    r"share this article|get shareable link|cookies? policy|sign up for alerts|"
    r"subscribe to nature|download pdf|supplementary information only available|"
    r"springer nature sharedit|copy shareable link|content-sharing initiative",
    re.I,
)

# Lines dropped from HITL source preview and LLM context when possible
_SKIP_LINE = re.compile(
    r"^(?:"
    r"share this article|"
    r"anyone you share the following link|"
    r"get shareable link|"
    r"sorry, a shareable link is not currently available|"
    r"copy shareable link to clipboard|"
    r"provided by the springer nature|"
    r"content-sharing initiative|"
    r"keywords\s*:|"
    r"cite this article|"
    r"download citation|"
    r"received\s*:|"
    r"accepted\s*:|"
    r"published\s*:|"
    r"doi\s*:|"
    r"https?://doi\.org/|"
    r"https?://www\.nature\.com/articles/|"
    r"^/\S*articles/\S+|"
    r"rights and permissions|"
    r"reprints and permissions|"
    r"about this article|"
    r"author information|"
    r"competing interests|"
    r"additional information|"
    r"data availability|"
    r"references\s*$|"
    r"acknowledgements?\s*$|"
    r"supplementary information"
    r")",
    re.I,
)

_ARTICLE_ID_ONLY = re.compile(r"^/s\d{5,}-\d{3,}-\d{5,}-\d+\s*$", re.I)


def is_placeholder_context(text: str) -> bool:
    return bool(_MOCK_PLACEHOLDER.search(text or ""))


def is_explicit_ui_noise(text: str) -> bool:
    """Share/cookie sidebar text — skip at ingest when little prose remains."""
    t = (text or "").strip()
    if not t:
        return True
    if _UI_BOILERPLATE.search(t[:800]):
        cleaned = sanitize_display_context(t)
        return len(cleaned) < max(120, len(t) * 0.35)
    return False


def is_ui_boilerplate(text: str) -> bool:
    """Web scrape noise (share buttons, cookie banners) — not useful for answers."""
    t = (text or "").strip()
    if not t:
        return True
    cleaned = sanitize_display_context(t)
    if len(cleaned) < 80:
        return True
    if _UI_BOILERPLATE.search(t[:800]) and len(cleaned) < max(120, len(t) * 0.35):
        return True
    return False


def sanitize_display_context(text: str) -> str:
    """
    Strip Nature.com sidebar / citation / share boilerplate for HITL preview and answers.
    Returns cleaned prose suitable for human review.
    """
    raw = (text or "").replace("\r\n", "\n").strip()
    if not raw:
        return ""

    kept: list[str] = []
    for line in re.split(r"\n+", raw):
        chunk = line.strip()
        if not chunk:
            continue
        if _ARTICLE_ID_ONLY.match(chunk):
            continue
        if re.match(r"^keywords\b", chunk, re.I):
            continue
        if _SKIP_LINE.search(chunk):
            continue
        if _UI_BOILERPLATE.search(chunk) and len(chunk) < 200:
            continue
        kept.append(chunk)

    out = "\n\n".join(kept).strip()
    if not out:
        # Fallback: drop only the noisiest phrases inline
        out = raw
        for pattern in (
            r"Share this article[^.]*\.",
            r"Get shareable link[^.]*\.",
            r"Copy shareable link to clipboard[^.]*\.",
            r"Provided by the Springer Nature SharedIt[^.]*\.",
            r"Keywords\s*:[^.]*\.",
            r"Cite this article[^.]*\.",
            r"Download citation[^.]*\.",
        ):
            out = re.sub(pattern, "", out, flags=re.I)
        out = re.sub(r"\s{2,}", " ", out).strip()

    return out


def load_chunk_text_from_store(chunk_id: str) -> str | None:
    """Load ``exact_context`` from chunk JSONL when Chroma still has placeholder text."""
    chunk_dir = Path(settings.chunk_output_dir)
    index_path = Path(settings.chunk_index_path)
    if not index_path.is_file():
        return None
    index = json.loads(index_path.read_text(encoding="utf-8"))
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
            if rec.get("chunk_id") == chunk_id:
                text = str(rec.get("exact_context", "")).strip()
                if text and not is_placeholder_context(text):
                    cleaned = sanitize_display_context(text)
                    return cleaned or text
    return None
