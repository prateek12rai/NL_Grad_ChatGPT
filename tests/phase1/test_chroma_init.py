"""Phase 1.5.5 — Chroma PersistentClient smoke."""

from shared.chroma_client import COLLECTION_NAME, get_or_create_collection


def test_creates_india_medical_local_collection(tmp_chroma_path):
    collection = get_or_create_collection()
    assert collection.name == COLLECTION_NAME
    assert collection.count() >= 0


def test_collection_persists_after_reopen(tmp_chroma_path):
    get_or_create_collection()
    again = get_or_create_collection()
    assert again.name == COLLECTION_NAME
