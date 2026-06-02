"""Corpus cap enforcement — max 1000 documents (architecture §8.6)."""

from __future__ import annotations

from pathlib import Path

from shared.config import settings

from scraper.manifest import ManifestFile, ManifestStore, reindex_manifest


def prune_manifest(
    manifest: ManifestFile,
    max_documents: int | None = None,
    corpus_root: Path | None = None,
    repo_root: Path | None = None,
) -> tuple[ManifestFile, list[str]]:
    """
    Remove oldest documents when count exceeds max_documents.
    Returns updated manifest and list of pruned document_ids.
    """
    cap = max_documents if max_documents is not None else settings.max_documents
    corpus_root = corpus_root or Path(settings.corpus_path)
    repo_root = repo_root or Path.cwd()

    manifest = reindex_manifest(manifest)
    if len(manifest.documents) <= cap:
        return manifest, []

    # chronological_rank 1 = newest; higher rank = older
    sorted_by_age = sorted(manifest.documents, key=lambda d: d.chronological_rank, reverse=True)
    to_remove = sorted_by_age[: len(manifest.documents) - cap]
    keep_ids = {d.document_id for d in manifest.documents} - {d.document_id for d in to_remove}

    pruned_ids: list[str] = []
    for doc in to_remove:
        pruned_ids.append(doc.document_id)
        file_path = Path(doc.local_path)
        if not file_path.is_absolute():
            file_path = repo_root / file_path
        if file_path.exists():
            file_path.unlink()

    manifest.documents = [d for d in manifest.documents if d.document_id in keep_ids]
    manifest.pruned_document_ids.extend(pruned_ids)
    manifest = reindex_manifest(manifest)
    return manifest, pruned_ids
