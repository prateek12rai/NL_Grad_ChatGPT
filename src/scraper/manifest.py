"""manifest.json load/save, merge, sort (architecture §8.2)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from shared.config import settings
from shared.schemas import DocumentRecord

from scraper.models import ScrapedItem

MANIFEST_SCHEMA_VERSION = "1"


class ManifestFile(BaseModel):
    schema_version: str = MANIFEST_SCHEMA_VERSION
    documents: list[DocumentRecord] = Field(default_factory=list)
    pruned_document_ids: list[str] = Field(default_factory=list)


class ManifestStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (Path(settings.corpus_path).parent / "manifest.json")

    def load(self) -> ManifestFile:
        if not self.path.exists():
            return ManifestFile()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return ManifestFile.model_validate(data)

    def save(self, manifest: ManifestFile) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def document_ids(self, manifest: ManifestFile) -> set[str]:
        return {d.document_id for d in manifest.documents}

    def upsert(self, manifest: ManifestFile, record: DocumentRecord) -> ManifestFile:
        docs = [d for d in manifest.documents if d.document_id != record.document_id]
        docs.append(record)
        manifest.documents = docs
        return reindex_manifest(manifest)


def make_document_id(source_url: str, document_title: str) -> str:
    canonical = f"{source_url.strip().lower()}|{document_title.strip().lower()}"
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:16]}"


def new_document_record(item: ScrapedItem, local_path: str) -> DocumentRecord:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return DocumentRecord(
        document_id=make_document_id(item.source_url, item.document_title),
        source_org=item.source_org,
        source_url=item.source_url,
        document_title=item.document_title,
        publication_date=item.publication_date,
        ingested_at=now,
        content_type=item.content_type,
        local_path=local_path.replace("\\", "/"),
        chronological_rank=0,
    )


def reindex_manifest(manifest: ManifestFile) -> ManifestFile:
    sorted_docs = sorted(
        manifest.documents,
        key=lambda d: (d.publication_date, d.ingested_at),
        reverse=True,
    )
    manifest.documents = [
        doc.model_copy(update={"chronological_rank": rank})
        for rank, doc in enumerate(sorted_docs, start=1)
    ]
    return manifest
