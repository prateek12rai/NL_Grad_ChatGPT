"""Catalog queries over manifest.json (counts and sorted document lists)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from shared.config import settings
from shared.schemas import SourceOrg


def _manifest_path() -> Path:
    return Path(settings.corpus_path).parent / "manifest.json"


def load_manifest_documents() -> list[dict]:
    path = _manifest_path()
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("documents", []))


def get_manifest_document(document_id: str) -> dict | None:
    for doc in load_manifest_documents():
        if str(doc.get("document_id", "")) == document_id:
            return doc
    return None


def _doc_matches(
    doc: dict,
    *,
    source_org: SourceOrg | None,
    target_date: date | None,
) -> bool:
    if source_org and str(doc.get("source_org", "")).lower() != source_org.value.lower():
        return False
    if target_date:
        pub = str(doc.get("publication_date", ""))[:10]
        if pub != target_date.isoformat():
            return False
    return True


def list_catalog_documents(
    *,
    source_org: SourceOrg | None = None,
    target_date: date | None = None,
) -> list[dict]:
    docs = [
        d
        for d in load_manifest_documents()
        if _doc_matches(d, source_org=source_org, target_date=target_date)
    ]
    return sorted(docs, key=lambda d: str(d.get("ingested_at", "")), reverse=True)


def count_catalog_documents(
    *,
    source_org: SourceOrg | None = None,
    target_date: date | None = None,
) -> int:
    return len(list_catalog_documents(source_org=source_org, target_date=target_date))


def _parse_pub_date(value: str) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def oldest_publication_date(*, source_org: SourceOrg | None = None) -> date | None:
    """Earliest ``publication_date`` across indexed documents (None if empty)."""
    dates: list[date] = []
    for doc in load_manifest_documents():
        if source_org and str(doc.get("source_org", "")).lower() != source_org.value.lower():
            continue
        parsed = _parse_pub_date(doc.get("publication_date", ""))
        if parsed:
            dates.append(parsed)
    return min(dates) if dates else None


def date_has_documents(target_date: date, *, source_org: SourceOrg | None = None) -> bool:
    """True when at least one indexed document was published on ``target_date``."""
    return count_catalog_documents(source_org=source_org, target_date=target_date) > 0
