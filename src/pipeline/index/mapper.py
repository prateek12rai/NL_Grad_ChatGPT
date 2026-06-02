"""
Phase 4.3 — map ChunkRecord + embedding to Chroma upsert fields (architecture §9.3).
"""

from __future__ import annotations

from shared.schemas import ChunkRecord

ChromaScalar = str | int | float | bool


def validate_chroma_metadata(metadata: dict) -> dict[str, ChromaScalar]:
    """Chroma accepts only scalar metadata values (architecture §9.4)."""
    cleaned: dict[str, ChromaScalar] = {}
    for key, value in metadata.items():
        if not isinstance(value, (str, int, float, bool)):
            raise TypeError(
                f"Chroma metadata field '{key}' must be str/int/float/bool, got {type(value)!r}"
            )
        cleaned[key] = value
    return cleaned


def chunk_to_chroma_metadata(chunk: ChunkRecord) -> dict[str, ChromaScalar]:
    """PRD metadata + ``content_hash`` for incremental skip (architecture §10.1)."""
    meta = chunk.to_chunk_metadata().to_chroma_metadata()
    meta["content_hash"] = chunk.content_hash
    return validate_chroma_metadata(meta)


def build_upsert_payload(
    chunks: list[ChunkRecord],
    embeddings: list[list[float]],
) -> dict[str, list]:
    """
  Build kwargs for ``collection.upsert``.

  | Chroma field | Source |
  |--------------|--------|
  | ids | chunk_id |
  | documents | exact_context |
  | embeddings | L2-normalized vector |
  | metadatas | PRD metadata |
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"chunks length {len(chunks)} != embeddings length {len(embeddings)}"
        )
    if not chunks:
        return {"ids": [], "embeddings": [], "documents": [], "metadatas": []}

    return {
        "ids": [c.chunk_id for c in chunks],
        "embeddings": embeddings,
        "documents": [c.exact_context for c in chunks],
        "metadatas": [chunk_to_chroma_metadata(c) for c in chunks],
    }
