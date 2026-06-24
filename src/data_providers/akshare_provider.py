"""AKShare provider prototype.

AKShare is suitable for low-frequency fallback/intelligence data only until
connectivity proves stable under repeated diagnostics.
"""

from __future__ import annotations

from .base import ProviderResult, ProviderStatus


class AKShareProvider:
    name = "akshare"

    def status(self) -> ProviderStatus:
        try:
            import akshare  # noqa: F401
        except Exception as exc:
            return ProviderStatus(self.name, configured=False, usable=False, message="akshare import failed", last_error=str(exc))
        return ProviderStatus(self.name, configured=True, usable=True, message="akshare import ok; run akshare_connectivity_check for endpoint health")

    def fetch_daily(self, symbol: str, start: str, end: str) -> ProviderResult:
        return ProviderResult(provider=self.name, symbol=symbol, status="not_wired", message="AKShare daily fetch remains fallback/design-only in Phase 4C.")
