"""JQData provider prototype.

Credentials must come from local environment variables or .env. Data must land
in staging and pass validation/dry-run before formal import.
"""

from __future__ import annotations

import os

from .base import ProviderResult, ProviderStatus


class JQDataProvider:
    name = "jqdata"

    def status(self) -> ProviderStatus:
        configured = bool(os.environ.get("JQDATA_USER") and os.environ.get("JQDATA_PASSWORD"))
        try:
            import jqdatasdk  # noqa: F401
        except Exception as exc:
            return ProviderStatus(self.name, configured=configured, usable=False, message="jqdatasdk import failed", last_error=str(exc))
        return ProviderStatus(self.name, configured=configured, usable=configured, message="jqdatasdk import ok; credential values are never printed")

    def fetch_daily(self, symbol: str, start: str, end: str) -> ProviderResult:
        return ProviderResult(provider=self.name, symbol=symbol, status="not_wired", message="Use src/data_sources/jqdata_source.py staging flow until provider layer is enabled.")
