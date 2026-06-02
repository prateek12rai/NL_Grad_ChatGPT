"""Ingest orchestrator — discover, PII filter, download, manifest, prune (§8.5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import httpx

from shared.config import settings
from shared.pii_filter import scan_text
from scraper.adapters.nature import NATURE_SEARCH_URL, NatureAdapter
from scraper.downloader import DocumentDownloader
from scraper.http_client import make_http_client
from scraper.ingest_log import IngestLogger
from scraper.manifest import ManifestStore, make_document_id, new_document_record
from scraper.pruner import prune_manifest
from scraper.adapters.base import BaseAdapter


@dataclass
class IngestResult:
    ingested: int = 0
    skipped_existing: int = 0
    skipped_pii: int = 0
    pruned_ids: list[str] = field(default_factory=list)


class IngestOrchestrator:
    def __init__(
        self,
        manifest_store: ManifestStore | None = None,
        ingest_logger: IngestLogger | None = None,
        downloader: DocumentDownloader | None = None,
        adapters: list[BaseAdapter] | None = None,
        mock_downloads: bool = True,
        repo_root: Path | None = None,
    ) -> None:
        self.manifest_store = manifest_store or ManifestStore()
        self.logger = ingest_logger or IngestLogger()
        self.repo_root = repo_root or Path.cwd()
        self.downloader = downloader or DocumentDownloader(mock_downloads=mock_downloads)
        self.adapters = adapters or []
        self.mock_downloads = mock_downloads
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = make_http_client()
        return self._client

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def run(
        self,
        sources: list[str] | None = None,
        max_per_source: int | None = 10,
        max_total: int | None = None,
    ) -> IngestResult:
        result = IngestResult()
        manifest = self.manifest_store.load()
        known_ids = self.manifest_store.document_ids(manifest)
        if self.mock_downloads:
            client = None
        else:
            client = self._get_client()
            self.downloader.client = client

        selected = self._select_adapters(sources)
        for adapter in selected:
            if max_total is not None and result.ingested >= max_total:
                break
            self._log_source_start(adapter)
            try:
                items = adapter.discover(client)
            except Exception as exc:
                self.logger.append(
                    "discover_error",
                    adapter.source_name,
                    error=str(exc),
                )
                continue

            if max_per_source is not None:
                items = items[:max_per_source]

            for item in items:
                if max_total is not None and result.ingested >= max_total:
                    break
                doc_id = make_document_id(item.source_url, item.document_title)
                if doc_id in known_ids:
                    result.skipped_existing += 1
                    continue

                combined = f"{item.document_title} {item.source_url}"
                pii = scan_text(combined)
                if not pii.is_clean:
                    result.skipped_pii += 1
                    self.logger.append(
                        "pii_rejected",
                        adapter.source_name,
                        document_id=doc_id,
                        violations=list(pii.violations),
                    )
                    continue

                try:
                    path = self.downloader.download(item, doc_id).resolve()
                    size = path.stat().st_size
                    max_bytes = settings.scraper_max_pdf_mb * 1024 * 1024
                    if size > max_bytes:
                        path.unlink(missing_ok=True)
                        self.logger.append(
                            "download_skipped_large",
                            adapter.source_name,
                            document_id=doc_id,
                            bytes=size,
                            max_mb=settings.scraper_max_pdf_mb,
                        )
                        continue
                except Exception as exc:
                    self.logger.append(
                        "download_error",
                        adapter.source_name,
                        document_id=doc_id,
                        error=str(exc),
                    )
                    continue

                rel_path = path.relative_to(self.repo_root.resolve()).as_posix()
                record = new_document_record(item, rel_path)
                manifest = self.manifest_store.upsert(manifest, record)
                known_ids.add(doc_id)
                result.ingested += 1
                self.logger.append(
                    "document_ingested",
                    adapter.source_name,
                    document_id=doc_id,
                    source_url=item.source_url,
                    local_path=rel_path,
                )

        manifest, pruned = prune_manifest(
            manifest,
            corpus_root=Path(self.downloader.corpus_root),
            repo_root=self.repo_root,
        )
        result.pruned_ids = pruned
        if pruned:
            self.logger.append(
                "prune_complete",
                "orchestrator",
                pruned_count=len(pruned),
                pruned_document_ids=pruned,
            )

        self.manifest_store.save(manifest)
        self.logger.append(
            "ingest_run_complete",
            "orchestrator",
            ingested=result.ingested,
            total_documents=len(manifest.documents),
        )
        return result

    def _select_adapters(self, sources: list[str] | None) -> list[BaseAdapter]:
        if self.adapters:
            if not sources:
                return self.adapters
            names = {s.lower() for s in sources}
            return [a for a in self.adapters if a.source_name.lower() in names]

        all_adapters: list[BaseAdapter] = [
            NatureAdapter(
                search_url=settings.nature_search_url or NATURE_SEARCH_URL,
                max_articles=settings.scraper_nature_max_articles,
            ),
        ]
        if not sources:
            return all_adapters
        names = {s.lower() for s in sources}
        return [a for a in all_adapters if a.source_name.lower() in names]

    def _log_source_start(self, adapter: BaseAdapter) -> None:
        url = getattr(adapter, "search_url", None) or getattr(adapter, "base_url", "")
        fields: dict = {"listing_url": url}
        if adapter.source_name == "Nature":
            fields["date_range"] = "last_30_days"
            fields["nature_url"] = getattr(adapter, "search_url", NATURE_SEARCH_URL)
        self.logger.append("discover_start", adapter.source_name, **fields)


def build_fixture_orchestrator(
    nature_html: str,
    data_dir: Path,
    mock_downloads: bool = True,
) -> IngestOrchestrator:
    """Factory for tests with Nature HTML fixture (portfolio ingest is Nature-only)."""
    corpus = data_dir / "corpus"
    manifest_path = data_dir / "manifest.json"
    log_path = data_dir / "ingest_log.jsonl"
    repo_root = data_dir.parent
    return IngestOrchestrator(
        manifest_store=ManifestStore(manifest_path),
        ingest_logger=IngestLogger(log_path),
        downloader=DocumentDownloader(corpus_root=corpus, mock_downloads=mock_downloads),
        adapters=[NatureAdapter(fixture_html=nature_html)],
        mock_downloads=mock_downloads,
        repo_root=repo_root,
    )
