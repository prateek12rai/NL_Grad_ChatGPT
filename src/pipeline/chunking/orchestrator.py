"""
Phase 3.6 — manifest loop, PII filter, JSONL + index output.

Free & fast: local CPU + disk only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from pipeline.chunking.chunk_log import ChunkLogger
from pipeline.chunking.exceptions import ExtractionError
from pipeline.chunking.metadata import (
    document_to_chunk_records,
    safe_document_filename,
    utc_now_iso,
)
from pipeline.chunking.writer import (
    INDEX_SCHEMA_VERSION,
    aggregate_content_hash,
    chunk_jsonl_path,
    chunk_meta_path,
    read_chunk_jsonl,
    write_chunk_jsonl,
    write_index,
    write_sidecar,
)
from scraper.manifest import MANIFEST_SCHEMA_VERSION, ManifestFile, ManifestStore
from shared.pii_filter import scan_text
from shared.schemas import ChunkRecord, DocumentRecord


PII_REVIEW_THRESHOLD = 0.30


@dataclass
class ChunkingResult:
    processed: int = 0
    skipped_incremental: int = 0
    skipped_missing: int = 0
    skipped_extract: int = 0
    chunks_written: int = 0
    chunks_dropped_pii: int = 0
    pruned_files_removed: int = 0


class DocumentSidecar(BaseModel):
    document_id: str
    source_ingested_at: str
    chunk_count: int
    pipeline_version: str = "1.0.0"


def _parse_ingested_at(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _should_skip_incremental(
    document: DocumentRecord,
    jsonl_path: Path,
    meta_path: Path,
) -> bool:
    if not jsonl_path.exists() or not meta_path.exists():
        return False
    sidecar = DocumentSidecar.model_validate_json(meta_path.read_text(encoding="utf-8"))
    doc_time = _parse_ingested_at(document.ingested_at)
    sidecar_time = _parse_ingested_at(sidecar.source_ingested_at)
    return doc_time <= sidecar_time


def _filter_pii(
    records: list[ChunkRecord],
    logger: ChunkLogger,
    document_id: str,
) -> tuple[list[ChunkRecord], int]:
    clean: list[ChunkRecord] = []
    dropped = 0
    for record in records:
        scan = scan_text(record.exact_context)
        if scan.is_clean:
            clean.append(record)
        else:
            dropped += 1
            logger.append(
                "pii_chunk_dropped",
                document_id=document_id,
                chunk_id=record.chunk_id,
                violations=list(scan.violations),
            )
    if records and dropped / len(records) > PII_REVIEW_THRESHOLD:
        logger.append(
            "document_pii_review",
            document_id=document_id,
            dropped=dropped,
            total=len(records),
        )
    return clean, dropped


class ChunkingOrchestrator:
    def __init__(
        self,
        repo_root: Path | None = None,
        manifest_store: ManifestStore | None = None,
        output_dir: Path | None = None,
        logger: ChunkLogger | None = None,
    ) -> None:
        from shared.config import settings

        self.repo_root = (repo_root or Path.cwd()).resolve()
        self.manifest_store = manifest_store or ManifestStore()
        data_dir = Path(self.manifest_store.path).parent.resolve()

        if output_dir is not None:
            self.output_dir = Path(output_dir).resolve()
        else:
            chunk_dir = Path(settings.chunk_output_dir)
            self.output_dir = (
                chunk_dir.resolve()
                if chunk_dir.is_absolute()
                else (self.repo_root / chunk_dir).resolve()
            )

        self.logger = logger or ChunkLogger(data_dir / "chunk_log.jsonl")
        self.index_path = self.output_dir / "index.json"

    def run(
        self,
        *,
        document_id: str | None = None,
        incremental: bool = True,
        force: bool = False,
    ) -> ChunkingResult:
        manifest = self._load_manifest()
        result = ChunkingResult()

        result.pruned_files_removed = self._handle_pruned(manifest)

        documents = manifest.documents
        if document_id:
            documents = [d for d in documents if d.document_id == document_id]
            if not documents:
                self.logger.append("document_not_found", document_id=document_id)
                return result

        for doc in documents:
            self._process_document(doc, result, incremental=incremental, force=force)

        self._rebuild_index()
        self.logger.append(
            "chunk_run_complete",
            processed=result.processed,
            chunks_written=result.chunks_written,
            skipped_incremental=result.skipped_incremental,
        )
        return result

    def _load_manifest(self) -> ManifestFile:
        manifest = self.manifest_store.load()
        if manifest.schema_version != MANIFEST_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported manifest schema_version: {manifest.schema_version}"
            )
        return manifest

    def _resolve_local_path(self, document: DocumentRecord) -> Path:
        path = Path(document.local_path)
        if not path.is_absolute():
            path = self.repo_root / path
        return path

    def _process_document(
        self,
        document: DocumentRecord,
        result: ChunkingResult,
        *,
        incremental: bool,
        force: bool,
    ) -> None:
        local_path = self._resolve_local_path(document)
        jsonl_path = chunk_jsonl_path(self.output_dir, document.document_id)
        meta_path = chunk_meta_path(self.output_dir, document.document_id)

        if not local_path.is_file():
            result.skipped_missing += 1
            self.logger.append(
                "missing_corpus_file",
                document_id=document.document_id,
                local_path=str(local_path),
            )
            return

        if force:
            self._delete_outputs(jsonl_path, meta_path)

        if incremental and not force and _should_skip_incremental(document, jsonl_path, meta_path):
            result.skipped_incremental += 1
            self.logger.append(
                "chunk_skipped_incremental",
                document_id=document.document_id,
            )
            return

        try:
            records = document_to_chunk_records(document, local_path)
        except ExtractionError as exc:
            result.skipped_extract += 1
            self.logger.append(
                "extract_error",
                document_id=document.document_id,
                error=str(exc),
            )
            return

        records, dropped = _filter_pii(records, self.logger, document.document_id)
        result.chunks_dropped_pii += dropped

        if not records:
            self.logger.append(
                "no_chunks_written",
                document_id=document.document_id,
                reason="empty_or_all_pii",
            )
            return

        write_chunk_jsonl(jsonl_path, records)
        write_sidecar(
            meta_path,
            document_id=document.document_id,
            source_ingested_at=document.ingested_at,
            chunk_count=len(records),
        )
        result.processed += 1
        result.chunks_written += len(records)
        self.logger.append(
            "document_chunked",
            document_id=document.document_id,
            chunk_count=len(records),
            chunk_file=str(jsonl_path.relative_to(self.repo_root)).replace("\\", "/"),
        )

    def _delete_outputs(self, jsonl_path: Path, meta_path: Path) -> None:
        for path in (jsonl_path, meta_path):
            if path.exists():
                path.unlink()

    def _handle_pruned(self, manifest: ManifestFile) -> int:
        removed = 0
        for doc_id in manifest.pruned_document_ids:
            jsonl_path = chunk_jsonl_path(self.output_dir, doc_id)
            meta_path = chunk_meta_path(self.output_dir, doc_id)
            for path in (jsonl_path, meta_path):
                if path.exists():
                    path.unlink()
                    removed += 1
            self.logger.append("pruned_chunks_removed", document_id=doc_id)
        return removed

    def _rebuild_index(self) -> None:
        documents: list[dict] = []
        total_chunks = 0

        for jsonl_path in sorted(self.output_dir.glob("*.jsonl")):
            if jsonl_path.name.endswith(".tmp"):
                continue
            rows = read_chunk_jsonl(jsonl_path)
            if not rows:
                continue
            doc_id = rows[0]["document_id"]
            safe_name = safe_document_filename(doc_id)
            rel_file = f"data/chunks/{safe_name}.jsonl"
            records = [ChunkRecord.model_validate(row) for row in rows]
            aggregate = aggregate_content_hash(records)
            documents.append(
                {
                    "document_id": doc_id,
                    "chunk_file": rel_file,
                    "chunk_count": len(rows),
                    "content_hash": aggregate,
                }
            )
            total_chunks += len(rows)

        payload = {
            "schema_version": INDEX_SCHEMA_VERSION,
            "generated_at": utc_now_iso(),
            "total_chunks": total_chunks,
            "documents": documents,
        }
        write_index(self.index_path, payload)
