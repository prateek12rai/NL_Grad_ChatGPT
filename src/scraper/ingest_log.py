"""Per-run audit log — data/ingest_log.jsonl (architecture §8.2)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shared.config import settings


class IngestLogger:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (Path(settings.corpus_path).parent / "ingest_log.jsonl")

    def append(self, event: str, source: str, **fields: Any) -> None:
        row = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event": event,
            "source": source,
            **fields,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
