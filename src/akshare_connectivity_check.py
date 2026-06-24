"""Low-frequency AKShare connectivity diagnostics.

This script is diagnostics-only. It does not write market data to the formal
database, does not connect to broker APIs, and does not place orders.
"""

from __future__ import annotations

import importlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import time
import traceback
from typing import Any, Callable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "reports"
JSON_REPORT = REPORT_DIR / "akshare_connectivity_check.json"
MD_REPORT = REPORT_DIR / "akshare_connectivity_check.md"

REQUEST_TIMEOUT_SECONDS = 25
SLEEP_BETWEEN_TESTS_SECONDS = 1.5


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    result = run_connectivity_check()
    JSON_REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_REPORT.write_text(render_markdown(result), encoding="utf-8")
    print(f"AKShare connectivity status: {result['akshare_status']}")
    print(f"written: {MD_REPORT}")
    print(f"written: {JSON_REPORT}")


def run_connectivity_check() -> dict[str, Any]:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    proxy_vars = [key for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"] if os.environ.get(key)]
    import_result = _check_import()
    tests: list[dict[str, Any]] = []

    if import_result["status"] == "success":
        checks: list[tuple[str, str]] = [
            ("trade_calendar_light", "_call_trade_calendar"),
            ("etf_history_small_range", "_call_etf_history"),
            ("a_share_history_small_range", "_call_a_share_history"),
            ("etf_spot_latest", "_call_etf_spot"),
        ]
        for name, fn_name in checks:
            tests.append(_run_child_test(name, fn_name, REQUEST_TIMEOUT_SECONDS))
            time.sleep(SLEEP_BETWEEN_TESTS_SECONDS)
    else:
        tests.append(
            {
                "name": "akshare_import",
                "status": "failed",
                "rows": 0,
                "elapsed_seconds": 0.0,
                "error_type": import_result.get("error_type", "ImportError"),
                "error": import_result.get("error", "akshare import failed"),
            }
        )

    akshare_status = _classify_status(import_result, tests)
    return {
        "generated_at": generated_at,
        "akshare_status": akshare_status,
        "akshare_version": import_result.get("version", ""),
        "python_executable": os.environ.get("VIRTUAL_ENV", "") or "system/default",
        "proxy_env_present": proxy_vars,
        "tests": tests,
        "likely_causes": _likely_causes(import_result, tests),
        "recommended_role": _recommended_role(akshare_status),
        "safety": {
            "broker_api": False,
            "real_order": False,
            "real_account": False,
            "credentials_logged": False,
            "formal_data_written": False,
            "low_frequency_probe_only": True,
        },
    }


def _check_import() -> dict[str, Any]:
    started = time.time()
    try:
        module = importlib.import_module("akshare")
        return {
            "status": "success",
            "version": str(getattr(module, "__version__", "")),
            "elapsed_seconds": round(time.time() - started, 3),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "version": "",
            "elapsed_seconds": round(time.time() - started, 3),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def _run_child_test(name: str, fn_name: str, timeout: int) -> dict[str, Any]:
    queue: mp.Queue = mp.Queue()
    proc = mp.Process(target=_child_entry, args=(fn_name, queue))
    started = time.time()
    proc.start()
    proc.join(timeout)
    elapsed = round(time.time() - started, 3)
    if proc.is_alive():
        proc.terminate()
        proc.join(5)
        return {
            "name": name,
            "status": "timeout",
            "rows": 0,
            "elapsed_seconds": elapsed,
            "error_type": "TimeoutError",
            "error": f"AKShare call exceeded {timeout}s",
        }
    try:
        payload = queue.get_nowait()
    except Exception:
        payload = {
            "status": "failed",
            "rows": 0,
            "error_type": "NoResult",
            "error": "child process returned no result",
        }
    payload["name"] = name
    payload["elapsed_seconds"] = elapsed
    return payload


def _child_entry(fn_name: str, queue: mp.Queue) -> None:
    try:
        fn_map: dict[str, Callable[[], pd.DataFrame]] = {
            "_call_trade_calendar": _call_trade_calendar,
            "_call_etf_history": _call_etf_history,
            "_call_a_share_history": _call_a_share_history,
            "_call_etf_spot": _call_etf_spot,
        }
        df = fn_map[fn_name]()
        queue.put(
            {
                "status": "success",
                "rows": int(len(df)) if hasattr(df, "__len__") else 0,
                "columns": list(df.columns[:12]) if hasattr(df, "columns") else [],
                "error_type": "",
                "error": "",
            }
        )
    except Exception as exc:
        queue.put(
            {
                "status": "failed",
                "rows": 0,
                "columns": [],
                "error_type": type(exc).__name__,
                "error": str(exc),
                "trace_tail": traceback.format_exc(limit=2).strip().splitlines()[-3:],
            }
        )


def _call_trade_calendar() -> pd.DataFrame:
    import akshare as ak

    return ak.tool_trade_date_hist_sina()


def _call_etf_history() -> pd.DataFrame:
    import akshare as ak

    return ak.fund_etf_hist_em(symbol="510300", period="daily", start_date="20260601", end_date="20260618", adjust="")


def _call_a_share_history() -> pd.DataFrame:
    import akshare as ak

    return ak.stock_zh_a_hist(symbol="600519", period="daily", start_date="20260601", end_date="20260618", adjust="")


def _call_etf_spot() -> pd.DataFrame:
    import akshare as ak

    return ak.fund_etf_spot_em()


def _classify_status(import_result: dict[str, Any], tests: list[dict[str, Any]]) -> str:
    if import_result.get("status") != "success":
        return "unavailable"
    if not tests:
        return "unavailable"
    success = sum(1 for row in tests if row.get("status") == "success")
    timeout_or_network = sum(1 for row in tests if row.get("status") in {"timeout", "failed"} and _is_network_like(row))
    if success == len(tests):
        return "usable"
    if success >= 2 and timeout_or_network:
        return "partially_usable"
    if success >= 1:
        return "unstable"
    return "unavailable"


def _is_network_like(row: dict[str, Any]) -> bool:
    text = f"{row.get('error_type', '')} {row.get('error', '')}".lower()
    needles = ["connection", "timeout", "remote", "proxy", "ssl", "read timed", "max retries"]
    return any(needle in text for needle in needles)


def _likely_causes(import_result: dict[str, Any], tests: list[dict[str, Any]]) -> list[str]:
    causes: list[str] = []
    if import_result.get("status") != "success":
        causes.append("akshare is not installed or cannot be imported in the active Python environment.")
    errors = " ".join(f"{row.get('error_type', '')} {row.get('error', '')}" for row in tests).lower()
    if "proxy" in errors:
        causes.append("proxy configuration may be interfering with Eastmoney/Sina endpoints.")
    if "remote" in errors or "connection" in errors:
        causes.append("remote endpoints may close connections or rate-limit requests from the current network.")
    if "timeout" in errors:
        causes.append("endpoint latency is high; long batch jobs should avoid AKShare as the primary daily source.")
    if not causes:
        causes.append("no major connectivity issue was detected in this low-frequency probe.")
    return causes


def _recommended_role(status: str) -> str:
    if status == "usable":
        return "Use AKShare as low-frequency supplemental source for public market/news/special data; keep formal ETF daily updates on the existing validated path until provider abstraction is fully tested."
    if status == "partially_usable":
        return "Use AKShare only as an optional fallback and intelligence-data probe with retry/backoff and local cache; do not use it as primary daily ETF update source."
    if status == "unstable":
        return "Use AKShare for manual diagnostics only; avoid automated daily ETF updates until repeated probes are stable."
    return "Do not rely on AKShare in automation; keep BaoStock/local cache/manual/JQData historical staging paths."


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# AKShare 可用性诊断 {result['generated_at']}",
        "",
        "本报告仅做低频连通性诊断，不写入 data/etf_daily，不接券商 API，不真实下单。",
        "",
        "## 结论",
        f"- akshare_status: {result['akshare_status']}",
        f"- akshare_version: {result.get('akshare_version') or 'N/A'}",
        f"- proxy_env_present: {', '.join(result.get('proxy_env_present') or []) or 'none'}",
        f"- 推荐角色：{result['recommended_role']}",
        "",
        "## 接口探测",
        "| test | status | rows | elapsed_seconds | error_type | error |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in result.get("tests", []):
        lines.append(
            "| {name} | {status} | {rows} | {elapsed_seconds} | {error_type} | {error} |".format(
                name=_md(row.get("name", "")),
                status=_md(row.get("status", "")),
                rows=row.get("rows", 0),
                elapsed_seconds=row.get("elapsed_seconds", 0),
                error_type=_md(row.get("error_type", "")),
                error=_md(str(row.get("error", ""))[:180]),
            )
        )
    lines.extend(
        [
            "",
            "## 可能原因",
        ]
    )
    for item in result.get("likely_causes", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 安全边界",
            "- 不接券商 API",
            "- 不真实下单",
            "- 不读取真实账户",
            "- 不保存或打印任何账号密码/token",
            "- 不写入正式行情目录",
        ]
    )
    return "\n".join(lines)


def _md(value: Any) -> str:
    return str(value).replace("|", "/").replace("\n", " ")


if __name__ == "__main__":
    main()
