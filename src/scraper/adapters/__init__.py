"""Source-specific scraper adapters."""

from scraper.adapters.dhr import DHRAdapter, DHR_BASE_URL
from scraper.adapters.icmr import ICMRAdapter, ICMR_REPORTS_URL
from scraper.adapters.nature import NATURE_SEARCH_URL, NatureAdapter

__all__ = [
    "DHRAdapter",
    "DHR_BASE_URL",
    "ICMRAdapter",
    "ICMR_REPORTS_URL",
    "NatureAdapter",
    "NATURE_SEARCH_URL",
]
