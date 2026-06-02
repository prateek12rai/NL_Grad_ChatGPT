PRODUCT REQUIREMENT DOCUMENT (PRD)
CHATGPT Glass — Nature-only Medical RAG + Human-in-the-Loop verification

1. Overview & Objective
In the Indian medical research ecosystem, inaccurate clinical guidance or data hallucinations carry severe clinical and legal risks. Medical professionals require a localized search utility that cross-references authoritative frameworks while maintaining complete control over information dissemination.
The objective of this project is to build a lightweight, highly accurate Retrieval-Augmented Generation (RAG) prototype engineered with a strict "Human-in-the-Loop" (HITL) verification guardrail. The system is designed so that no generated medical response can be copied, exported, or shared until a certified professional has manually inspected and verified each cited passage against a locally stored on-disk database.
2. Target Users
•	• Medical Research Professionals reviewing clinical trends and localized epidemiology.
•	• Healthcare Policy Advisors cross-referencing national health data frameworks.
•	• Clinical Consultants verifying disease management guidelines issued by national apex bodies.
3. Scope of Work
3.1. Corpus Definition & Automated Scraping Service (Nature-only)
The data pipeline runs as an automated headless scraper that downloads Nature medical-research HTML into a local repository directory, then chunks and indexes it on disk.

- Corpus constraint (portfolio prototype): **~20 newest Nature articles** only.
- Nature search URL (single allowed source):  
  https://www.nature.com/search?article_type=research&subject=medical-research&date_range=last_30_days&order=relevance
- Sorting policy: newest-first; keep the most recent 20.
- Optional automation: GitHub Actions can run on a schedule, but local runs are supported for development.

3.2. Core Backend Architecture
The backend processes clinical literature using precise semantic chunking strategies to minimize context loss and stores them in a local sqlite-backed vector system.
• Semantic Segmentation (Chunking): Avoids fixed character blocks. Text is parsed based on semantic changes with a hard boundary of 512 tokens and an 80-token overlap to ensure medical contexts (such as drug contraindications) are not split across chunks.
• Vectorization Engine: Text chunks are transformed into high-density vector spaces using the BAAI/bge-large-en-v1.5 transformer model via the serverless Hugging Face Inference API. The pipeline calculates vector spaces using L2 normalization:
    ||v||₂ = √(∑ vᵢ²) = 1
• On-Disk Local Database Integration: Normalized vector arrays are stored locally in the environment via Chroma's PersistentClient. This saves database index states directly to an on-disk folder (e.g., ./chroma_db), avoiding cloud dependencies and external database crash risks. Every vector payload must explicitly follow this schema:
import chromadb

# Initialize local, on-disk storage file-path
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="india_medical_local")

metadata_payload = {
    "source_url": "https://www.icmr.gov.in/pdf/guidelines/tb_protocol_2026.pdf",
    "document_title": "National Operational Guidelines for Pulmonary Tuberculosis - Update",
    "publication_year": 2026,
    "page_number": 24,
    "exact_context": "For multi-drug resistant strains, administer Bedaquiline under strictly monitored DOTS context...",
    "verification_status": "unverified"
}

3.3. Core Frontend UI/UX Functionality (CHATGPT Glass)
The UI is a single-page prototype that mimics a ChatGPT-style landing and conversation flow:

- Landing: title + tagline + glass search input + starter prompts (2 corpus + 1 off-topic from a rotating set).
- Conversation: show **You asked** then the answer; the input clears after response.
- Suggestions-first: show 3 clickable “You might like” options before the answer to reduce ambiguity.
- Citations: numbered `[n]` markers + citation rows with an **Open article** button.
- HITL verification: user opens Nature HTML, reviews, then clicks **Verify** on the citation row.
- Export gate: **Copy answer** and Share (logos-only) remain locked until all cited sources are verified.

4. Operational Constraints & Boundaries
4.1. Privacy and Data Security Restrictions
The system operates under a zero-retention framework for personal information. It is strictly prohibited from collecting, extracting, or storing:
•	• Aadhaar numbers, PAN cards, or any national identity digits.
•	• Patient names, private clinical records, diagnostic files, or history registries.
•	• Authentication hashes, passwords, phone numbers, or email credentials.
4.2. Response & Advisory Constraints
• The system is restricted from providing definitive individual diagnostic choices or direct medical prescriptions.
• The LLM generation layer uses strict system prompt constraints (Groq chat completions) enforcing that it answers using only retrieved context chunks. If the data is missing or out-of-corpus, it must refuse (Pinky Promise) instead of fabricating an answer.
5. Expected Deliverables
1. README Architecture Document: Outlining local environment paths, folder permissions for database initialization, and secret management keys (HUGGINGFACE_API_TOKEN).
2. Optional GitHub Actions workflow: Scheduled ingest (if enabled) that updates local index artifacts.
3. RAG Processing Pipeline Source Code: Extraction → chunking → embeddings → local-disk Chroma upsert for the Nature-only URL.
4. Frontend Interface Application: CHATGPT Glass landing + conversation + verification gate + copy/share lock.
6. Success Criteria
1.	1. Strict Verification Isolation: Total lock on export actions while an unverified citation tag remains in the current thread state.
2.	2. Zero Network Cloud Crashes: Seamless reads and writes handled purely via local disk access without remote vector database handshakes.
3.	3. Out-of-corpus guardrail: Non-medical/off-topic queries trigger the Pinky Promise refusal path.
4.	4. Nature Rolling Sync Execution: Enforced newest-only trimming to ~20 Nature articles from the last 30 days.
