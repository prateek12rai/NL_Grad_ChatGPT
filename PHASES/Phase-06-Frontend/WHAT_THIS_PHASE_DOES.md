# Phase 6 — Doctor Verification Screen (Plain English)



## What this phase is about



We build the **CHATGPT Glass** prototype UI (hosted on **Vercel**):



- **Landing (ChatGPT-style):** heading *ChatGPT Glass*, tagline *(We deliver Real facts only)*, pill search bar, and **three fresh starter prompts** stacked vertically, refreshed on every new chat:
  1. a question about one of our **latest** indexed Nature articles (verifiable),
  2. a **"Show me all research on <date>"** query for a random date just *before* our oldest article — demonstrates the graceful *"we don't have that date → here are our top 3 articles"* fallback,
  3. a randomly chosen funny off-topic demo (triggers the Pinky Promise).
- **Date list answers:** a valid date (e.g. 2026-06-01) returns up to **3 articles with links**; an unavailable date returns *"Sorry, we don't have any articles for that date… try our top 3 articles"* with 3 verifiable citations.
- **Out-of-corpus / Pinky Promise:** the suggestions shown are always **fresh and verifiable** (each maps to a real Nature article you can open and verify).

- **After ask:** conversation view with the AI draft, numbered sources [1], and **You might like** follow-ups

- **Source preview:** click a citation to read a **sanitized excerpt** (Nature share/citation boilerplate removed) under **Review before you verify**

- **Trust nudge:** review the article excerpt, then click **Verify** on each citation

- **Bottom:** **Share** (X, WhatsApp, Facebook, Teams) and **Copy** stay **greyed out** until every source is verified



This implements the core safety rule: **no sharing unverified medical text**.



## What you will see when it is done



- A public Vercel link (preview first, then production)

- End-to-end demo: ask → review excerpt → verify → share/copy unlocks

- No indexed-corpus count lines in the answer area (internal API metadata only)



## Depends on



Phase 5 backend must be online so the website can talk to it.


