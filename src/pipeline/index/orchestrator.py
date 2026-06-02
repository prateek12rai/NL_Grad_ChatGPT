"""
Phase 4.4 — embed + upsert orchestrator with prune cascade and hash skip.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pipeline.embeddings import BgeEmbeddingClient, l2_normalize_batch
from pipeline.embeddings.batch_planner import plan_batches
from pipeline.index.chroma_store import ChromaStore
from pipeline.index.delete import delete_pruned_documents
from pipeline.index.embed_log import EmbedLogger
from pipeline.index.loader import load_chunks_from_index
from scraper.manifest import ManifestStore
from shared.config import settings
from shared.schemas import ChunkRecord, VerificationStatus

STATS_SCHEMA_VERSION = "1"


@dataclass
class IndexResult:
    chunks_embedded: int = 0
    chunks_skipped_unchanged: int = 0
    chunks_deleted: int = 0
    chunks_errors: int = 0
    pruned_documents: int = 0
    dry_run: bool = False


class IndexOrchestrator:
    def __init__(
        self,
        repo_root: Path | None = None,
        *,
        chroma_store: ChromaStore | None = None,
        embed_client: BgeEmbeddingClient | None = None,
        manifest_store: ManifestStore | None = None,
        logger: EmbedLogger | None = None,
    ) -> None:
        self.repo_root = (repo_root or Path.cwd()).resolve()
        self.store = chroma_store or ChromaStore()
        self.embed_client = embed_client or BgeEmbeddingClient()
        data_dir = Path(settings.corpus_path).parent
        self.manifest_store = manifest_store or ManifestStore(data_dir / "manifest.json")
        self.logger = logger or EmbedLogger(data_dir / "embed_log.jsonl")
        self.stats_path = data_dir / "chroma_stats.json"

    def run(
        self,
        *,
        dry_run: bool = False,
        prune_only: bool = False,
        clear_pruned_manifest: bool = True,
    ) -> IndexResult:
        result = IndexResult(dry_run=dry_run)
        self.logger.append("index_run_start", dry_run=dry_run, prune_only=prune_only)

        pruned_ids = self.manifest_store.load().pruned_document_ids
        if pruned_ids:
            result.pruned_documents = len(pruned_ids)
            if dry_run:
                would_delete = sum(
                    1
                    for cid in self.store.list_chunk_ids()
                    if cid.startswith(tuple(f"{d}::" for d in pruned_ids))
                )
                result.chunks_deleted = would_delete
            else:
                result.chunks_deleted = delete_pruned_documents(self.store, pruned_ids)
                self.logger.append(
                    "prune_cascade_complete",
                    document_ids=pruned_ids,
                    chunks_deleted=result.chunks_deleted,
                )
                if clear_pruned_manifest:
                    self._clear_pruned_manifest()

        if prune_only:
            self._write_stats(result)
            self.logger.append("index_run_complete", **result.__dict__)
            return result

        chunks = load_chunks_from_index(self.repo_root)
        to_embed = self._select_chunks_for_embed(chunks, result)

        if dry_run:
            result.chunks_embedded = len(to_embed)
            self._write_stats(result)
            self.logger.append("index_run_complete", **result.__dict__)
            return result

        self._embed_and_upsert(to_embed, result)
        self._write_stats(result)
        self.logger.append("index_run_complete", **result.__dict__)
        return result

    def _clear_pruned_manifest(self) -> None:
        manifest = self.manifest_store.load()
        if not manifest.pruned_document_ids:
            return
        manifest.pruned_document_ids = []
        self.manifest_store.save(manifest)

    def _select_chunks_for_embed(
        self,
        chunks: list[ChunkRecord],
        result: IndexResult,
    ) -> list[ChunkRecord]:
        pending: list[ChunkRecord] = []
        for chunk in chunks:
            stored = self.store.get_chunk_metadata(chunk.chunk_id)
            if stored:
                stored_hash = stored.get("content_hash")
                if stored_hash and stored_hash == chunk.content_hash:
                    result.chunks_skipped_unchanged += 1
                    self.logger.append(
                        "chunk_skipped_unchanged",
                        chunk_id=chunk.chunk_id,
                    )
                    continue
                chunk = chunk.model_copy(
                    update={"verification_status": VerificationStatus.UNVERIFIED}
                )
            pending.append(chunk)
        return pending

    def _embed_and_upsert(
        self,
        chunks: list[ChunkRecord],
        result: IndexResult,
    ) -> None:
        texts = [c.exact_context for c in chunks]
        batches = plan_batches(texts)

        offset = 0
        for batch_texts in batches:
            batch_chunks = chunks[offset : offset + len(batch_texts)]
            offset += len(batch_texts)
            try:
                vectors = l2_normalize_batch(self.embed_client.embed_passages(batch_texts))
                self.store.upsert_chunks(batch_chunks, vectors)
                result.chunks_embedded += len(batch_chunks)
                for chunk in batch_chunks:
                    self.logger.append(
                        "chunk_embedded",
                        chunk_id=chunk.chunk_id,
                        content_hash=chunk.content_hash,
                    )
            except Exception as exc:
                result.chunks_errors += len(batch_chunks)
                for chunk in batch_chunks:
                    self.logger.append(
                        "chunk_embed_error",
                        chunk_id=chunk.chunk_id,
                        error=str(exc),
                    )

    def _write_stats(self, result: IndexResult) -> None:
        payload = {
            "schema_version": STATS_SCHEMA_VERSION,
            "collection": self.store.collection_name,
            "total_vectors": self.store.count(),
            "embedding_model": settings.embed_model_id,
            "embedding_dimension": settings.bge_dimension,
            "last_indexed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "chunks_skipped_unchanged": result.chunks_skipped_unchanged,
            "chunks_embedded": result.chunks_embedded,
            "chunks_deleted": result.chunks_deleted,
            "chunks_errors": result.chunks_errors,
            "dry_run": result.dry_run,
        }
        self.stats_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.stats_path.with_name(self.stats_path.name + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self.stats_path)
