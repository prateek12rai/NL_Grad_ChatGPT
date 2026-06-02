"""In-memory verification sessions for HITL (Phase 5.4)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from shared.schemas import ExportGateResponse, VerificationStatus


@dataclass
class CitationEntry:
    index: int
    chunk_id: str
    document_title: str
    verification_status: VerificationStatus
    source_url: str = ""
    publication_date: str = ""


@dataclass
class QuerySession:
    session_id: str
    citations: list[CitationEntry] = field(default_factory=list)
    # Citation indices referenced in the model answer (export gate uses these only)
    cited_indices: set[int] = field(default_factory=set)
    # HITL: export unlocks only after user clicks verify in this session (not Chroma history)
    verified_chunk_ids: set[str] = field(default_factory=set)
    # True when the user was asked to clarify; next query may retry or get pinky promise
    awaiting_clarification: bool = False


class SessionStore:
    """Process-local session store (portfolio scale)."""

    def __init__(self) -> None:
        self._sessions: dict[str, QuerySession] = {}

    def create(
        self,
        citations: list[CitationEntry],
        *,
        cited_indices: set[int] | None = None,
        awaiting_clarification: bool = False,
    ) -> QuerySession:
        session_id = str(uuid.uuid4())
        session = QuerySession(
            session_id=session_id,
            citations=citations,
            cited_indices=cited_indices or set(),
            awaiting_clarification=awaiting_clarification,
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> QuerySession | None:
        return self._sessions.get(session_id)

    def mark_verified(self, session_id: str, chunk_id: str) -> bool:
        session = self.get(session_id)
        if not session:
            return False
        for citation in session.citations:
            if citation.chunk_id == chunk_id:
                citation.verification_status = VerificationStatus.VERIFIED
                session.verified_chunk_ids.add(chunk_id)
                return True
        return False

    def clear(self) -> None:
        """Test helper — reset all sessions."""
        self._sessions.clear()

    def _export_scope(self, session: QuerySession) -> list[CitationEntry]:
        """Only citations used in this answer count toward export (per-query HITL)."""
        if session.cited_indices:
            return [c for c in session.citations if c.index in session.cited_indices]
        return list(session.citations)

    def export_gate(self, session_id: str) -> ExportGateResponse | None:
        session = self.get(session_id)
        if not session:
            return None
        scope = self._export_scope(session)
        total = len(scope)
        verified = sum(1 for c in scope if c.chunk_id in session.verified_chunk_ids)
        pending = [
            c.index for c in scope if c.chunk_id not in session.verified_chunk_ids
        ]
        return ExportGateResponse(
            allowed=total > 0 and verified == total,
            total=total,
            verified=verified,
            pending_indices=pending,
        )


# Shared singleton for FastAPI app
session_store = SessionStore()
