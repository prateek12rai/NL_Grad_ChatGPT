"""
Patch legacy fixture Nature URLs in chunk JSONL + Chroma metadata.

Run from repo root:
  set PYTHONPATH=src
  python scripts/patch_nature_source_urls.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pipeline.index.chroma_store import ChromaStore
from shared.config import settings
from shared.source_links import FIXTURE_URL_REPLACEMENTS

TITLE_BY_URL = {
    "https://www.nature.com/articles/s41467-026-73798-3": (
        "BNT162b2 LP.8.1 early vaccine effectiveness against COVID-19 ED/UC visits"
    ),
    "https://www.nature.com/articles/s41467-026-70664-0": (
        "Optimizing global genomic surveillance for early detection of SARS-CoV-2 variants"
    ),
}


def patch_jsonl(path: Path) -> int:
    if not path.is_file():
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    updated = 0
    out: list[str] = []
    for line in lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        old = rec.get("source_url", "")
        if old in FIXTURE_URL_REPLACEMENTS:
            new = FIXTURE_URL_REPLACEMENTS[old]
            rec["source_url"] = new
            if new in TITLE_BY_URL:
                rec["document_title"] = TITLE_BY_URL[new]
            updated += 1
        out.append(json.dumps(rec, ensure_ascii=False))
    path.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")
    return updated


def patch_manifest(manifest_path: Path) -> int:
    if not manifest_path.is_file():
        return 0
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    count = 0
    for entry in data.get("documents", []):
        old = entry.get("source_url", "")
        if old in FIXTURE_URL_REPLACEMENTS:
            entry["source_url"] = FIXTURE_URL_REPLACEMENTS[old]
            count += 1
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return count


def patch_chroma() -> int:
    store = ChromaStore()
    if store.count() == 0:
        return 0
    result = store.collection.get(include=["metadatas"])
    ids = result.get("ids") or []
    metadatas = result.get("metadatas") or []
    patched = 0
    for chunk_id, meta in zip(ids, metadatas):
        if not meta:
            continue
        old = str(meta.get("source_url", ""))
        if old not in FIXTURE_URL_REPLACEMENTS:
            continue
        new = FIXTURE_URL_REPLACEMENTS[old]
        updated = dict(meta)
        updated["source_url"] = new
        if new in TITLE_BY_URL:
            updated["document_title"] = TITLE_BY_URL[new]
        store.collection.update(ids=[chunk_id], metadatas=[updated])
        patched += 1
    return patched


def main() -> None:
    chunks_dir = Path(settings.chunk_output_dir)
    n_jsonl = sum(patch_jsonl(p) for p in chunks_dir.glob("*.jsonl"))
    n_manifest = patch_manifest(ROOT / "data" / "manifest.json")
    n_chroma = patch_chroma()
    print(
        f"Patched {n_jsonl} chunk line(s), {n_manifest} manifest entry(ies), "
        f"{n_chroma} Chroma vector(s)."
    )


if __name__ == "__main__":
    main()
