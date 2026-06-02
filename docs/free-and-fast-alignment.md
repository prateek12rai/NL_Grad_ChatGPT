# Free & Fast Alignment (Non-Negotiable)

**Applies to:** All phases · [architecture.md](./architecture.md)

This project is a **portfolio/demo** system. It must stay **$0 on free tiers** and **quick to build and run**.

---

## Cost: what we use ($0)

| Component | Service | When it costs quota |
|-----------|---------|---------------------|
| User answers | **Groq** free tier | Each query (Phase 5) |
| Search vectors | **Hugging Face Inference** free tier (`BAAI/bge-large-en-v1.5`) | Phase 4 embed only |
| Vector storage | **Chroma** on disk | Never (local files) |
| Chunking | **CPU** (Python libraries) | Never |
| Backend UI | **Streamlit** free | Hosting only |
| Frontend | **Vercel** Hobby | Hosting only |
| Daily updates | **GitHub Actions** | CI minutes (free for public repos) |

### What we do NOT use (would cost money or complexity)

- Google Gemini paid / OpenAI paid for answers  
- Pinecone, Weaviate Cloud, or other hosted vector DBs  
- Embedding-based sentence merging during chunking (extra model)  
- LLM-based “smart chunking”  
- GPU servers  

---

## Speed: what keeps us quick

| Rule | Detail |
|------|--------|
| **1,000 document cap** | Oldest pruned automatically (Phase 2) |
| **Nature last 7 days** | Small rolling ingest |
| **Structural chunking** | Sections + sentences on CPU (Phases 3.2–3.3) |
| **tiktoken local** | Token limits without API (Phase 3.4) |
| **Skip unchanged** | Re-embed only when chunk text changes (Phase 4) |
| **Small retrieval** | ~8 chunks per question → fewer Groq tokens |
| **Fixture mode** | `--fixture` for offline dev without API calls |

Typical timing targets:

- Chunk one document: **seconds** (CPU)  
- Full daily GHA pipeline: **under ~30 minutes** at 1k doc cap  
- User question: **seconds** (local Chroma + one Groq call)  

---

## Phase-by-phase checklist

| Phase | Free? | Quick? | Notes |
|-------|-------|--------|-------|
| 1 Foundation | Yes | Yes | Local only |
| 2 Scraping | Yes | Yes | Network-bound; capped |
| 3 Chunking | **Yes** | **Yes** | **No HF/Groq in Phase 3** |
| 4 Embedding | Free tier | Moderate | HF at embed time only; mock + `content_hash` skip |
| 5 RAG + Groq | Free tier | Yes | `GROQ_MOCK` for offline; model fallback chain |
| 6 Vercel UI | Free tier | Yes | Static + API calls |
| 7 GHA schedule | Free tier | Moderate | Daily batch |

---

## Before adding any new feature

1. Does it require a **paid** API? → Stop or find a free tier.  
2. Does it call an API on **every document every day**? → Batch, cache, skip unchanged.  
3. Does it add a **large download model** for chunking? → Defer to optional v1.1.  

---

*Last updated: 2026-06-01 — aligned with structural Phase 3.3 decision.*
