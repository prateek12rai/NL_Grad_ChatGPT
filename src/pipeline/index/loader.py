"""Load Phase 3 chunk JSONL files via index.json."""

from __future__ import annotations

import json
from pathlib import Path

from shared.config import settings
from shared.schemas import ChunkRecord

INDEX_SCHEMA_VERSION = "1"


def load_chunks_from_index(
    repo_root: Path,
    index_path: Path | None = None,
) -> list[ChunkRecord]:
    """Read all ``ChunkRecord`` rows listed in ``data/chunks/index.json``."""
    idx_path = index_path or Path(settings.chunk_index_path)
    if not idx_path.is_absolute():
        idx_path = repo_root / idx_path
    if not idx_path.exists():
        return []

    index = json.loads(idx_path.read_text(encoding="utf-8"))
    if index.get("schema_version") != INDEX_SCHEMA_VERSION:
        raise ValueError(f"Unsupported chunk index schema: {index.get('schema_version')}")

    records: list[ChunkRecord] = []
    for doc in index.get("documents", []):
        chunk_file = doc.get("chunk_file", "")
        path = Path(chunk_file)
        if not path.is_absolute():
            path = repo_root / path
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                records.append(ChunkRecord.model_validate(json.loads(line)))
    return records
