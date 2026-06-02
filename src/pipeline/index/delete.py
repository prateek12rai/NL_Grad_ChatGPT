"""Phase 4.4 — prune cascade deletes (architecture §10.2)."""

from __future__ import annotations

from pipeline.index.chroma_store import ChromaStore


def delete_pruned_documents(
    store: ChromaStore,
    pruned_document_ids: list[str],
) -> int:
    """Delete Chroma rows for each pruned ``document_id``."""
    return store.delete_for_document_ids(pruned_document_ids)
