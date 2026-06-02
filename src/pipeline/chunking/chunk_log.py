"""Per-run audit log — data/chunk_log.jsonl (architecture §12.2)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shared.config import settings


class ChunkLogger:
    def __init__(self, path: Path | None = None) -> None:
        default = Path(settings.corpus_path).parent / "chunk_log.jsonl"
        self.path = path or default

    def append(self, event: str, **fields: Any) -> None:
        row = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event": event,
            **fields,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
