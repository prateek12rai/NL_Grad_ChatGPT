"""
Keep only the N newest Nature HTML articles; rebuild manifest; drop chunks/Chroma.

  set PYTHONPATH=src
  python scripts/trim_corpus.py --keep 20
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import chromadb

from scraper.manifest import ManifestFile, ManifestStore, make_document_id, reindex_manifest
from shared.config import settings
from shared.schemas import DocumentRecord, SourceOrg


def _parse_ingest_log(log_path: Path) -> dict[str, dict]:
    """document_id -> latest ingest row."""
    by_id: dict[str, dict] = {}
    if not log_path.is_file():
        return by_id
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("event") != "document_ingested":
            continue
        doc_id = row["document_id"]
        by_id[doc_id] = row
    return by_id


def _html_meta(path: Path) -> tuple[str, str, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    title_m = re.search(r"<title>([^<]+)</title>", text, re.I)
    title = (title_m.group(1).strip() if title_m else path.stem)[:280]
    date_m = re.search(r"publicationDate=(\d{4}-\d{2}-\d{2})", text)
    if not date_m:
        date_m = re.search(
            r"Published[^<]*<time datetime=[\"'](\d{4}-\d{2}-\d{2})",
            text,
            re.I | re.S,
        )
    if not date_m:
        date_m = re.search(r'<time datetime="(\d{4}-\d{2}-\d{2})"', text)
    pub_date = date_m.group(1) if date_m else "1970-01-01"
    url_m = re.search(r'rel="canonical"\s+href="([^"]+)"', text)
    url = url_m.group(1) if url_m else ""
    return title, pub_date, url


def _record_from_file(path: Path, ingest: dict | None) -> DocumentRecord:
    title, pub_date, url = _html_meta(path)
    if ingest:
        url = ingest.get("source_url") or url
        doc_id = ingest["document_id"]
        ingested_at = ingest.get("timestamp", "").replace("Z", "Z") or "1970-01-01T00:00:00Z"
        if not url:
            url = f"https://www.nature.com/articles/unknown"
    else:
        doc_id = make_document_id(url or str(path), title)
        ingested_at = "1970-01-01T00:00:00Z"
    rel = path.relative_to(ROOT).as_posix()
    return DocumentRecord(
        document_id=doc_id,
        source_org=SourceOrg.NATURE,
        source_url=url,
        document_title=title,
        publication_date=pub_date,
        ingested_at=ingested_at if "T" in ingested_at else f"{ingested_at}T00:00:00Z",
        content_type="html",
        local_path=rel,
        chronological_rank=0,
    )


def _reset_chroma_collection() -> None:
    chroma_path = ROOT / settings.chroma_path
    if not chroma_path.is_dir():
        return
    client = chromadb.PersistentClient(path=str(chroma_path.resolve()))
    name = settings.chroma_collection_name
    try:
        client.delete_collection(name)
        print(f"Chroma collection deleted: {name}")
    except Exception as exc:
        print(f"Warning: could not delete Chroma collection ({exc}). Stop uvicorn and retry.")


def trim_corpus(keep: int, nature_dir: Path | None = None, *, reset_chroma: bool = True) -> None:
    nature_dir = nature_dir or (ROOT / settings.corpus_path / "nature")
    if not nature_dir.is_dir():
        raise SystemExit(f"No corpus at {nature_dir}")

    ingest_by_id = _parse_ingest_log(ROOT / "data" / "ingest_log.jsonl")
    records: list[DocumentRecord] = []

    for path in sorted(nature_dir.glob("*.html")):
        stem = path.stem  # sha256_abc...
        doc_id = None
        ingest_row = None
        for did, row in ingest_by_id.items():
            safe = did.replace(":", "_")
            if path.name == f"{safe}.html" or path.stem == safe:
                doc_id = did
                ingest_row = row
                break
        if ingest_row is None:
            records.append(_record_from_file(path, None))
        else:
            records.append(_record_from_file(path, ingest_row))

    records = sorted(
        records,
        key=lambda d: (d.publication_date, d.ingested_at),
        reverse=True,
    )
    keep_records = records[:keep]
    keep_paths = {ROOT / r.local_path for r in keep_records}
    keep_ids = {r.document_id for r in keep_records}

    removed_files = 0
    for path in nature_dir.glob("*.html"):
        if path.resolve() not in {p.resolve() for p in keep_paths}:
            path.unlink()
            removed_files += 1

    # Remove non-nature corpus trees (legacy PDFs)
    corpus_root = ROOT / settings.corpus_path
    for sub in ("dhr", "icmr"):
        legacy = corpus_root / sub
        if legacy.is_dir():
            shutil.rmtree(legacy)
            print(f"Removed legacy folder {legacy}")

    manifest = ManifestFile(documents=keep_records)
    manifest = reindex_manifest(manifest)
    ManifestStore(ROOT / "data" / "manifest.json").save(manifest)

    chunks_dir = ROOT / settings.chunk_output_dir
    if chunks_dir.is_dir():
        shutil.rmtree(chunks_dir)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    index_path = Path(settings.chunk_index_path)
    if not index_path.is_absolute():
        index_path = ROOT / index_path
    if index_path.exists():
        index_path.unlink()

    for log_name in ("chunk_log.jsonl", "embed_log.jsonl"):
        log_path = ROOT / "data" / log_name
        if log_path.is_file():
            log_path.write_text("", encoding="utf-8")

    if reset_chroma:
        _reset_chroma_collection()

    stats = ROOT / "data" / "chroma_stats.json"
    if stats.is_file():
        stats.unlink()

    print(f"Kept {len(keep_records)} newest HTML articles (removed {removed_files} files).")
    print(f"Manifest: data/manifest.json ({len(manifest.documents)} documents)")
    print("Re-chunk and re-embed: python -m pipeline.chunking.run --force && python -m pipeline.index.chroma_upsert")


def main() -> int:
    parser = argparse.ArgumentParser(description="Trim Nature corpus to N newest HTML articles")
    parser.add_argument("--keep", type=int, default=20, help="Number of articles to keep")
    parser.add_argument(
        "--no-reset-chroma",
        action="store_true",
        help="Keep existing Chroma vectors (default: drop collection)",
    )
    args = parser.parse_args()
    trim_corpus(args.keep, reset_chroma=not args.no_reset_chroma)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
