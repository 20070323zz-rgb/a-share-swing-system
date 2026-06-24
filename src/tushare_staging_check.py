"""Phase 4C-1 Tushare small-sample staging dry-run.

This script only writes data/staging/tushare and reports/. It never overwrites
data/etf_daily, never touches paper trading files, and never changes execution.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time
from typing import Any

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from data_providers.tushare_provider import STAGING_COLUMNS, TushareProvider  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ETF_DAILY_DIR = DATA_DIR / "etf_daily"
STAGING_DIR = DATA_DIR / "staging" / "tushare"
REPORT_DIR = PROJECT_ROOT / "reports"

STAGING_CSV = STAGING_DIR / "tushare_etf_daily_sample.csv"
CONFIG_JSON = REPORT_DIR / "tushare_config_check.json"
CONFIG_MD = REPORT_DIR / "tushare_config_check.md"
CHECK_JSON = REPORT_DIR / "tushare_staging_check.json"
CHECK_MD = REPORT_DIR / "tushare_staging_check.md"
NO_LOOKAHEAD_MD = REPORT_DIR / "tushare_no_lookahead_check.md"

PREFERRED_SAMPLES = [
    ("510300", "沪深300ETF"),
    ("159915", "创业板ETF"),
    ("512880", "证券ETF"),
    ("518880", "黄金ETF"),
    ("515790", "光伏ETF"),
]


def main() -> None:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    result = run_check()
    write_reports(result)
    print(f"Tushare staging status: {result['status']}")
    print(f"sample success: {result['sample_symbols_success']}, failed: {result['sample_symbols_failed']}")
    print(f"written: {CHECK_MD}")


def run_check() -> dict[str, Any]:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    provider = TushareProvider()
    status = provider.status()
    token_diag = token_diagnostics()
    config = {
        "generated_at": generated_at,
        "tushare_token_configured": bool(status.configured),
        "token_visible_in_logs": False,
        **token_diag,
        "provider_ready": bool(status.usable),
        "provider_message": status.message,
        "next_action": "Run small-sample staging dry-run." if status.usable else "Configure TUSHARE_TOKEN in local environment or .env, then rerun staging check.",
    }
    if not status.configured or not status.usable:
        empty = pd.DataFrame(columns=STAGING_COLUMNS)
        empty.to_csv(STAGING_CSV, index=False)
        return {
            "generated_at": generated_at,
            "status": "skipped_no_token" if not status.configured else "skipped_provider_unusable",
            **config,
            "staging_csv": str(STAGING_CSV.relative_to(PROJECT_ROOT)),
            "sample_symbols": [],
            "sample_symbols_tested": 0,
            "sample_symbols_success": 0,
            "sample_symbols_failed": 0,
            "rows_written": 0,
            "results": [],
            "field_schema_ok": False,
            "recommended_next_step": config["next_action"],
            "safety": _safety(),
        }

    samples = choose_samples()
    start, end, date_count = recent_local_date_range(samples)
    rows: list[pd.DataFrame] = []
    results: list[dict[str, Any]] = []
    for symbol, name in samples:
        item = provider.fetch_daily(symbol, start=start, end=end, name=name)
        data = item.data.copy()
        if item.status == "success" and not data.empty:
            rows.append(data)
        results.append(
            {
                "symbol": symbol,
                "name": name,
                "status": item.status,
                "rows": int(len(data)),
                "start": str(data["date"].min()) if not data.empty and "date" in data.columns else "",
                "end": str(data["date"].max()) if not data.empty and "date" in data.columns else "",
                "failure_reason": item.message if item.status != "success" else "",
                "error_type": item.metadata.get("error_type", ""),
            }
        )
        time.sleep(1.2)

    combined = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=STAGING_COLUMNS)
    combined.to_csv(STAGING_CSV, index=False)
    success_count = sum(1 for row in results if row["status"] == "success" and row["rows"] > 0)
    failure_count = len(results) - success_count
    field_schema_ok = set(STAGING_COLUMNS).issubset(set(combined.columns))
    return {
        "generated_at": generated_at,
        "status": "completed",
        **config,
        "staging_csv": str(STAGING_CSV.relative_to(PROJECT_ROOT)),
        "sample_symbols": [symbol for symbol, _ in samples],
        "sample_symbols_tested": len(samples),
        "sample_symbols_success": success_count,
        "sample_symbols_failed": failure_count,
        "rows_written": int(len(combined)),
        "date_range": {"start": start, "end": end, "local_trading_days": date_count},
        "results": results,
        "field_schema_ok": field_schema_ok,
        "available_date_estimated": bool((combined.get("available_date_estimated", pd.Series(dtype=bool)).astype(str) == "True").any()) if not combined.empty else True,
        "recommended_next_step": _recommend_next_step(success_count, failure_count),
        "safety": _safety(),
    }


def choose_samples() -> list[tuple[str, str]]:
    pool = _read_csv(DATA_DIR / "backtest_trade_pool.csv")
    available = {path.stem[-6:] for path in ETF_DAILY_DIR.glob("*.csv")}
    samples: list[tuple[str, str]] = []
    for symbol, name in PREFERRED_SAMPLES:
        if symbol in available:
            samples.append((symbol, name))
    if len(samples) >= 5:
        return samples[:5]
    if not pool.empty:
        for _, row in pool.iterrows():
            symbol = str(row.get("symbol", "")).strip()[:6]
            if symbol and symbol in available and symbol not in {item[0] for item in samples}:
                samples.append((symbol, str(row.get("name", symbol))))
            if len(samples) >= 5:
                break
    return samples[:5]


def recent_local_date_range(samples: list[tuple[str, str]]) -> tuple[str, str, int]:
    dates: list[pd.Timestamp] = []
    for symbol, _ in samples:
        path = _local_path(symbol)
        if path is None:
            continue
        try:
            df = pd.read_csv(path, usecols=["date"])
            dates.extend(pd.to_datetime(df["date"], errors="coerce").dropna().tolist())
        except Exception:
            continue
    if not dates:
        end = pd.Timestamp.today().normalize()
        start = end - pd.Timedelta(days=45)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), 0
    unique = sorted(set(pd.Timestamp(d).normalize() for d in dates))
    tail = unique[-30:] if len(unique) >= 30 else unique
    return tail[0].strftime("%Y-%m-%d"), tail[-1].strftime("%Y-%m-%d"), len(tail)


def write_reports(result: dict[str, Any]) -> None:
    config = {
        "generated_at": result["generated_at"],
        "tushare_token_configured": result["tushare_token_configured"],
        "token_visible_in_logs": False,
        "env_file_exists": bool(result.get("env_file_exists", False)),
        "env_var_present": bool(result.get("env_var_present", False)),
        "env_file_has_tushare_token_key": bool(result.get("env_file_has_tushare_token_key", False)),
        "provider_ready": result["provider_ready"],
        "next_action": "Run small-sample staging dry-run." if result["provider_ready"] else "Configure TUSHARE_TOKEN locally and rerun.",
    }
    CONFIG_JSON.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    CHECK_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    CONFIG_MD.write_text(render_config_md(config), encoding="utf-8")
    CHECK_MD.write_text(render_check_md(result), encoding="utf-8")
    NO_LOOKAHEAD_MD.write_text(render_no_lookahead_md(result), encoding="utf-8")


def render_config_md(config: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# Tushare 配置检查 {config['generated_at']}",
            "",
            "本报告只显示 token 是否存在，不显示 token 原文。",
            "",
            f"- tushare_token_configured: {config['tushare_token_configured']}",
            f"- token_visible_in_logs: {config['token_visible_in_logs']}",
            f"- env_file_exists: {config.get('env_file_exists', False)}",
            f"- env_var_present: {config.get('env_var_present', False)}",
            f"- env_file_has_tushare_token_key: {config.get('env_file_has_tushare_token_key', False)}",
            f"- provider_ready: {config['provider_ready']}",
            f"- next_action: {config['next_action']}",
            "",
            "安全边界：不接券商 API，不真实下单，不保存或打印 token。",
        ]
    )


def token_diagnostics() -> dict[str, bool]:
    env_path = PROJECT_ROOT / ".env"
    key_present = False
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key = stripped.split("=", 1)[0].strip()
                if key.startswith("export "):
                    key = key.split(None, 1)[1].strip()
                if key == "TUSHARE_TOKEN":
                    key_present = True
                    break
        except Exception:
            key_present = False
    return {
        "env_file_exists": env_path.exists(),
        "env_var_present": bool(os.environ.get("TUSHARE_TOKEN")),
        "env_file_has_tushare_token_key": key_present,
    }


def render_check_md(result: dict[str, Any]) -> str:
    lines = [
        f"# Tushare staging dry-run {result['generated_at']}",
        "",
        "本报告只检查 Tushare 小样本 staging，不覆盖 data/etf_daily，不接执行层。",
        "",
        "## 摘要",
        f"- status: {result['status']}",
        f"- tushare_token_configured: {result['tushare_token_configured']}",
        f"- provider_ready: {result['provider_ready']}",
        f"- tested: {result['sample_symbols_tested']}",
        f"- success: {result['sample_symbols_success']}",
        f"- failed: {result['sample_symbols_failed']}",
        f"- rows_written: {result['rows_written']}",
        f"- staging_csv: {result['staging_csv']}",
        f"- recommended_next_step: {result['recommended_next_step']}",
        "",
        "## 明细",
        "| symbol | name | status | rows | start | end | failure_reason |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in result.get("results", []):
        lines.append(
            f"| {_md(row.get('symbol'))} | {_md(row.get('name'))} | {_md(row.get('status'))} | {row.get('rows', 0)} | {_md(row.get('start'))} | {_md(row.get('end'))} | {_md(row.get('failure_reason'))} |"
        )
    lines.extend(
        [
            "",
            "## 质量判断",
            f"- ETF 日线接口可用：{result['sample_symbols_success'] > 0}",
            f"- 字段 schema 完整：{result.get('field_schema_ok', False)}",
            "- available_date 当前按 T+1 自然日估算，尚不可直接进入 alpha。",
            "- 本轮不扩大到 183 只，不切换正式主源。",
            "",
            "## 安全边界",
            "- 不覆盖正式数据",
            "- 不接 BUY ranking / paper_trade_engine / 正式回测",
            "- 不打印 token",
        ]
    )
    return "\n".join(lines)


def render_no_lookahead_md(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# Tushare no-lookahead 检查 {result['generated_at']}",
            "",
            "- Tushare staging 数据包含 `available_date` 字段。",
            "- 当前 `available_date` 规则为 `estimated_t_plus_1_calendar_day`，属于估算，不是真实确认的可得时间。",
            "- 因此 Tushare staging 数据当前不能进入正式 alpha、BUY ranking、paper_trade_engine 或正式回测。",
            "- T 日数据只能在 T+1 或以后使用；若后续接入研究因子，必须先确认真实可得时间。",
            "- 本轮数据只写入 `data/staging/tushare/`，不覆盖 `data/etf_daily/`。",
            "",
            f"- staging_status: {result['status']}",
            f"- rows_written: {result['rows_written']}",
            f"- available_date_estimated: {result.get('available_date_estimated', True)}",
        ]
    )


def _recommend_next_step(success_count: int, failure_count: int) -> str:
    if success_count >= 4 and failure_count == 0:
        return "Tushare small sample looks good; next step can expand staging to 20-30 ETFs, still no formal overwrite."
    if success_count > 0:
        return "Tushare is partially usable; inspect failures and compare with BaoStock before any larger staging."
    return "Tushare staging is not usable yet; keep BaoStock as daily source and check token/permission/import issues."


def _local_path(symbol: str) -> Path | None:
    for prefix in ["sh", "sz"]:
        path = ETF_DAILY_DIR / f"{prefix}_{symbol}.csv"
        if path.exists():
            return path
    matches = sorted(ETF_DAILY_DIR.glob(f"*{symbol}*.csv"))
    return matches[0] if matches else None


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame()


def _safety() -> dict[str, bool]:
    return {
        "broker_api": False,
        "real_order": False,
        "real_account": False,
        "token_logged": False,
        "formal_data_written": False,
        "paper_trades_modified": False,
        "paper_positions_modified": False,
        "paper_trade_engine_modified": False,
    }


def _md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")[:300]


if __name__ == "__main__":
    main()
