"""
Streamlit operational app — Phase 5 dashboard + query tester.
Deploy target: Streamlit Cloud (architecture §11.6).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from api.groq import GroqChatClient, model_chain
from api.rag import run_rag_query
from pipeline.index.chroma_store import ChromaStore
from shared.chroma_client import COLLECTION_NAME, chroma_health_check
from shared.config import settings

st.set_page_config(
    page_title="Medical RAG — Backend",
    page_icon="🏥",
    layout="wide",
)

st.title("India Medical RAG — Backend Console")
st.caption("Phase 5 — retrieval, Groq answers, verification sessions (HITL UI on Vercel in Phase 6)")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Chroma")
    try:
        status = chroma_health_check()
        store = ChromaStore()
        st.success(f"`{COLLECTION_NAME}` — {status} ({store.count()} vectors)")
    except Exception as exc:
        st.error(f"Chroma: {exc}")

with col2:
    st.subheader("Groq")
    mock = settings.groq_mock or not settings.groq_api_key
    st.info("Mock mode" if mock else "Live API key configured")
    st.code("\n".join(model_chain()), language="text")

with col3:
    st.subheader("Config")
    stats_path = Path(settings.corpus_path).parent / "chroma_stats.json"
    if stats_path.exists():
        st.json(json.loads(stats_path.read_text(encoding="utf-8")))
    else:
        st.warning("No chroma_stats.json — run chroma_upsert first")

st.divider()
st.subheader("Query tester (local RAG + Groq)")
if "clinical_query" not in st.session_state:
    st.session_state["clinical_query"] = ""
auto_run = False
if auto := st.session_state.pop("auto_run_query", None):
    st.session_state["clinical_query"] = auto
    auto_run = True

st.text_area(
    "Clinical / policy question",
    placeholder="e.g. What do guidelines say about Bedaquiline for resistant TB?",
    height=100,
    key="clinical_query",
)
run_query = st.button("Run RAG query", type="primary") or auto_run

if run_query and st.session_state["clinical_query"].strip():
    query = st.session_state["clinical_query"].strip()
    with st.spinner("Retrieving and generating…"):
        try:
            result = run_rag_query(query)
            st.markdown(f"**Model:** `{result.model_used}` · **Retrieval:** {result.retrieval_ms:.0f} ms")
            st.markdown(result.answer)
            if result.out_of_corpus and result.suggested_queries:
                st.markdown("**Suggested verified topics** (click to ask)")
                for s in result.suggested_queries:
                    if st.button(s.label, key=f"suggest_{s.chunk_id}"):
                        st.session_state["auto_run_query"] = s.query
                        st.rerun()
            if result.citations:
                st.markdown("**Citations**")
                for c in result.citations:
                    color = "green" if c.verification_status.value == "verified" else "orange"
                    st.markdown(
                        f":{color}[**[{c.index}]**] `{c.chunk_id}` — {c.document_title} "
                        f"({c.verification_status.value})"
                    )
                st.caption(
                    f"Session ID: `{result.session_id}` — export is allowed for this question only "
                    "after cited sources are verified."
                )
            elif result.out_of_corpus:
                st.warning("Out of corpus — no citations for this question.")
        except Exception as exc:
            st.error(str(exc))

st.info(
    "REST API: `POST /api/v1/query`, `GET /api/v1/chunks/{id}`, "
    "`PATCH /api/v1/sessions/{id}/verify/{chunk_id}`, `GET .../export-gate`. "
    "Start with `scripts/start_backend.ps1` or uvicorn on port 8000."
)
