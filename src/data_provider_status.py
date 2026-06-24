"""Summarize provider status for Phase 4C diagnostics."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from data_providers.akshare_provider import AKShareProvider  # noqa: E402
from data_providers.baostock_provider import BaoStockProvider  # noqa: E402
from data_providers.jqdata_provider import JQDataProvider  # noqa: E402
from data_providers.local_cache_provider import LocalCacheProvider  # noqa: E402
from data_providers.tushare_provider import TushareProvider  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ETF_DAILY_DIR = DATA_DIR / "etf_daily"
REPORT_DIR = PROJECT_ROOT / "reports"
JSON_REPORT = REPORT_DIR / "data_provider_status.json"
MD_REPORT = REPORT_DIR / "data_provider_status.md"


DAILY_PRIORITY = ["baostock", "tushare_if_configured", "akshare_fallback"]
HISTORY_PRIORITY = ["jqdata", "baostock", "tushare_if_configured"]
SPECIAL_PRIORITY = ["akshare", "tushare", "manual"]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_status()
    JSON_REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_REPORT.write_text(render_md(payload), encoding="utf-8")
    print(f"provider status written: {MD_REPORT}")


def build_status() -> dict[str, Any]:
    providers = {
        "local_cache": LocalCacheProvider(ETF_DAILY_DIR).status(),
        "baostock": BaoStockProvider().status(),
        "tushare": TushareProvider().status(),
        "akshare": AKShareProvider().status(),
        "jqdata": JQDataProvider().status(),
    }
    akshare_probe = _read_json(REPORT_DIR / "akshare_connectivity_check.json")
    tushare_check = _read_json(REPORT_DIR / "tushare_staging_check.json")
    compare = _read_json(REPORT_DIR / "tushare_baostock_compare.json")
    tushare_good = bool(tushare_check.get("sample_symbols_success", 0) >= 4 and compare.get("close_consistent_count", 0) >= 4)
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "baostock_status": _status_payload(providers["baostock"]),
        "tushare_status": _status_payload(providers["tushare"]),
        "akshare_status": {**_status_payload(providers["akshare"]), "connectivity": akshare_probe.get("akshare_status", "not_checked")},
        "jqdata_status": _status_payload(providers["jqdata"]),
        "local_cache_status": {**_status_payload(providers["local_cache"]), "etf_file_count": len(list(ETF_DAILY_DIR.glob("*.csv"))) if ETF_DAILY_DIR.exists() else 0},
        "daily_source_priority": DAILY_PRIORITY,
        "history_source_priority": HISTORY_PRIORITY,
        "special_data_priority": SPECIAL_PRIORITY,
        "daily_source_priority_candidate": ["tushare_if_configured", "baostock", "akshare_fallback"] if tushare_good else DAILY_PRIORITY,
        "formal_source_switched": False,
        "recommended_daily_source": "baostock",
        "candidate_daily_source": "tushare" if tushare_good else "",
        "summary": "Provider status is diagnostics-only; formal daily source remains BaoStock in Phase 4C-1.",
        "safety": {
            "broker_api": False,
            "real_order": False,
            "token_logged": False,
            "formal_data_written": False,
            "execution_layer_changed": False,
        },
    }


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        f"# Data provider 状态 {payload['generated_at']}",
        "",
        "本报告只做 provider 诊断，不切换正式日更主源，不写入 data/etf_daily。",
        "",
        "## 优先级",
        f"- daily_source_priority: {', '.join(payload['daily_source_priority'])}",
        f"- history_source_priority: {', '.join(payload['history_source_priority'])}",
        f"- special_data_priority: {', '.join(payload['special_data_priority'])}",
        f"- daily_source_priority_candidate: {', '.join(payload['daily_source_priority_candidate'])}",
        f"- recommended_daily_source: {payload['recommended_daily_source']}",
        f"- candidate_daily_source: {payload.get('candidate_daily_source') or 'none'}",
        f"- formal_source_switched: {payload['formal_source_switched']}",
        "",
        "## Provider 明细",
        "| provider | configured | usable | message |",
        "| --- | --- | --- | --- |",
    ]
    for key in ["local_cache_status", "baostock_status", "tushare_status", "akshare_status", "jqdata_status"]:
        row = payload[key]
        lines.append(f"| {key.replace('_status','')} | {row.get('configured')} | {row.get('usable')} | {_md(row.get('message'))} |")
    lines.extend(
        [
            "",
            "## 安全边界",
            "- 不打印 token",
            "- 不接券商 API",
            "- 不真实下单",
            "- 不修改执行层",
        ]
    )
    return "\n".join(lines)


def _status_payload(status: Any) -> dict[str, Any]:
    return {
        "configured": bool(status.configured),
        "usable": bool(status.usable),
        "message": status.message,
        "last_error": bool(status.last_error),
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {}


def _md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")[:300]


if __name__ == "__main__":
    main()
