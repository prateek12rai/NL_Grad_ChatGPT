"""
Phase 4.5 — Chroma index verification checks (architecture §11.1).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.embeddings import BgeEmbeddingClient
from pipeline.embeddings.normalize import L2_TOLERANCE, is_unit_vector, l2_norm
from pipeline.index.chroma_store import COLLECTION_METADATA, ChromaStore
from pipeline.index.retriever import retrieve
from shared.config import settings

REQUIRED_METADATA_KEYS = frozenset(
    {
        "source_url",
        "document_title",
        "publication_year",
        "page_number",
        "exact_context",
        "verification_status",
        "source_org",
        "chunk_id",
        "content_hash",
    }
)

SAMPLE_QUERY = "tuberculosis Bedaquiline treatment guidelines"


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class VerifyReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append(CheckResult(name=name, passed=passed, detail=detail))


def load_expected_count(repo_root: Path | None = None) -> int | None:
    """Prefer ``chroma_stats.json``, else chunk ``index.json`` total_chunks."""
    root = repo_root or Path.cwd()
    stats_path = Path(settings.corpus_path).parent / "chroma_stats.json"
    if not stats_path.is_absolute():
        stats_path = root / stats_path
    if stats_path.exists():
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
        return int(stats.get("total_vectors", 0))

    index_path = Path(settings.chunk_index_path)
    if not index_path.is_absolute():
        index_path = root / index_path
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        return int(index.get("total_chunks", 0))
    return None


def verify_chroma_index(
    *,
    chroma_path: Path | str | None = None,
    expected_count: int | None = None,
    embed_client: BgeEmbeddingClient | None = None,
    repo_root: Path | None = None,
    sample_query: str | None = None,
) -> VerifyReport:
    """Run all Phase 4.5 verification checks."""
    report = VerifyReport()
    root = (repo_root or Path.cwd()).resolve()
    client = embed_client or BgeEmbeddingClient()
    query_text = sample_query or SAMPLE_QUERY

    store = ChromaStore(path=chroma_path)
    collection = store.collection

    # Collection exists
    try:
        names = [c.name for c in store.client.list_collections()]
        exists = store.collection_name in names
        report.add(
            "collection_exists",
            exists,
            f"found={store.collection_name}, collections={names}",
        )
    except Exception as exc:
        report.add("collection_exists", False, str(exc))
        return report

    meta = collection.metadata or {}
    cosine_ok = meta.get("hnsw:space") == COLLECTION_METADATA["hnsw:space"]
    report.add(
        "collection_cosine_metadata",
        cosine_ok,
        f"metadata={meta}",
    )

    count = store.count()
    expected = expected_count
    if expected is None:
        expected = load_expected_count(root)
    if expected is not None:
        report.add(
            "vector_count",
            count == expected,
            f"count={count}, expected={expected}",
        )
    else:
        report.add("vector_count", count >= 0, f"count={count} (no expected baseline)")

    # Sample offline query
    if count > 0:
        try:
            hits = retrieve(
                query_text,
                top_k=min(8, count),
                store=store,
                embed_client=client,
            )
            report.add(
                "sample_query",
                len(hits) > 0,
                f"n_results={len(hits)}",
            )
        except Exception as exc:
            report.add("sample_query", False, str(exc))
    else:
        report.add("sample_query", False, "collection empty")

    # Persistence — reopen client
    try:
        count_before = count
        again = ChromaStore(path=chroma_path)
        count_after = again.count()
        report.add(
            "persistence_reopen",
            count_after == count_before,
            f"before={count_before}, after={count_after}",
        )
    except Exception as exc:
        report.add("persistence_reopen", False, str(exc))

    # L2 norm spot-check
    if count > 0:
        sample_n = min(10, count)
        fetched = collection.get(include=["embeddings"], limit=sample_n)
        embeddings = fetched.get("embeddings") or []
        bad = []
        for vec in embeddings:
            if vec is None:
                bad.append("missing")
            elif not is_unit_vector(vec, tolerance=L2_TOLERANCE):
                bad.append(f"norm={l2_norm(vec):.6f}")
        report.add(
            "l2_norm_spot_check",
            len(bad) == 0,
            f"checked={len(embeddings)}, failures={bad[:3]}",
        )
    else:
        report.add("l2_norm_spot_check", False, "collection empty")

    # Metadata keys on sample
    if count > 0:
        fetched = collection.get(include=["metadatas"], limit=1)
        metas = fetched.get("metadatas") or []
        if metas and metas[0]:
            keys = set(metas[0].keys())
            missing = REQUIRED_METADATA_KEYS - keys
            report.add(
                "metadata_keys",
                len(missing) == 0,
                f"missing={sorted(missing)}" if missing else "all present",
            )
        else:
            report.add("metadata_keys", False, "no metadata returned")
    else:
        report.add("metadata_keys", False, "collection empty")

    return report
