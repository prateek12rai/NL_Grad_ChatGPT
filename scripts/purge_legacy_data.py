"""
Remove non-Nature corpus artifacts (legacy DHR/ICMR/PDF paths) from data + Chroma.

  set PYTHONPATH=src
  python scripts/purge_legacy_data.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import chromadb

from scraper.manifest import ManifestStore, reindex_manifest
from shared.config import settings
from shared.schemas import SourceOrg


def _is_nature_doc(doc: dict) -> bool:
    org = str(doc.get("source_org", ""))
    url = str(doc.get("source_url", "")).lower()
    path = str(doc.get("local_path", "")).lower()
    if org == SourceOrg.NATURE.value:
        return True
    if "nature.com/articles" in url:
        return True
    if "/corpus/nature/" in path and path.endswith(".html"):
        return True
    return False


def purge_manifest() -> int:
    store = ManifestStore(ROOT / "data" / "manifest.json")
    manifest = store.load()
    before = len(manifest.documents)
    manifest.documents = [d for d in manifest.documents if _is_nature_doc(d.model_dump())]
    manifest.pruned_document_ids = []
    manifest = reindex_manifest(manifest)
    store.save(manifest)
    return before - len(manifest.documents)


def purge_corpus_dirs() -> None:
    corpus = ROOT / settings.corpus_path
    for sub in ("dhr", "icmr"):
        path = corpus / sub
        if path.is_dir():
            shutil.rmtree(path)
            print(f"Removed {path}")


def purge_chunk_files() -> int:
    chunk_dir = ROOT / settings.chunk_output_dir
    if not chunk_dir.is_dir():
        return 0
    removed = 0
    store = ManifestStore(ROOT / "data" / "manifest.json")
    keep_docs = {d.document_id for d in store.load().documents}
    for jsonl in chunk_dir.glob("*.jsonl"):
        # chunk files named sha256_xxx.jsonl — match manifest doc ids
        stem = jsonl.stem.replace("_", ":")
        doc_prefix = stem.split("::")[0] if "::" in stem else stem
        if doc_prefix not in keep_docs and not any(
            k.replace(":", "_") in jsonl.stem for k in keep_docs
        ):
            jsonl.unlink(missing_ok=True)
            meta = jsonl.with_suffix(".meta.json")
            meta.unlink(missing_ok=True)
            removed += 1
    # Only drop the index if we actually removed orphan chunks (it must be rebuilt after).
    if removed:
        index = ROOT / settings.chunk_index_path
        if index.is_file():
            index.unlink()
    return removed


def purge_chroma_non_nature() -> int:
    chroma_path = ROOT / settings.chroma_path
    if not chroma_path.is_dir():
        return 0
    client = chromadb.PersistentClient(path=str(chroma_path.resolve()))
    try:
        coll = client.get_collection(settings.chroma_collection_name)
    except Exception:
        return 0
    result = coll.get(include=["metadatas"])
    ids = result.get("ids") or []
    metas = result.get("metadatas") or []
    to_delete: list[str] = []
    for cid, meta in zip(ids, metas):
        if not meta:
            continue
        org = str(meta.get("source_org", ""))
        url = str(meta.get("source_url", "")).lower()
        if org != SourceOrg.NATURE.value and "nature.com/articles" not in url:
            to_delete.append(cid)
    if to_delete:
        coll.delete(ids=to_delete)
    return len(to_delete)


def main() -> int:
    print("Purging legacy DHR/ICMR/non-Nature data…")
    purge_corpus_dirs()
    removed_manifest = purge_manifest()
    manifest = ManifestStore(ROOT / "data" / "manifest.json").load()
    print(f"Manifest: kept {len(manifest.documents)} Nature docs (removed {removed_manifest})")
    removed_chunks = purge_chunk_files()
    print(f"Orphan chunk files removed: {removed_chunks}")
    removed_vectors = purge_chroma_non_nature()
    print(f"Chroma vectors removed (non-Nature): {removed_vectors}")
    if removed_manifest or removed_chunks or removed_vectors:
        print("Data changed — rebuild the chunk index and embeddings:")
        print("  python -m pipeline.chunking.run --manifest data/manifest.json --force")
        print("  python -m pipeline.index.chroma_upsert")
    else:
        print("No legacy data found — corpus is already Nature-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
