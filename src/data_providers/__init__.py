"""Provider abstraction prototypes for market-data research.

These classes are not wired into the execution layer yet. They document the
target interface for future staged data ingestion.
"""

from .base import DailyBarSchema, DataProvider, ProviderResult, ProviderStatus
from .local_cache_provider import LocalCacheProvider

__all__ = [
    "DailyBarSchema",
    "DataProvider",
    "ProviderResult",
    "ProviderStatus",
    "LocalCacheProvider",
]
