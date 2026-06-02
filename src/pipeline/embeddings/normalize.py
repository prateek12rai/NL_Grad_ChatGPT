"""
Phase 4.2 — L2 normalization for BGE embeddings (architecture §8, gate 4.6.2).

PRD: v_norm = v / ||v||_2  with ||v_norm||_2 = 1 (tolerance 1e-5).
"""

from __future__ import annotations

import math

L2_TOLERANCE = 1e-5


def l2_norm(vector: list[float]) -> float:
    """Euclidean norm ||v||_2."""
    return math.sqrt(sum(x * x for x in vector))


def l2_normalize(vector: list[float]) -> list[float]:
    """Scale vector to unit length; raises if zero vector."""
    norm = l2_norm(vector)
    if norm == 0.0:
        raise ValueError("Zero vector cannot be normalized")
    return [x / norm for x in vector]


def l2_normalize_batch(vectors: list[list[float]]) -> list[list[float]]:
    """Normalize each vector in place logically (new lists returned)."""
    return [l2_normalize(v) for v in vectors]


def is_unit_vector(vector: list[float], *, tolerance: float = L2_TOLERANCE) -> bool:
    """True when ||v||_2 is within tolerance of 1.0."""
    if not vector:
        return False
    return abs(l2_norm(vector) - 1.0) < tolerance
