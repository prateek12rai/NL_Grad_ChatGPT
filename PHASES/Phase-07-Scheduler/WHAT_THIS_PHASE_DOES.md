# Phase 7 — Daily Auto-Update (Plain English)

## What this phase is about

We set up **GitHub Actions** — a robot that runs every day at **6:00 AM India time** to:

1. Download new documents (same 3 websites)  
2. Chunk and embed them  
3. Update `chroma_db` and save logs  
4. Commit changes back to GitHub so the online backend can use fresh data  

You do not need to click anything daily; GitHub runs on a schedule.

## What you will see when it is done

- A green checkmark on GitHub Actions after a test run  
- Log file proving Nature still uses “last 7 days”  
- Updated database folder in the repository  
