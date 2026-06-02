"""FastAPI application — health + Phase 5 RAG routes (architecture §11.4)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.groq.client import GroqChatClient
from api.routes import router as api_v1_router
from pipeline.index.hybrid_retrieval import retrieval_mode
from shared.chroma_client import chroma_health_check
from shared.config import settings
from shared.schemas import HealthResponse

_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app = FastAPI(
    title="India Medical RAG API",
    description="Human-in-the-Loop medical RAG API (Render + Vercel; Streamlit ops optional locally)",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        chroma_status = chroma_health_check()
    except Exception:
        chroma_status = "unreachable"
    return HealthResponse(
        status="ok",
        chroma=chroma_status,
        rag_retrieval=retrieval_mode(),
        groq_live=settings.groq_live,
        embed_mock=settings.embed_mock,
    )
