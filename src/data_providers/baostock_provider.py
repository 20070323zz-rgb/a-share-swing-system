"""BaoStock provider prototype.

The existing production path remains scripts/update_etf_data.py. This class is
only the target interface for a future staged provider layer.
"""

from __future__ import annotations

from .base import ProviderResult, ProviderStatus


class BaoStockProvider:
    name = "baostock"

    def status(self) -> ProviderStatus:
        try:
            import baostock  # noqa: F401
        except Exception as exc:
            return ProviderStatus(self.name, configured=False, usable=False, message="baostock import failed", last_error=str(exc))
        return ProviderStatus(self.name, configured=True, usable=True, message="baostock import ok")

    def fetch_daily(self, symbol: str, start: str, end: str) -> ProviderResult:
        return ProviderResult(
            provider=self.name,
            symbol=symbol,
            status="not_wired",
            message="Use scripts/update_etf_data.py until staged provider integration is explicitly enabled.",
        )
