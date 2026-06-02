# Real ingest — Nature only (last 30 days)

**Single portfolio URL** (only source):

https://www.nature.com/search?article_type=research&subject=medical-research&date_range=last_30_days&order=relevance

ICMR and DHR PDF ingest paths are **removed** from the default scheduler. The scraper paginates search results and downloads full article HTML.

## Full rebuild (20 newest articles)

```powershell
$env:PYTHONPATH = "src"
python scripts/build_real_prototype.py --fresh --max-total 20
```

Trim an oversized corpus without re-scraping:

```powershell
python scripts/trim_corpus.py --keep 20
```

## Ingest only

```powershell
python -m scraper.scheduler --max-total 20
```
