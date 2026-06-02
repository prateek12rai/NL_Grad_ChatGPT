"""Export gate is per query session and only for citations used in the answer."""

from api.sessions.store import CitationEntry, SessionStore
from shared.schemas import VerificationStatus


def test_export_gate_only_cited_indices():
    store = SessionStore()
    citations = [
        CitationEntry(1, "chunk-a", "Doc A", VerificationStatus.UNVERIFIED),
        CitationEntry(2, "chunk-b", "Doc B", VerificationStatus.UNVERIFIED),
    ]
    session = store.create(citations, cited_indices={2})
    assert store.mark_verified(session.session_id, "chunk-b")

    gate = store.export_gate(session.session_id)
    assert gate is not None
    assert gate.total == 1
    assert gate.verified == 1
    assert gate.allowed is True
    assert gate.pending_indices == []
