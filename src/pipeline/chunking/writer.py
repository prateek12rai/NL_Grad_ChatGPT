"""Atomic JSONL / index writes (architecture §15)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from shared.schemas import ChunkRecord

from pipeline.chunking.metadata import safe_document_filename


PIPELINE_VERSION = "1.0.0"
INDEX_SCHEMA_VERSION = "1"


def chunk_jsonl_path(output_dir: Path, document_id: str) -> Path:
    return output_dir / f"{safe_document_filename(document_id)}.jsonl"


def chunk_meta_path(output_dir: Path, document_id: str) -> Path:
    return output_dir / f"{safe_document_filename(document_id)}.meta.json"


def read_chunk_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_chunk_jsonl(path: Path, records: list[ChunkRecord]) -> None:
    """Write via ``.jsonl.tmp`` then atomic rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record.to_jsonl_dict(), ensure_ascii=False) + "\n")
    tmp.replace(path)


def write_sidecar(
    path: Path,
    *,
    document_id: str,
    source_ingested_at: str,
    chunk_count: int,
) -> None:
    payload = {
        "document_id": document_id,
        "source_ingested_at": source_ingested_at,
        "chunk_count": chunk_count,
        "pipeline_version": PIPELINE_VERSION,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def aggregate_content_hash(records: list[ChunkRecord]) -> str:
    """Document-level fingerprint for index.json (architecture §12.3)."""
    if not records:
        return "sha256:empty"
    joined = "\n".join(sorted(r.content_hash for r in records))
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:16]}"


def write_index(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)
