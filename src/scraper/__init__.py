"""Phase 2 — web scrapers for DHR, ICMR, Nature."""

from scraper.orchestrator import IngestOrchestrator, IngestResult
from scraper.scheduler import main as run_scheduler

__all__ = ["IngestOrchestrator", "IngestResult", "run_scheduler"]
