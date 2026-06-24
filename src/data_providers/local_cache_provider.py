"""Local CSV cache provider prototype."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base import ProviderResult, ProviderStatus, existing_local_path, normalize_daily_bar_schema


class LocalCacheProvider:
    name = "local_cache"

    def __init__(self, etf_daily_dir: Path):
        self.etf_daily_dir = Path(etf_daily_dir)

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            configured=self.etf_daily_dir.exists(),
            usable=self.etf_daily_dir.exists(),
            message=f"local cache dir: {self.etf_daily_dir}",
        )

    def fetch_daily(self, symbol: str, start: str, end: str) -> ProviderResult:
        path = existing_local_path(self.etf_daily_dir, symbol)
        if path is None:
            return ProviderResult(provider=self.name, symbol=symbol, status="missing", message="local csv not found")
        df = pd.read_csv(path)
        out = normalize_daily_bar_schema(df, self.name, pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
        if not out.empty:
            out = out[(out["date"] >= start) & (out["date"] <= end)].copy()
        return ProviderResult(provider=self.name, symbol=symbol, status="success", data=out, message=str(path))
