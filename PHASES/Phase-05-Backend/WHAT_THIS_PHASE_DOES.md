# Phase 5 — Backend & AI Answers (Plain English)

## What this phase is about

This is the **brain** of the system:

1. You ask a question in everyday language  
2. The system finds the best matching chunks from `chroma_db`  
3. **Groq** (free AI API) writes an answer **only using those chunks** — it must not invent facts  
4. If the question is **not in the indexed corpus**, it returns the exact **Pinky Promise** message and three **clickable suggestions** from verified topics only  
5. It tracks which sources were cited and whether a human has verified them **per question** (each ask gets its own session)  
6. **Copy/export** for that question unlocks only when every **citation used in that answer** is verified — other questions do not block export  

We deploy this part on **Streamlit Cloud** (online backend). A small API layer lets the website on Vercel talk to it later.

## What you will see when it is done

- A working backend you can test with sample questions  
- Gate report PASS  
- Instructions for your Groq API key (free tier)

## What we will NOT do yet

- Full pretty doctor UI (Phase 6)  
- Daily automatic downloads (Phase 7)
