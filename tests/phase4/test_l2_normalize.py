"""Phase 4.2 — L2 normalization (architecture §8, gate 4.6.2)."""

import math

import pytest

from pipeline.embeddings import (
    BgeEmbeddingClient,
    L2_TOLERANCE,
    is_unit_vector,
    l2_norm,
    l2_normalize,
    l2_normalize_batch,
    mock_embedding_vector,
)


def test_l2_norm_known_vector():
    assert abs(l2_norm([3.0, 4.0]) - 5.0) < 1e-9


def test_l2_normalize_unit_length():
    raw = [3.0, 4.0, 0.0]
    normed = l2_normalize(raw)
    assert abs(l2_norm(normed) - 1.0) < L2_TOLERANCE
    assert abs(normed[0] - 0.6) < 1e-9
    assert abs(normed[1] - 0.8) < 1e-9


def test_l2_normalize_zero_vector_raises():
    with pytest.raises(ValueError, match="Zero vector"):
        l2_normalize([0.0, 0.0, 0.0])


def test_is_unit_vector():
    assert is_unit_vector(l2_normalize([1.0, 2.0, 3.0]))
    assert not is_unit_vector([1.0, 2.0, 3.0])


def test_l2_normalize_batch():
    batch = [[1.0, 0.0], [0.0, 2.0], [3.0, 4.0]]
    normed = l2_normalize_batch(batch)
    assert len(normed) == 3
    for vec in normed:
        assert abs(l2_norm(vec) - 1.0) < L2_TOLERANCE


def test_mock_bge_vectors_normalize_to_unit():
    """Mock embeddings from 4.1 are not unit length until normalized."""
    raw = mock_embedding_vector("clinical TB guidance passage")
    assert not is_unit_vector(raw)
    normed = l2_normalize(raw)
    assert len(normed) == 1024
    assert abs(l2_norm(normed) - 1.0) < L2_TOLERANCE


def test_bge_client_passages_normalize_to_unit():
    client = BgeEmbeddingClient(api_token="", mock=True)
    raw_vectors = client.embed_passages(["First chunk.", "Second chunk."])
    normed = l2_normalize_batch(raw_vectors)
    for vec in normed:
        assert abs(l2_norm(vec) - 1.0) < L2_TOLERANCE


def test_already_normalized_stays_unit():
    unit = l2_normalize([math.sqrt(0.5), math.sqrt(0.5)])
    again = l2_normalize(unit)
    assert abs(l2_norm(again) - 1.0) < L2_TOLERANCE
    assert abs(again[0] - unit[0]) < 1e-6
