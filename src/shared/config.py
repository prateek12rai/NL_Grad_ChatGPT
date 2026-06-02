"""Application settings from environment variables."""

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _read_dotenv_bool(key: str) -> bool | None:
    """Read a boolean flag from repo ``.env`` (used when OS env overrides the file)."""
    for candidate in (Path.cwd() / ".env", _REPO_ROOT / ".env"):
        if not candidate.is_file():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            name, _, value = stripped.partition("=")
            if name.strip() != key:
                continue
            val = value.strip().strip('"').strip("'").lower()
            return val in ("true", "1", "yes", "on")
    return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = ""
    groq_mock: bool = False
    groq_model_primary: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    groq_model_fallback: str = "llama-3.1-8b-instant"
    groq_max_tokens: int = 2048
    groq_temperature: float = 0.1
    rag_top_k: int = 8
    rag_context_chunks: int = 3
    rag_max_citations: int = 1
    rag_max_per_document: int = 1
    # LIST-by-date answers return up to this many distinct articles (with links)
    rag_list_max_documents: int = 3
    # Live Nature.com scrape during count queries (adds latency; off by default)
    rag_nature_live_count: bool = False
    # Min cosine similarity (1 - distance) to include a vector hit in LLM context
    rag_min_similarity: float = 0.18
    rag_temperature: float = 0.35
    # Max Chroma cosine distance to treat a hit as in-corpus (lower = stricter)
    rag_max_distance: float = 0.78
    # Below this top-hit similarity or term overlap → pinky promise (out of corpus)
    rag_ooc_min_similarity: float = 0.22
    rag_ooc_min_term_overlap: float = 0.08
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    huggingface_api_token: str = ""
    embed_model_id: str = "BAAI/bge-large-en-v1.5"
    embed_batch_size: int = 16
    embed_mock: bool = False
    embed_max_chars_per_request: int = 24000
    bge_dimension: int = 1024
    chroma_path: str = "./chroma_db"
    chroma_collection_name: str = "india_medical_local"
    corpus_path: str = "./data/corpus"
    chunk_output_dir: str = "./data/chunks"
    chunk_index_path: str = "./data/chunks/index.json"
    max_documents: int = 20
    # Live scrape limits — small Nature-only prototype (newest-first, cap 20)
    scraper_max_per_source: int = 20
    scraper_max_total: int = 20
    scraper_max_pdf_mb: int = 12
    nature_search_url: str = (
        "https://www.nature.com/search?"
        "article_type=research&subject=medical-research&date_range=last_30_days&order=relevance"
    )
    scraper_nature_max_pages: int = 2
    scraper_nature_max_articles: int = 20
    scraper_request_delay_seconds: float = 1.0

    @property
    def chroma_path_resolved(self) -> Path:
        return Path(self.chroma_path).resolve()

    @property
    def groq_live(self) -> bool:
        """Live Groq when a real API key is set and mock mode is off."""
        return bool(self.groq_api_key.strip()) and not self.groq_mock

    @model_validator(mode="after")
    def dotenv_overrides_process_env(self) -> "Settings":
        """
        Windows/shell often sets GROQ_MOCK=true while ``.env`` says false.

        For mock flags, the repo ``.env`` file wins so local dev matches the file.
        """
        groq = _read_dotenv_bool("GROQ_MOCK")
        if groq is not None:
            object.__setattr__(self, "groq_mock", groq)
        embed = _read_dotenv_bool("EMBED_MOCK")
        if embed is not None:
            object.__setattr__(self, "embed_mock", embed)
        return self


settings = Settings()
