"""Tushare provider for small-sample staging diagnostics.

Token handling must stay in environment variables or .env; tokens must never be
printed to logs or reports. This provider writes no formal data by itself.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
import json
import urllib.request

import pandas as pd

from .base import DAILY_BAR_COLUMNS, ProviderResult, ProviderStatus, normalize_daily_bar_schema


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOKEN_ENV_NAME = "TUSHARE_TOKEN"
STAGING_COLUMNS = DAILY_BAR_COLUMNS + ["symbol", "name", "available_date_rule", "available_date_estimated"]


class TushareProvider:
    name = "tushare"

    def __init__(self, token: str | None = None):
        self._token = token or _load_token()

    def status(self) -> ProviderStatus:
        token_configured = bool(self._token)
        try:
            import tushare  # noqa: F401
        except Exception as exc:
            if token_configured:
                return ProviderStatus(
                    self.name,
                    configured=True,
                    usable=True,
                    message="tushare package missing; HTTP API fallback will be used",
                    last_error=_sanitize(str(exc)),
                )
            return ProviderStatus(self.name, configured=False, usable=False, message="tushare import failed and token missing", last_error=_sanitize(str(exc)))
        return ProviderStatus(self.name, configured=token_configured, usable=token_configured, message="tushare import ok; token presence only reported")

    def fetch_daily(self, symbol: str, start: str, end: str, name: str = "") -> ProviderResult:
        status = self.status()
        if not status.configured:
            return ProviderResult(provider=self.name, symbol=symbol, status="skipped_no_token", message="Tushare token is not configured.", source_status=status)
        if not status.usable:
            return ProviderResult(provider=self.name, symbol=symbol, status="failed_provider_unusable", message=status.message, source_status=status)
        try:
            ts_code = to_ts_code(symbol)
            raw = self._fetch_fund_daily(ts_code, start, end)
            if raw is None or raw.empty:
                return ProviderResult(provider=self.name, symbol=symbol, status="no_data", message=f"no rows returned for {ts_code}", source_status=status)
            normalized = self._normalize_fund_daily(raw, symbol=symbol, name=name)
            return ProviderResult(
                provider=self.name,
                symbol=symbol,
                status="success",
                data=normalized,
                message=f"fetched {len(normalized)} rows for {ts_code}",
                source_status=status,
                metadata={"ts_code": ts_code, "available_date_estimated": True},
            )
        except Exception as exc:
            return ProviderResult(
                provider=self.name,
                symbol=symbol,
                status="failed",
                message=_sanitize(str(exc)),
                source_status=status,
                metadata={"error_type": type(exc).__name__},
            )

    def _fetch_fund_daily(self, ts_code: str, start: str, end: str) -> pd.DataFrame:
        try:
            import tushare as ts

            pro = ts.pro_api(self._token)
            return pro.fund_daily(ts_code=ts_code, start_date=_compact_date(start), end_date=_compact_date(end))
        except ImportError:
            return _fetch_fund_daily_http(self._token, ts_code, start, end)

    def _normalize_fund_daily(self, raw: pd.DataFrame, symbol: str, name: str = "") -> pd.DataFrame:
        df = raw.copy()
        rename = {
            "trade_date": "date",
            "vol": "volume",
            "amount": "amount",
        }
        df = df.rename(columns={col: rename.get(str(col), col) for col in df.columns})
        fetch_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        normalized = normalize_daily_bar_schema(df, self.name, fetch_time)
        if normalized.empty:
            return pd.DataFrame(columns=STAGING_COLUMNS)
        dates = pd.to_datetime(normalized["date"], errors="coerce")
        normalized["available_date"] = (dates + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")
        normalized["symbol"] = normalize_symbol(symbol)
        normalized["name"] = name or normalize_symbol(symbol)
        normalized["available_date_rule"] = "estimated_t_plus_1_calendar_day"
        normalized["available_date_estimated"] = True
        return normalized[STAGING_COLUMNS].sort_values("date").reset_index(drop=True)


def _load_token() -> str:
    token = os.environ.get(TOKEN_ENV_NAME, "").strip()
    if token:
        return token
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return ""
    try:
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            if key.startswith("export "):
                key = key.split(None, 1)[1].strip()
            if key == TOKEN_ENV_NAME:
                return value.strip().strip('"').strip("'")
    except Exception:
        return ""
    return ""


def normalize_symbol(symbol: str) -> str:
    digits = "".join(ch for ch in str(symbol) if ch.isdigit())
    return digits[-6:] if len(digits) >= 6 else str(symbol).strip()


def to_ts_code(symbol: str) -> str:
    text = str(symbol).strip().upper()
    digits = normalize_symbol(text)
    if text.endswith(".SH") or text.endswith(".SZ"):
        return f"{digits}.{text[-2:]}"
    if digits.startswith(("5", "6")):
        return f"{digits}.SH"
    if digits.startswith(("0", "1", "3")):
        return f"{digits}.SZ"
    return f"{digits}.SH"


def _compact_date(value: str) -> str:
    return str(value).replace("-", "")[:8]


def _fetch_fund_daily_http(token: str, ts_code: str, start: str, end: str) -> pd.DataFrame:
    payload = {
        "api_name": "fund_daily",
        "token": token,
        "params": {
            "ts_code": ts_code,
            "start_date": _compact_date(start),
            "end_date": _compact_date(end),
        },
        "fields": "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount",
    }
    request = urllib.request.Request(
        "http://api.tushare.pro",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        body = response.read().decode("utf-8", errors="replace")
    data = json.loads(body)
    if int(data.get("code", -1)) != 0:
        raise RuntimeError(f"Tushare API error code={data.get('code')} msg={data.get('msg', '')}")
    table = data.get("data") or {}
    fields = table.get("fields") or []
    items = table.get("items") or []
    return pd.DataFrame(items, columns=fields)


def _sanitize(message: Any) -> str:
    text = str(message)
    token = _load_token()
    if token:
        text = text.replace(token, "***")
    return text[:500]
