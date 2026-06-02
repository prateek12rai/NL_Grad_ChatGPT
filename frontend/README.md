# Frontend (Vercel) — CHATGPT Glass prototype

Single-page **Human-in-the-Loop** UI (Phase 6): landing + conversation, citations with verify nudge, and copy/share locked until cited sources are verified.

## Prerequisites

1. **Phase 5 API** running locally (or deployed):
   ```powershell
   cd C:\path\to\NL_Grad_ChatGPT
   $env:PYTHONPATH = "src"
   python -m uvicorn api.main:app --reload --port 8000
   ```
2. **Chroma indexed** (Phases 2–4 done once): `chroma_db/` with vectors.
3. **`.env`**: `GROQ_API_KEY`, `GROQ_MOCK=false` for live answers.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_BACKEND_URL` | Yes (prod) | FastAPI base URL (e.g. `https://your-api.example.com`) |
| `NEXT_PUBLIC_BACKEND_URL` | Optional | Alias for Vite/Next |

Local default: `http://localhost:8000`

## Commands

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # dist/ for Vercel
npm run test:e2e # Playwright (mocks API; starts dev server)
```

## Deploy to Vercel

1. Import repo; set **Root Directory** to `frontend`.
2. Framework: **Vite**.
3. Add `VITE_BACKEND_URL` → your Streamlit/FastAPI public URL.
4. Ensure backend `CORS_ORIGINS` includes your Vercel preview/production URL.

## User flow

1. Type a question → **Ask**
2. Use **You might like** suggestions or ask a follow-up
3. Click **Open article** → review Nature page → click **Verify**
4. When export gate opens → **Copy answer** (Share shows logos only in prototype)

Out-of-corpus questions show the Pinky Promise message and clickable verified-topic suggestions.
