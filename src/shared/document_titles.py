"""Resolve human-readable document titles when ingest used file-size placeholders."""

from __future__ import annotations

import re

_FILESIZE_TITLE = re.compile(r"^\([\d.]+\s*(MB|KB|GB)\)$", re.I)


def is_low_quality_title(title: str) -> bool:
    t = (title or "").strip()
    if len(t) < 8:
        return True
    if _FILESIZE_TITLE.match(t):
        return True
    if t.lower() in {"guidelines", "costing manual"}:
        return True
    return False


def resolve_document_title(
    title: str,
    source_url: str,
    exact_context: str,
) -> str:
    if not is_low_quality_title(title):
        return title.strip()

    url = (source_url or "").lower()
    if "htain.dhr.gov.in" in url or "dhr.gov.in" in url or "icmr.gov.in" in url:
        return "Legacy non-Nature source (re-ingest or purge)"

    for line in (exact_context or "").splitlines():
        line = line.strip()
        if len(line) >= 24 and not line.isdigit():
            return line[:140]

    return title.strip() or "Indexed medical document"
