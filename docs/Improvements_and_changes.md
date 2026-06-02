# Improvements and changes (from start → today)

This file is a running project changelog for **ChatGPT Glass** (Nature-only medical RAG + HITL verification). It summarizes what was built, what was changed, and why.

> Note: this workspace is **not a git repo**, so this log is timeline-based (Phase gates + implementation milestones), not commit-based.

---

## Product direction (big shifts)

- **Branding**: UI renamed to **ChatGPT Glass** with tagline **“(We deliver Real facts only)”**.
- **Corpus scope tightened**: moved to a **Nature-only** portfolio index (small + fast), with strict “medical research only” behavior.
- **HITL-first UX**: copy/share stays locked until **all citations in the answer are verified**.

---

## Phase 1 — Foundation & contracts (gate PASS)

- **Repo scaffold**: `src/`, `tests/phaseN/`, `frontend/`, `backend/`.
- **Shared schemas**: request/response models and metadata contracts in `src/shared/schemas.py`.
- **Config system**: environment-backed settings in `src/shared/config.py` (mock modes supported).
- **PII protection**: baseline PII filter (Aadhaar/PAN/etc.) and fixtures.
- **Health endpoints and stubs**: minimal API + Streamlit health wiring.

Evidence: `docs/phase-reports/phase-1-gate.md`

---

## Phase 2 — Ingestion & scraping (gate PASS)

- **Scraper orchestration**: ingestion scheduler CLI `src/scraper/scheduler.py`.
- **Manifest + logs**: `data/manifest.json` and `data/ingest_log.jsonl` created/maintained.
- **Fixture mode**: offline fixtures for safe tests (no live website dependency).
- **Nature URL enforcement**: strict URL compliance tests (portfolio search query constraints).

Evidence: `docs/phase-reports/phase-2-gate.md`

---

## Phase 3 — Chunking & cleanup (gate PASS)

- **HTML extraction improvements**: stripped boilerplate UI from Nature pages during ingest/chunking.
- **Semantic chunking**: max token cap + overlap; stable `chunk_id` format and chunk index.
- **Noise filtering**: dropped placeholder/UI-noise chunks so embeddings index real prose.

Evidence: `docs/phase-reports/phase-3-gate.md`

---

## Phase 4 — Embeddings + local Chroma (gate PASS)

- **Chroma PersistentClient**: local-disk vector store (no cloud vector DB).
- **Mock embeddings**: fully offline development mode for embeddings.
- **Index orchestration**: `python -m pipeline.index.chroma_upsert` upserts + supports prune cascade.
- **Safety metadata**: Chroma collection metadata now records whether the index is **mock** vs **live** so retrieval mode stays correct in tests and demos.

Evidence: `docs/phase-reports/phase-4-gate.md`

---

## Phase 5 — RAG backend + safety gates (gate PASS)

### Retrieval + generation
- **RAG orchestrator**: `src/api/rag/orchestrator.py` (analyze → retrieve → prompt → Groq → citations).
- **Hybrid retrieval**: vector/lexical fallback (`retrieve_for_rag` path).
- **Session isolation**: every query returns a new `session_id`, verification state is per-session.

### Safety / “Pinky Promise”
- **Relevance gate**: multi-stage guardrail to refuse out-of-corpus questions early and reliably.
- **Non-medical blocking**: off-topic queries trigger Pinky Promise without citations.
- **Post-LLM refusal detection**: detects “insufficient information” style answers and refuses even if formatting is wrong.
- **Spelling fix**: “Invalid” corrected in the Pinky Promise core message.

### Date/list behavior
- **LIST-by-date deterministic path**: “show me all research on YYYY-MM-DD” bypasses the LLM and returns **up to 3 articles with links** (configurable via `rag_list_max_documents=3`).
- **Date not found edge case**: if the user asks for a date with no indexed data, API returns:
  - “Sorry, we don’t have any articles for <date>…”
  - plus **top 3 verifiable articles** as clickable suggestions.

Evidence: `docs/phase-reports/phase-5-gate.md`

---

## Phase 6 — Frontend HITL console + premium UI (gate PASS)

### Core UX improvements
- **ChatGPT-like landing** with rotating starter prompts (refreshed per new chat).
- **Multi-line query input** (`textarea`) for long questions.
- **“You asked” block**: shows the user’s question above the answer; input clears after response.
- **Answer normalization**: frontend markdown normalizer ensures headings/bullets render consistently.

### HITL verification + export lock
- **Citation row design**: “Open article” uses a button (prevents bottom-left URL hover).
- **Verify flow**: clear “review then verify” nudges; verified state updates UI.
- **Share prototype**: share menu shows logos only (no external calls); copy/share locked until verified.

### Premium “glass” theme
- Added an **optional premium landing** (`frontend/src/components/GlassLandingPremium.tsx`) with gradient + glass cards + floating input.
- Applied glass/gradient polish across conversation surfaces (pane/header/export/share popover).
- Increased share popover opacity + blur to avoid background text bleeding through.

Evidence: `docs/phase-reports/phase-6-gate.md`

---

## Phase 7 — GitHub Actions scheduler (implemented; gate awaiting GitHub run)

### What was implemented
- Workflow: `.github/workflows/daily-ingest.yml`
  - Cron: **06:00 IST** (`30 0 * * *`)
  - Manual runs: `workflow_dispatch` with `dry_run`
  - Pipeline: ingest → chunk → embed/upsert → tests → commit artifacts (non-dry-run only)

### Validations
- Added offline scheduler validations: `tests/phase7/test_scheduler_pipeline.py`
  - Works with fixtures + mock embeddings (quota-safe).

### Status
- Code is ready; **you still need to run it once in GitHub Actions** to mark Phase 7 gate as PASS.

Evidence: `docs/phase-reports/phase-7-gate.md`

---

## Testing improvements (cross-phase)

- Added/updated targeted tests across Phase 3/4/5/6/7 to prevent regressions:
  - Pinky Promise triggers and refusal correctness
  - Starter prompts behavior (latest + date-list + off-topic)
  - LIST-by-date (valid date returns 3 links; missing date returns fallback)
  - Frontend E2E expectations after UI refactors

---

## Documentation updates

- Architecture refreshed to match real behavior: `docs/architecture.md`
- PRD wording aligned to ChatGPT Glass prototype direction: `docs/problemstatement.md`
- Phase docs updated to match the new UI flows + safety behavior.

---

## Open items / next steps

- **Phase 7 gate**: run GitHub Actions once (`dry_run=true` then `dry_run=false` with `HUGGINGFACE_API_TOKEN`) and fill `phase-7-gate.md` SHA + decision.
- **Phase 8**: end-to-end production integration (GHA → Render → Vercel) — see [deployment-plan.md](./deployment-plan.md).

