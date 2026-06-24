"""用 BaoStock 在用户本机下载 ETF 日线数据。

本脚本只下载公开行情并写入本地 CSV，不连接券商 API，不下单，
不读取账号、密码、验证码或任何交易账户信息。
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date
import json
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DATA_DOWNLOAD_REPORT_FILE, DATA_UPDATE_LOG_FILE, ETF_DAILY_DIR, REPORT_DIR, WATCHLIST_FILE  # noqa: E402
from data_loader import baostock_code, read_watchlist  # noqa: E402


BAOSTOCK_FIELDS = [
    "date",
    "code",
    "open",
    "high",
    "low",
    "close",
    "preclose",
    "volume",
    "amount",
    "adjustflag",
    "turn",
    "tradestatus",
    "pctChg",
    "isST",
]

DATA_UPDATE_STATUS_FILE = REPORT_DIR / "data_update_status.json"
DATA_UPDATE_DIAGNOSIS_FILE = REPORT_DIR / "data_update_diagnosis_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="本机 BaoStock ETF 日线下载脚本")
    parser.add_argument("--start", default="2018-01-01", help="没有本地 CSV 时的默认起始日期，默认 2018-01-01。")
    parser.add_argument("--end", default=date.today().strftime("%Y-%m-%d"), help="结束日期，默认今天。")
    parser.add_argument("--symbols", nargs="*", help="只下载指定代码，可空格或逗号分隔，例如 510300 159915。")
    parser.add_argument("--all-etf", action="store_true", help="更新正式 data/etf_daily/ 中全部 ETF CSV，并合并 watchlist/candidate imported ETF。")
    parser.add_argument("--source", default="auto", choices=["auto", "jqdata", "baostock", "tushare"], help="数据源；auto 优先 JQData，失败 fallback BaoStock。")
    parser.add_argument("--primary", default="baostock", choices=["baostock", "jqdata"], help="auto 模式主源，默认 baostock；JQData 保留为手动/研究源。")
    parser.add_argument("--fallback", default="baostock", help="auto 模式 fallback 数据源，默认 baostock。")
    parser.add_argument("--staging", action="store_true", help="保留 staging-first 语义；JQData 总是先写 staging。")
    parser.add_argument("--validate-only", action="store_true", help="只下载到 staging 并验证，不导入正式 data/etf_daily。")
    parser.add_argument("--no-fallback", action="store_true", help="source=auto 时禁用 fallback。")
    parser.add_argument("--dry-run", action="store_true", help="只估算和报告，不调用 BaoStock，不写入 CSV。")
    parser.add_argument("--skip-existing", action="store_true", help="已有日期不重复下载；当前合并逻辑始终本地原行优先。")
    parser.add_argument("--skip-backfill", action="store_true", help="只补本地最新日期之后的数据，不反复尝试更早历史；适合 daily_close。")
    parser.add_argument("--max-api-calls", type=int, default=50000, help="每日最大 BaoStock 调用数，默认 50000。")
    parser.add_argument("--adjustflag", default="2", choices=["1", "2", "3"], help="复权类型：1 后复权，2 前复权，3 不复权；默认 2。")
    parser.add_argument("--request-timeout", type=int, default=20, help="单次 BaoStock 请求超时秒数，默认 20，避免网络等待卡住自动化。")
    parser.add_argument("--login-retries", type=int, default=2, help="BaoStock 登录失败后的重试次数，默认 2。")
    parser.add_argument("--login-retry-delay", type=float, default=3.0, help="BaoStock 登录失败后的重试等待秒数，默认 3.0。")
    parser.add_argument("--retries", type=int, default=2, help="BaoStock 单标的请求失败后的重试次数，默认 2。")
    parser.add_argument("--retry-delay", type=float, default=1.0, help="BaoStock 请求失败后的重试等待秒数，默认 1.0。")
    parser.add_argument("--request-interval", type=float, default=0.1, help="BaoStock 标的之间的轻微等待秒数，默认 0.1。")
    parser.add_argument("--relogin-every", type=int, default=40, help="每处理多少个标的主动重登 BaoStock，默认 40；0 表示不主动重登。")
    parser.add_argument("--max-consecutive-failures", type=int, default=25, help="连续 BaoStock 请求失败达到该数量后停止本轮，默认 25。")
    parser.add_argument("--isolated-queries", action="store_true", help="每次 BaoStock 查询放入独立子进程，超时即停止该标的；适合 launchd 自动化。")
    parser.add_argument("--source-ready-probe", action="store_true", help="正式全池更新前先探测数据源是否已有 requested end 数据；未就绪则快速返回 CAUTION，避免全池空跑。")
    parser.add_argument("--strict-exit", action="store_true", help="正式更新未真正完成或失败比例过高时返回非 0，方便 launchd/dashboard 标记 CAUTION/ERROR。")
    parser.add_argument("--status-json", default=str(DATA_UPDATE_STATUS_FILE), help="写入机器可读更新状态 JSON，默认 reports/data_update_status.json。")
    parser.add_argument("--max-failed-ratio", type=float, default=0.20, help="strict-exit 下 failed_error 占比超过该值标记 ERROR，默认 0.20。")
    parser.add_argument("--max-pending-ratio", type=float, default=0.80, help="strict-exit 下 pending_source_update 占比超过该值标记 CAUTION，默认 0.80。")
    parser.add_argument("--_query-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_child-code", default="", help=argparse.SUPPRESS)
    parser.add_argument("--_child-start", default="", help=argparse.SUPPRESS)
    parser.add_argument("--_child-end", default="", help=argparse.SUPPRESS)
    parser.add_argument("--_child-adjustflag", default="2", help=argparse.SUPPRESS)
    parser.add_argument("--_child-output", default="", help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args._query_child:
        _run_query_child(args)
        return

    start = _normalize_date(args.start)
    end = _normalize_date(args.end)
    symbols = _parse_symbols(args.symbols)

    watchlist = read_watchlist(WATCHLIST_FILE)
    all_etf = args.all_etf or (args.source in {"auto", "jqdata"} and not symbols)
    items = _select_items(watchlist, symbols, all_etf=all_etf)
    ETF_DAILY_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DOWNLOAD_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if args.source != "baostock":
        from data_sources.source_router import run_source_update

        raise SystemExit(run_source_update(args, items, start, end))

    results: list[dict] = []
    estimated_api_calls = _estimate_api_calls(items, start, end, skip_backfill=args.skip_backfill)
    if estimated_api_calls > args.max_api_calls:
        results.append({"code": "", "name": "", "status": "failed_error", "message": f"estimated_api_calls {estimated_api_calls} exceeds max_api_calls {args.max_api_calls}; stopped before BaoStock login."})
        run_status = _build_run_status(results, estimated_api_calls, args.dry_run, start, end, args.source, args.max_failed_ratio, args.max_pending_ratio)
        _write_report(results, args.adjustflag, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
        _write_update_log(results, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
        _write_status_json(run_status, Path(args.status_json))
        _write_diagnosis_report(run_status, results)
        raise SystemExit(f"estimated_api_calls {estimated_api_calls} exceeds max_api_calls {args.max_api_calls}")

    if _is_empty_items(items):
        results.append({"code": "", "name": "", "status": "unsupported_or_empty", "message": "没有匹配到可下载 ETF。"})
        run_status = _build_run_status(results, estimated_api_calls, args.dry_run, start, end, args.source, args.max_failed_ratio, args.max_pending_ratio)
        _write_report(results, args.adjustflag, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
        _write_update_log(results, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
        _write_status_json(run_status, Path(args.status_json))
        _write_diagnosis_report(run_status, results)
        print(f"未匹配到可下载 ETF，已生成报告：{DATA_DOWNLOAD_REPORT_FILE}")
        return

    if args.dry_run:
        for _, item in items.iterrows():
            code = str(item["code"]).strip()
            bs_code = baostock_code(code)
            output_path = ETF_DAILY_DIR / f"{bs_code.replace('.', '_')}.csv"
            old = _read_existing(output_path)
            ranges = _download_ranges(old, start, end, skip_backfill=args.skip_backfill)
            results.append(_dry_run_result(item, bs_code, output_path, old, ranges, start, end))
        run_status = _build_run_status(results, estimated_api_calls, True, start, end, args.source, args.max_failed_ratio, args.max_pending_ratio)
        _write_report(results, args.adjustflag, run_status, estimated_api_calls=estimated_api_calls, dry_run=True)
        _write_update_log(results, run_status, estimated_api_calls=estimated_api_calls, dry_run=True)
        _write_status_json(run_status, Path(args.status_json))
        _write_diagnosis_report(run_status, results)
        print(f"ETF 数据下载 dry-run 完成：计划调用 {estimated_api_calls} 次，标的 {len(items)} 个。")
        print(f"已生成下载报告：{DATA_DOWNLOAD_REPORT_FILE}")
        return

    if args.source_ready_probe and estimated_api_calls > 5 and _is_today_or_future(end):
        probe_status = _probe_source_ready(items, end, args.adjustflag, args.request_timeout)
        if probe_status["status"] == "not_ready":
            results = _build_pending_results_from_local_ranges(items, start, end, skip_backfill=args.skip_backfill)
            run_status = _build_run_status(
                results,
                estimated_api_calls,
                args.dry_run,
                start,
                end,
                args.source,
                args.max_failed_ratio,
                args.max_pending_ratio,
                actual_api_calls=int(probe_status["actual_api_calls"]),
            )
            run_status["status"] = "pending_source_update"
            run_status["severity"] = "CAUTION"
            run_status["reason"] = probe_status["message"]
            run_status["recommendation"] = _data_update_recommendation(run_status["severity"], run_status["status"])
            _write_report(results, args.adjustflag, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
            _write_update_log(results, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
            _write_status_json(run_status, Path(args.status_json))
            _write_diagnosis_report(run_status, results)
            print(probe_status["message"])
            print(f"已生成下载报告：{DATA_DOWNLOAD_REPORT_FILE}")
            if args.strict_exit:
                raise SystemExit(int(run_status["exit_code"]))
            return
        if probe_status["status"] == "failed":
            results.append({"code": "", "name": "source_probe", "status": "failed_error", "message": probe_status["message"]})
            run_status = _build_run_status(
                results,
                estimated_api_calls,
                args.dry_run,
                start,
                end,
                args.source,
                args.max_failed_ratio,
                args.max_pending_ratio,
                actual_api_calls=int(probe_status["actual_api_calls"]),
            )
            _write_report(results, args.adjustflag, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
            _write_update_log(results, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
            _write_status_json(run_status, Path(args.status_json))
            _write_diagnosis_report(run_status, results)
            raise SystemExit(probe_status["message"])

    bs = None
    if not args.isolated_queries:
        try:
            import baostock as bs_module
        except Exception as exc:
            results.append({"code": "", "name": "", "status": "failed_error", "message": f"BaoStock 导入失败：{exc}"})
            run_status = _build_run_status(results, estimated_api_calls, args.dry_run, start, end, args.source, args.max_failed_ratio, args.max_pending_ratio)
            _write_report(results, args.adjustflag, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
            _write_update_log(results, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
            _write_status_json(run_status, Path(args.status_json))
            _write_diagnosis_report(run_status, results)
            raise SystemExit("BaoStock 导入失败，请确认在本机 .venv 中已安装 baostock。")
        bs = bs_module

        message = _baostock_login_with_retries(bs, args.request_timeout, args.login_retries, args.login_retry_delay)
        if message:
            results.append({"code": "", "name": "", "status": "failed_error", "message": message})
            run_status = _build_run_status(results, estimated_api_calls, args.dry_run, start, end, args.source, args.max_failed_ratio, args.max_pending_ratio)
            _write_report(results, args.adjustflag, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
            _write_update_log(results, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
            _write_status_json(run_status, Path(args.status_json))
            _write_diagnosis_report(run_status, results)
            raise SystemExit(message)

    try:
        consecutive_failures = 0
        for index, (_, item) in enumerate(items.iterrows(), start=1):
            if bs is not None and args.relogin_every > 0 and index > 1 and (index - 1) % args.relogin_every == 0:
                _baostock_logout(bs)
                relogin_message = _baostock_login_with_retries(bs, args.request_timeout, args.login_retries, args.login_retry_delay)
                if relogin_message:
                    results.append(_result_for_login_failure(item, relogin_message, start, end))
                    consecutive_failures += 1
                    if _should_stop_after_failures(consecutive_failures, args.max_consecutive_failures):
                        results.append(_stop_result(start, end, consecutive_failures, args.max_consecutive_failures))
                        break
                    continue
            result = _download_one_with_retries(
                bs,
                item,
                start,
                end,
                args.adjustflag,
                args.request_timeout,
                skip_backfill=args.skip_backfill,
                retries=max(args.retries, 0),
                retry_delay=max(args.retry_delay, 0),
            )
            results.append(result)
            if str(result.get("status", "")) == "failed_error":
                consecutive_failures += 1
            else:
                consecutive_failures = 0
            if _should_stop_after_failures(consecutive_failures, args.max_consecutive_failures):
                results.append(_stop_result(start, end, consecutive_failures, args.max_consecutive_failures))
                break
            if args.request_interval > 0:
                time.sleep(args.request_interval)
    finally:
        if bs is not None:
            _baostock_logout(bs)

    run_status = _build_run_status(results, estimated_api_calls, args.dry_run, start, end, args.source, args.max_failed_ratio, args.max_pending_ratio)
    _write_report(results, args.adjustflag, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
    _write_update_log(results, run_status, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
    _write_status_json(run_status, Path(args.status_json))
    _write_diagnosis_report(run_status, results)
    counts = _status_counts(results)
    added_count = counts.get("success_appended", 0) + counts.get("partial_success", 0)
    up_to_date_count = counts.get("up_to_date", 0) + counts.get("already_up_to_date", 0)
    no_new_count = counts.get("no_new_data", 0) + counts.get("pending_source_update", 0) + counts.get("backfill_no_data", 0)
    failed_count = counts.get("failed_error", 0) + counts.get("unsupported_or_empty", 0)
    print(
        "ETF 数据更新完成："
        f"新增/部分新增 {added_count} 个，已最新 {up_to_date_count} 个，"
        f"数据源未更新/无新增 {no_new_count} 个，真正失败/不可用 {failed_count} 个。"
    )
    print(f"状态统计：{counts}")
    print(f"更新健康：{run_status['severity']} / {run_status['status']} - {run_status['reason']}")
    print(f"已生成下载报告：{DATA_DOWNLOAD_REPORT_FILE}")
    if args.strict_exit and int(run_status.get("exit_code", 0)) != 0:
        raise SystemExit(int(run_status["exit_code"]))


def _select_items(watchlist: pd.DataFrame, symbols: set[str] | None, all_etf: bool) -> pd.DataFrame:
    if all_etf:
        df = _build_all_etf_universe(watchlist)
    else:
        df = watchlist.copy()
        df["code"] = df["code"].astype(str).str.strip()
        pool_mask = df["role"].isin(["trade_pool", "observe_pool"])
        etf_mask = df["type"].astype(str).str.upper() == "ETF"
        df = df[pool_mask & etf_mask].copy()
    if symbols:
        df = df[df["code"].isin(symbols)]
    return df.sort_values("code").drop_duplicates("code", keep="first").reset_index(drop=True)


def _build_all_etf_universe(watchlist: pd.DataFrame) -> pd.DataFrame:
    rows: dict[str, dict] = {}

    for path in sorted(ETF_DAILY_DIR.glob("*.csv")):
        code = _code_from_etf_daily_path(path)
        if not code:
            continue
        rows[code] = {
            "code": code,
            "name": code,
            "type": "ETF",
            "group": "formal_data",
            "role": "data_update",
            "source": "data_etf_daily",
        }

    if not watchlist.empty:
        wl = watchlist.copy()
        wl["code"] = wl["code"].astype(str).str.strip()
        wl = wl[(wl["type"].astype(str).str.upper() == "ETF") & wl["role"].isin(["trade_pool", "observe_pool"])]
        for _, row in wl.iterrows():
            code = str(row["code"]).strip()
            if code:
                rows[code] = {**rows.get(code, {}), **row.to_dict(), "role": str(row.get("role", "data_update"))}

    candidate_path = PROJECT_ROOT / "data" / "etf_pool_expansion_candidates.csv"
    results_path = PROJECT_ROOT / "reports" / "etf_expansion_import_results.csv"
    imported_codes = _imported_expansion_codes(results_path)
    if candidate_path.exists():
        candidates = pd.read_csv(candidate_path, dtype=str).fillna("")
        valid_status = candidates["status"].eq("imported") if "status" in candidates else pd.Series(False, index=candidates.index)
        for _, row in candidates[valid_status].iterrows():
            code = str(row.get("code", "")).strip()
            if not re.fullmatch(r"\d{6}", code):
                continue
            if code not in imported_codes and not (ETF_DAILY_DIR / f"{baostock_code(code).replace('.', '_')}.csv").exists():
                continue
            rows[code] = {
                **rows.get(code, {}),
                "code": code,
                "name": str(row.get("name", code)),
                "type": "ETF",
                "group": str(row.get("group", "expanded")),
                "role": str(row.get("pool", "data_update")) or "data_update",
                "source": "etf_pool_expansion_candidates",
            }

    quarantine = {p.name.split(".")[0] for p in (PROJECT_ROOT / "data" / "staging" / "jqdata_expanded_failed").glob("*.csv")}
    rows = {code: row for code, row in rows.items() if code not in quarantine}
    return pd.DataFrame(rows.values())


def _imported_expansion_codes(results_path: Path) -> set[str]:
    if not results_path.exists():
        return set()
    results = pd.read_csv(results_path, dtype=str).fillna("")
    if "final_action" in results.columns:
        results = results[results["final_action"].eq("imported")]
    elif "status" in results.columns:
        results = results[results["status"].eq("imported")]
    return set(results.get("symbol", pd.Series(dtype=str)).astype(str))


def _code_from_etf_daily_path(path: Path) -> str:
    match = re.fullmatch(r"(?:sh|sz)_(\d{6})\.csv", path.name)
    return match.group(1) if match else ""


def _is_empty_items(items: object) -> bool:
    if items is None:
        return True
    if isinstance(items, pd.DataFrame):
        return items.empty
    if isinstance(items, (list, dict, tuple, set)):
        return len(items) == 0
    return False


def _estimate_api_calls(items: pd.DataFrame, start: str, end: str, skip_backfill: bool = False) -> int:
    calls = 0
    for _, item in items.iterrows():
        code = str(item["code"]).strip()
        output_path = ETF_DAILY_DIR / f"{baostock_code(code).replace('.', '_')}.csv"
        if _download_ranges(_read_existing(output_path), start, end, skip_backfill=skip_backfill):
            calls += 1
    return calls


def _dry_run_result(item: pd.Series, bs_code: str, output_path: Path, old: pd.DataFrame | None, ranges: list[tuple[str, str, str]], start: str, end: str) -> dict:
    if not ranges:
        return _result(item, bs_code, output_path, "already_up_to_date", old, requested_start=start, requested_end=end, message="dry-run: 本地 CSV 已覆盖本次 start/end 范围。")
    msg = "dry-run: planned ranges " + "; ".join(f"{mode} {s}~{e}" for s, e, mode in ranges)
    return _result(
        item,
        bs_code,
        output_path,
        "dry_run_planned",
        old,
        requested_start=start,
        requested_end=end,
        backfill_needed=any(item[2] == "backfill" for item in ranges),
        forward_needed=any(item[2] == "forward" for item in ranges),
        message=msg,
    )


def _probe_source_ready(items: pd.DataFrame, requested_end: str, adjustflag: str, request_timeout: int) -> dict:
    preferred = ["510300", "159915", "512800", "515000", "515220", "510050"]
    item_map = {str(row["code"]).strip(): row for _, row in items.iterrows()}
    probe_items = [item_map[code] for code in preferred if code in item_map]
    if len(probe_items) < 3:
        for _, row in items.head(5).iterrows():
            code = str(row["code"]).strip()
            if code not in {str(item["code"]).strip() for item in probe_items}:
                probe_items.append(row)
            if len(probe_items) >= 5:
                break

    messages: list[str] = []
    actual_calls = 0
    failures = 0
    for item in probe_items[:5]:
        code = str(item["code"]).strip()
        bs_code = baostock_code(code)
        fetched, message = _query_baostock_daily_isolated(bs_code, requested_end, requested_end, adjustflag, request_timeout)
        actual_calls += 1
        messages.append(f"{code}: {message}")
        if fetched is None:
            failures += 1
            continue
        if not fetched.empty:
            return {
                "status": "ready",
                "actual_api_calls": actual_calls,
                "message": f"BaoStock source probe found {requested_end} data from {code}; continue full update.",
            }

    if failures >= max(len(probe_items[:5]), 1):
        return {
            "status": "failed",
            "actual_api_calls": actual_calls,
            "message": "BaoStock source probe failed for all anchors: " + "；".join(messages),
        }
    return {
        "status": "not_ready",
        "actual_api_calls": actual_calls,
        "message": f"BaoStock source probe indicates {requested_end} daily data is not ready yet; skipped full-universe empty run. Probe: " + "；".join(messages),
    }


def _build_pending_results_from_local_ranges(items: pd.DataFrame, start: str, end: str, skip_backfill: bool) -> list[dict]:
    rows: list[dict] = []
    for _, item in items.iterrows():
        code = str(item["code"]).strip()
        bs_code = baostock_code(code)
        output_path = ETF_DAILY_DIR / f"{bs_code.replace('.', '_')}.csv"
        old = _read_existing(output_path)
        ranges = _download_ranges(old, start, end, skip_backfill=skip_backfill)
        if not ranges:
            rows.append(_result(item, bs_code, output_path, "up_to_date", old, requested_start=start, requested_end=end, message="本地 CSV 已覆盖本次 start/end 范围。"))
        else:
            rows.append(_result(
                item,
                bs_code,
                output_path,
                "pending_source_update",
                old,
                requested_start=start,
                requested_end=end,
                backfill_needed=any(row[2] == "backfill" for row in ranges),
                forward_needed=any(row[2] == "forward" for row in ranges),
                message="source-ready probe returned empty for requested end; skipped full-universe query until data source is ready.",
            ))
    return rows


def _download_one(bs: object, item: pd.Series, default_start: str, end: str, adjustflag: str, request_timeout: int, skip_backfill: bool = False) -> dict:
    code = str(item["code"]).strip()
    name = str(item.get("name", code)).strip()
    bs_code = baostock_code(code)
    output_path = ETF_DAILY_DIR / f"{bs_code.replace('.', '_')}.csv"
    old = _read_existing(output_path)
    ranges = _download_ranges(old, default_start, end, skip_backfill=skip_backfill)
    if not ranges:
        return _result(
            item,
            bs_code,
            output_path,
            "up_to_date",
            old,
            requested_start=default_start,
            requested_end=end,
            message="本地 CSV 已覆盖本次 start/end 范围。",
        )

    backfill_frames: list[pd.DataFrame] = []
    forward_frames: list[pd.DataFrame] = []
    messages: list[str] = []
    query_errors: list[str] = []
    for range_start, range_end, range_mode in ranges:
        fetched, message = _query_baostock_daily(bs, bs_code, range_start, range_end, adjustflag, request_timeout)
        messages.append(f"{range_mode} {range_start}~{range_end}: {message}")
        if fetched is None:
            query_errors.append(f"{range_mode} {range_start}~{range_end}: {message}")
        elif not fetched.empty:
            normalized = _normalize_download(fetched)
            if range_mode == "backfill":
                backfill_frames.append(normalized)
            else:
                forward_frames.append(normalized)

    backfill_new = _concat_frames(backfill_frames)
    forward_new = _concat_frames(forward_frames)
    backfill_rows = len(backfill_new)
    forward_rows = len(forward_new)
    if backfill_rows == 0 and forward_rows == 0:
        status = _empty_download_status(old, ranges, end, query_errors)
        return _result(
            item,
            bs_code,
            output_path,
            status,
            old,
            requested_start=default_start,
            requested_end=end,
            backfill_needed=any(item[2] == "backfill" for item in ranges),
            forward_needed=any(item[2] == "forward" for item in ranges),
            message=_empty_download_message(status, old, messages, query_errors),
        )

    merged = _merge_daily(old, backfill_new, forward_new)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    if backfill_rows > 0 and forward_rows > 0:
        status = "partial_success"
    elif backfill_rows > 0:
        status = "partial_success"
    else:
        status = "success_appended"
    return _result(
        item,
        bs_code,
        output_path,
        status,
        merged,
        requested_start=default_start,
        requested_end=end,
        backfill_needed=any(item[2] == "backfill" for item in ranges),
        forward_needed=any(item[2] == "forward" for item in ranges),
        backfill_rows=backfill_rows,
        forward_rows=forward_rows,
        message="；".join(messages) + ("；部分请求异常但已有新增数据。" if query_errors else "") + "；保存成功。",
    )


def _download_one_with_retries(
    bs: object,
    item: pd.Series,
    default_start: str,
    end: str,
    adjustflag: str,
    request_timeout: int,
    skip_backfill: bool,
    retries: int,
    retry_delay: float,
) -> dict:
    attempts: list[str] = []
    for attempt in range(retries + 1):
        result = _download_one(bs, item, default_start, end, adjustflag, request_timeout, skip_backfill=skip_backfill)
        status = str(result.get("status", ""))
        message = str(result.get("message", ""))
        if status != "failed_error" or not _is_transient_baostock_error(message):
            if attempts:
                result["message"] = "；".join(attempts + [message])
            return result

        attempts.append(f"attempt {attempt + 1} failed: {message}")
        if attempt >= retries:
            result["message"] = "；".join(attempts)
            return result
        time.sleep(retry_delay)
        if bs is not None:
            _baostock_logout(bs)
            relogin_message = _baostock_login_with_retries(bs, request_timeout, retries=1, retry_delay=retry_delay)
            if relogin_message:
                attempts.append(f"relogin failed: {relogin_message}")
                result["message"] = "；".join(attempts)
                return result
        time.sleep(retry_delay)
    return result


def _is_transient_baostock_error(message: str) -> bool:
    transient_markers = [
        "Broken pipe",
        "RemoteDisconnected",
        "ConnectionError",
        "接收数据异常",
        "timed out",
        "超时",
        "单次请求超过",
    ]
    return any(marker in message for marker in transient_markers)


def _baostock_login_with_retries(bs: object, request_timeout: int, retries: int, retry_delay: float) -> str:
    attempts: list[str] = []
    total_attempts = max(int(retries or 0), 0) + 1
    for attempt in range(total_attempts):
        message = _baostock_login(bs, request_timeout)
        if not message:
            if attempts:
                print(f"BaoStock 登录重试成功：第 {attempt + 1} 次尝试。")
            return ""
        attempts.append(f"attempt {attempt + 1}: {message}")
        if attempt < total_attempts - 1:
            print(f"BaoStock 登录失败，{max(retry_delay, 0)} 秒后重试：{message}", flush=True)
            time.sleep(max(retry_delay, 0))
    return "；".join(attempts)


def _baostock_login(bs: object, request_timeout: int) -> str:
    if request_timeout > 0:
        socket.setdefaulttimeout(request_timeout)
    try:
        with _baostock_timeout(request_timeout):
            login_result = bs.login()
    except _BaoStockTimeoutError as exc:
        return f"BaoStock 登录超时：{exc}"
    except Exception as exc:
        return f"BaoStock 登录异常：{exc}"
    if getattr(login_result, "error_code", "") != "0":
        return f"BaoStock 登录失败：{getattr(login_result, 'error_msg', '')}"
    _set_baostock_socket_timeout(request_timeout)
    return ""


def _baostock_logout(bs: object) -> None:
    try:
        bs.logout()
    except Exception:
        pass


def _set_baostock_socket_timeout(request_timeout: int) -> None:
    if request_timeout <= 0:
        return
    try:
        import baostock.common.context as bs_context

        sock = getattr(bs_context, "default_socket", None)
        if sock is not None:
            sock.settimeout(request_timeout)
    except Exception:
        pass


def _should_stop_after_failures(consecutive_failures: int, max_consecutive_failures: int) -> bool:
    return max_consecutive_failures > 0 and consecutive_failures >= max_consecutive_failures


def _stop_result(requested_start: str, requested_end: str, consecutive_failures: int, max_consecutive_failures: int) -> dict:
    return {
        "code": "",
        "name": "batch_guard",
        "group": "system",
        "role": "guard",
        "baostock_code": "",
        "requested_start": requested_start,
        "requested_end": requested_end,
        "status": "stopped_after_consecutive_failures",
        "backfill_needed": False,
        "backfill_rows": 0,
        "forward_needed": False,
        "forward_rows": 0,
        "total_rows": 0,
        "start_date": "",
        "end_date": "",
        "file_path": "",
        "message": f"连续 BaoStock 请求失败 {consecutive_failures} 次，达到阈值 {max_consecutive_failures}，本轮停止后续请求，避免自动化长时间卡住。",
    }


def _result_for_login_failure(item: pd.Series, message: str, requested_start: str, requested_end: str) -> dict:
    code = str(item.get("code", "")).strip()
    bs_code = baostock_code(code)
    output_path = ETF_DAILY_DIR / f"{bs_code.replace('.', '_')}.csv"
    old = _read_existing(output_path)
    return _result(
        item,
        bs_code,
        output_path,
        "failed_error",
        old,
        requested_start=requested_start,
        requested_end=requested_end,
        message=message,
    )


def _empty_download_status(old: pd.DataFrame | None, ranges: list[tuple[str, str, str]], end: str, query_errors: list[str]) -> str:
    if query_errors:
        return "failed_error"
    has_local = old is not None and not old.empty and "date" in old.columns
    forward_needed = any(item[2] == "forward" for item in ranges)
    backfill_needed = any(item[2] == "backfill" for item in ranges)
    if not has_local:
        return "unsupported_or_empty"
    if forward_needed:
        return "pending_source_update" if _is_today_or_future(end) else "no_new_data"
    if backfill_needed:
        return "backfill_no_data"
    return "no_new_data"


def _empty_download_message(status: str, old: pd.DataFrame | None, messages: list[str], query_errors: list[str]) -> str:
    local_note = "本地已有有效数据；" if old is not None and not old.empty else "本地无有效数据；"
    if status == "failed_error":
        return local_note + "BaoStock 请求异常或返回错误；" + "；".join(query_errors or messages)
    if status == "unsupported_or_empty":
        return local_note + "BaoStock 全范围返回空数据，可能是不支持该 ETF、代码错误、ETF 太新或数据源暂无数据；" + "；".join(messages)
    if status == "pending_source_update":
        return local_note + "forward 请求返回空，可能是数据源尚未更新或当日无可用数据；backfill 空不视为正式失败；" + "；".join(messages)
    if status == "backfill_no_data":
        return local_note + "backfill 请求返回空，可能是 BaoStock 不支持更早历史或 ETF 当时尚未上市；本地数据仍可用；" + "；".join(messages)
    return local_note + "请求返回空但本地数据可用，视为无新增数据；" + "；".join(messages)


def _is_today_or_future(value: str) -> bool:
    try:
        return pd.to_datetime(value).date() >= date.today()
    except Exception:
        return False


def _download_ranges(old: pd.DataFrame | None, default_start: str, end: str, skip_backfill: bool = False) -> list[tuple[str, str, str]]:
    requested_start = pd.to_datetime(default_start)
    requested_end = pd.to_datetime(end)
    if requested_start > requested_end:
        return []
    if old is None or old.empty or "date" not in old.columns:
        return [(requested_start.strftime("%Y-%m-%d"), requested_end.strftime("%Y-%m-%d"), "forward")]

    old_dates = pd.to_datetime(old["date"], errors="coerce").dropna()
    if old_dates.empty:
        return [(requested_start.strftime("%Y-%m-%d"), requested_end.strftime("%Y-%m-%d"), "forward")]

    first_date = old_dates.min()
    last_date = old_dates.max()
    ranges: list[tuple[str, str, str]] = []

    backward_end = first_date - pd.Timedelta(days=1)
    if not skip_backfill and first_date > requested_start and requested_start <= backward_end:
        ranges.append((requested_start.strftime("%Y-%m-%d"), backward_end.strftime("%Y-%m-%d"), "backfill"))

    forward_start = last_date + pd.Timedelta(days=1)
    if last_date < requested_end and forward_start <= requested_end:
        ranges.append((forward_start.strftime("%Y-%m-%d"), requested_end.strftime("%Y-%m-%d"), "forward"))

    return ranges


def _query_baostock_daily(bs: object, bs_code: str, start: str, end: str, adjustflag: str, request_timeout: int) -> tuple[pd.DataFrame | None, str]:
    if bs is None:
        return _query_baostock_daily_isolated(bs_code, start, end, adjustflag, request_timeout)

    try:
        with _baostock_timeout(request_timeout):
            rs = bs.query_history_k_data_plus(
                bs_code,
                ",".join(BAOSTOCK_FIELDS),
                start_date=start,
                end_date=end,
                frequency="d",
                adjustflag=adjustflag,
            )
            if getattr(rs, "error_code", "") != "0":
                return None, f"BaoStock 返回错误：{getattr(rs, 'error_msg', '')}"

            rows = []
            while rs.next():
                rows.append(rs.get_row_data())
    except Exception as exc:
        return None, f"BaoStock 请求异常：{exc}"

    if not rows:
        return pd.DataFrame(columns=BAOSTOCK_FIELDS), "返回空数据"
    return pd.DataFrame(rows, columns=BAOSTOCK_FIELDS), f"返回 {len(rows)} 行"


def _query_baostock_daily_isolated(bs_code: str, start: str, end: str, adjustflag: str, request_timeout: int) -> tuple[pd.DataFrame | None, str]:
    timeout_seconds = max(int(request_timeout or 8) + 3, 3)
    with tempfile.NamedTemporaryFile(prefix="baostock_query_", suffix=".json", delete=False) as tmp:
        output_path = Path(tmp.name)
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--_query-child",
        "--_child-code",
        bs_code,
        "--_child-start",
        start,
        "--_child-end",
        end,
        "--_child-adjustflag",
        adjustflag,
        "--_child-output",
        str(output_path),
    ]
    try:
        completed = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        _unlink_silent(output_path)
        return None, f"BaoStock 子进程请求超过 {timeout_seconds} 秒：{bs_code} {start}~{end}"

    try:
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:
        _unlink_silent(output_path)
        stderr = (completed.stderr or "").strip()
        return None, f"BaoStock 子进程无有效结果：{type(exc).__name__}: {exc}; stderr={stderr}"
    finally:
        _unlink_silent(output_path)

    if completed.returncode != 0 or not payload.get("ok", False):
        return None, str(payload.get("message") or completed.stderr or "BaoStock 子进程请求失败")
    rows = payload.get("rows", [])
    if not rows:
        return pd.DataFrame(columns=BAOSTOCK_FIELDS), "返回空数据"
    return pd.DataFrame(rows, columns=BAOSTOCK_FIELDS), f"返回 {len(rows)} 行"


def _run_query_child(args: argparse.Namespace) -> None:
    payload: dict[str, object] = {"ok": False, "message": "", "rows": []}
    try:
        import baostock as bs

        login_result = bs.login()
        if getattr(login_result, "error_code", "") != "0":
            payload["message"] = f"BaoStock 登录失败：{getattr(login_result, 'error_msg', '')}"
        else:
            rs = bs.query_history_k_data_plus(
                args._child_code,
                ",".join(BAOSTOCK_FIELDS),
                start_date=args._child_start,
                end_date=args._child_end,
                frequency="d",
                adjustflag=args._child_adjustflag,
            )
            if getattr(rs, "error_code", "") != "0":
                payload["message"] = f"BaoStock 返回错误：{getattr(rs, 'error_msg', '')}"
            else:
                rows = []
                while rs.next():
                    rows.append(rs.get_row_data())
                payload = {"ok": True, "message": f"返回 {len(rows)} 行", "rows": rows}
        try:
            bs.logout()
        except Exception:
            pass
    except Exception as exc:
        payload["message"] = f"BaoStock 子进程异常：{type(exc).__name__}: {exc}"

    Path(args._child_output).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _unlink_silent(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


class _BaoStockTimeoutError(TimeoutError):
    pass


@contextmanager
def _baostock_timeout(seconds: int):
    if seconds <= 0:
        yield
        return

    def _handle_timeout(signum, frame):  # noqa: ARG001
        raise _BaoStockTimeoutError(f"BaoStock 单次请求超过 {seconds} 秒")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


def _normalize_download(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for col in ["open", "high", "low", "close", "preclose", "volume", "amount", "turn", "pctChg"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["date", "open", "high", "low", "close", "volume"])
    return out[BAOSTOCK_FIELDS].sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)


def _merge_daily(old: pd.DataFrame | None, backfill_new: pd.DataFrame, forward_new: pd.DataFrame) -> pd.DataFrame:
    frames = []
    if old is not None and not old.empty:
        old = old.copy()
        for col in BAOSTOCK_FIELDS:
            if col not in old.columns:
                old[col] = pd.NA
        frames.append(old[BAOSTOCK_FIELDS])
    if not backfill_new.empty:
        frames.append(backfill_new[BAOSTOCK_FIELDS])
    if not forward_new.empty:
        frames.append(forward_new[BAOSTOCK_FIELDS])
    merged = pd.concat(frames, ignore_index=True)
    merged["date"] = pd.to_datetime(merged["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    merged = merged.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="first")
    return merged[BAOSTOCK_FIELDS].reset_index(drop=True)


def _concat_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(columns=BAOSTOCK_FIELDS)
    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        return pd.DataFrame(columns=BAOSTOCK_FIELDS)
    return combined[BAOSTOCK_FIELDS].sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)


def _read_existing(path: Path) -> pd.DataFrame | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        return pd.read_csv(path, dtype={"code": str})
    except Exception:
        return None


def _result(
    item: pd.Series,
    bs_code: str,
    output_path: Path,
    status: str,
    df: pd.DataFrame | None,
    requested_start: str,
    requested_end: str,
    message: str,
    backfill_needed: bool = False,
    forward_needed: bool = False,
    backfill_rows: int = 0,
    forward_rows: int = 0,
) -> dict:
    row_count = 0 if df is None else len(df)
    start_date = ""
    end_date = ""
    if df is not None and not df.empty and "date" in df.columns:
        dates = pd.to_datetime(df["date"], errors="coerce").dropna()
        if not dates.empty:
            start_date = dates.min().strftime("%Y-%m-%d")
            end_date = dates.max().strftime("%Y-%m-%d")
    return {
        "code": str(item.get("code", "")),
        "name": str(item.get("name", "")),
        "group": str(item.get("group", "")),
        "role": str(item.get("role", "")),
        "baostock_code": bs_code,
        "requested_start": requested_start,
        "requested_end": requested_end,
        "status": status,
        "backfill_needed": backfill_needed,
        "backfill_rows": backfill_rows,
        "forward_needed": forward_needed,
        "forward_rows": forward_rows,
        "total_rows": row_count,
        "start_date": start_date,
        "end_date": end_date,
        "file_path": str(output_path.relative_to(PROJECT_ROOT)),
        "message": message,
    }


def _build_run_status(
    results: list[dict],
    estimated_api_calls: int,
    dry_run: bool,
    requested_start: str,
    requested_end: str,
    source: str,
    max_failed_ratio: float,
    max_pending_ratio: float,
    actual_api_calls: int | None = None,
) -> dict:
    counts = _status_counts(results)
    processed_symbols = len([row for row in results if str(row.get("code", "")).strip()])
    universe_size = max(processed_symbols, estimated_api_calls if estimated_api_calls > 0 else 0, len(results), 1)
    denominator = max(universe_size, 1)
    added_rows = sum(int(row.get("backfill_rows", 0) or 0) + int(row.get("forward_rows", 0) or 0) for row in results)
    failed_count = counts.get("failed_error", 0) + counts.get("unsupported_or_empty", 0) + counts.get("stopped_after_consecutive_failures", 0)
    pending_count = counts.get("pending_source_update", 0)
    up_to_date_count = counts.get("up_to_date", 0) + counts.get("already_up_to_date", 0)
    no_new_count = counts.get("no_new_data", 0) + counts.get("backfill_no_data", 0)
    planned_count = counts.get("dry_run_planned", 0)
    latest_local_date = _latest_local_data_date()
    requested_end_date = _normalize_date(requested_end)
    stale_vs_requested = _date_less_than(latest_local_date, requested_end_date)
    failed_ratio = failed_count / denominator
    pending_ratio = pending_count / denominator

    if dry_run:
        severity = "INFO"
        status = "dry_run"
        reason = f"dry-run only; planned {planned_count} BaoStock queries, no local CSV was written."
        exit_code = 0
    elif failed_ratio > max_failed_ratio:
        severity = "ERROR"
        status = "failed"
        reason = f"failed/unsupported ratio {failed_ratio:.1%} exceeds threshold {max_failed_ratio:.1%}; data update did not complete cleanly."
        exit_code = 3
    elif added_rows == 0 and pending_ratio >= max_pending_ratio and stale_vs_requested:
        severity = "CAUTION"
        status = "pending_source_update"
        reason = f"BaoStock returned no forward rows for most ETFs; latest local date remains {latest_local_date}, requested end {requested_end_date}."
        exit_code = 2
    elif added_rows == 0 and stale_vs_requested and (pending_count > 0 or no_new_count > 0 or failed_count > 0):
        severity = "CAUTION"
        status = "stale_no_new_rows"
        reason = f"No new rows were appended and local data is still stale versus requested end {requested_end_date}."
        exit_code = 2
    elif failed_count > 0:
        severity = "CAUTION"
        status = "partial_warning"
        reason = f"Update appended {added_rows} rows but {failed_count} ETF queries failed or were unsupported."
        exit_code = 2
    elif added_rows > 0:
        severity = "OK"
        status = "updated"
        reason = f"Update appended {added_rows} rows; existing local rows kept priority on duplicate dates."
        exit_code = 0
    else:
        severity = "OK"
        status = "up_to_date"
        reason = "No new rows were needed; local files already cover the requested range or source returned no older backfill."
        exit_code = 0

    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "mode": "dry-run" if dry_run else "formal update",
        "requested_start": requested_start,
        "requested_end": requested_end_date,
        "latest_local_date": latest_local_date,
        "stale_vs_requested": stale_vs_requested,
        "severity": severity,
        "status": status,
        "reason": reason,
        "exit_code": exit_code,
        "universe_size": universe_size,
        "processed_symbols": processed_symbols,
        "estimated_api_calls": estimated_api_calls,
        "actual_api_calls": 0 if dry_run else (estimated_api_calls if actual_api_calls is None else actual_api_calls),
        "status_counts": counts,
        "added_rows": added_rows,
        "failed_count": failed_count,
        "failed_ratio": round(failed_ratio, 6),
        "pending_count": pending_count,
        "pending_ratio": round(pending_ratio, 6),
        "up_to_date_count": up_to_date_count,
        "no_new_count": no_new_count,
        "dry_run_planned_count": planned_count,
        "baostock_api_calls": 0 if dry_run else (estimated_api_calls if actual_api_calls is None else actual_api_calls),
        "safety": {
            "broker_api": False,
            "real_order": False,
            "real_account": False,
            "credentials_saved": False,
            "local_existing_rows_priority": True,
        },
        "recommendation": _data_update_recommendation(severity, status),
    }


def _data_update_recommendation(severity: str, status: str) -> str:
    if severity == "ERROR":
        return "Do not treat daily ETF data as updated. Keep reports in cached-data mode and review BaoStock connectivity or switch to a staging-first Tushare/JQData fallback."
    if severity == "CAUTION":
        return "Treat signals as close-proxy/cached-data signals. Do not show daily update as green; rerun later or use another read-only data source through staging."
    if status == "dry_run":
        return "Dry-run only. Run without --dry-run after reviewing estimated calls."
    return "Daily update status is acceptable under current local-data rules."


def _latest_local_data_date() -> str:
    latest = ""
    for path in sorted(ETF_DAILY_DIR.glob("*.csv")):
        try:
            df = pd.read_csv(path, usecols=["date"], dtype=str)
        except Exception:
            continue
        if df.empty:
            continue
        dates = pd.to_datetime(df["date"], errors="coerce").dropna()
        if dates.empty:
            continue
        candidate = dates.max().strftime("%Y-%m-%d")
        if not latest or candidate > latest:
            latest = candidate
    return latest or "unknown"


def _date_less_than(left: str, right: str) -> bool:
    try:
        return pd.to_datetime(left) < pd.to_datetime(right)
    except Exception:
        return False


def _write_status_json(run_status: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run_status, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_diagnosis_report(run_status: dict, results: list[dict]) -> None:
    counts = run_status.get("status_counts", {})
    failed_rows = [row for row in results if str(row.get("status", "")) in {"failed_error", "unsupported_or_empty", "stopped_after_consecutive_failures"}]
    pending_rows = [row for row in results if str(row.get("status", "")) == "pending_source_update"]
    lines = [
        f"# 自动化数据更新诊断报告 {run_status.get('generated_at', '')}",
        "",
        "本报告用于解释 daily_close 数据更新是否真正完成。它只检查本地行情更新状态，不接券商 API，不下单，不读取账号密码。",
        "",
        "## 结论",
        f"- severity：{run_status.get('severity')}",
        f"- status：{run_status.get('status')}",
        f"- reason：{run_status.get('reason')}",
        f"- recommendation：{run_status.get('recommendation')}",
        "",
        "## 关键数字",
        f"- source：{run_status.get('source')}",
        f"- mode：{run_status.get('mode')}",
        f"- requested_end：{run_status.get('requested_end')}",
        f"- latest_local_date：{run_status.get('latest_local_date')}",
        f"- universe_size：{run_status.get('universe_size')}",
        f"- estimated_api_calls：{run_status.get('estimated_api_calls')}",
        f"- added_rows：{run_status.get('added_rows')}",
        f"- failed_count：{run_status.get('failed_count')}",
        f"- pending_count：{run_status.get('pending_count')}",
        f"- status_counts：{counts}",
        "",
        "## 失败或不可用样例",
    ]
    if failed_rows:
        for row in failed_rows[:30]:
            lines.append(f"- {row.get('code', '')} {row.get('name', '')}: {row.get('status')} / {str(row.get('message', ''))[:240]}")
    else:
        lines.append("- 无。")
    lines.extend(["", "## 数据源暂未更新样例"])
    if pending_rows:
        for row in pending_rows[:30]:
            lines.append(f"- {row.get('code', '')} {row.get('name', '')}: {str(row.get('message', ''))[:240]}")
    else:
        lines.append("- 无。")
    lines.extend(
        [
            "",
            "## 数据源切换建议",
            "- BaoStock 可继续作为免费日常源，但自动化不得把 pending/failed 误标为 OK。",
            "- Tushare/JQData 可以作为 L2 只读备用源，但必须通过环境变量读取 token/账号，先写入 staging，再 validate/dry-run/import。",
            "- JQData 若试用区间有限，不应用来强拉无权限日期；Tushare 若有稳定日线权限，更适合做 BaoStock 失败时的备用日更源。",
            "",
            "## 安全边界",
            "- 不接券商 API；不真实下单；不读取真实账户；不保存密码或 token。",
            "- 合并重复日期时仍保持本地原行优先。",
        ]
    )
    DATA_UPDATE_DIAGNOSIS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_report(results: list[dict], adjustflag: str, run_status: dict, estimated_api_calls: int = 0, dry_run: bool = False) -> None:
    counts = _status_counts(results)
    true_failed = counts.get("failed_error", 0)
    pending = counts.get("pending_source_update", 0)
    no_new = counts.get("no_new_data", 0)
    lines = [
        f"# ETF 本机数据下载报告 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "本报告来自本机 BaoStock ETF 下载脚本。脚本只下载行情数据，不接券商 API，不下单，不读取账号密码。",
        "",
        f"- 保存目录：`data/etf_daily/`",
        f"- 复权参数 adjustflag：{adjustflag}",
        f"- 模式：{'dry-run' if dry_run else 'formal update'}",
        f"- estimated_api_calls：{estimated_api_calls}",
        f"- update_severity：{run_status.get('severity')}",
        f"- update_status：{run_status.get('status')}",
        f"- latest_local_date：{run_status.get('latest_local_date')}",
        f"- added_rows：{run_status.get('added_rows')}",
        f"- reason：{run_status.get('reason')}",
        "- BaoStock API calls are one query per ETF with missing requested range; skipped/up-to-date files are not queried.",
        f"- 状态统计：{counts}",
        f"- 真正请求/系统错误 failed_error：{true_failed}",
        f"- 数据源暂未更新 pending_source_update：{pending}",
        f"- 无新增 no_new_data：{no_new}",
        "- 说明：本地已有有效数据时，forward 当天返回空不会再被计为真正失败。",
        "",
        "## 下载结果",
        "| 代码 | 名称 | group | pool | BaoStock代码 | 请求起始 | 请求结束 | 状态 | 是否前补 | 前补新增行数 | 是否后补 | 后补新增行数 | 最终起始日期 | 最终结束日期 | 最终行数 | 文件 | 说明 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | ---: | --- | --- | ---: | --- | --- |",
    ]
    for row in results:
        lines.append(
            f"| {row.get('code', '')} | {row.get('name', '')} | {row.get('group', '')} | {row.get('role', '')} | "
            f"{row.get('baostock_code', '')} | {row.get('requested_start', '')} | {row.get('requested_end', '')} | {row.get('status', '')} | "
            f"{'是' if row.get('backfill_needed', False) else '否'} | {row.get('backfill_rows', 0)} | "
            f"{'是' if row.get('forward_needed', False) else '否'} | {row.get('forward_rows', 0)} | "
            f"{row.get('start_date', '')} | {row.get('end_date', '')} | {row.get('total_rows', 0)} | "
            f"{row.get('file_path', '')} | {str(row.get('message', '')).replace('|', '/')} |"
        )
    DATA_DOWNLOAD_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def _write_update_log(results: list[dict], run_status: dict, estimated_api_calls: int = 0, dry_run: bool = False) -> None:
    counts = _status_counts(results)
    failed_count = counts.get("failed_error", 0)
    unsupported_count = counts.get("unsupported_or_empty", 0)
    no_new_count = counts.get("no_new_data", 0)
    pending_count = counts.get("pending_source_update", 0)
    added_rows = sum(int(row.get("backfill_rows", 0) or 0) + int(row.get("forward_rows", 0) or 0) for row in results)
    lines = [
        f"# ETF Data Update Log {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "本日志来自本机 BaoStock ETF 更新脚本；不接券商 API，不下单，不读取账号密码。",
        "",
        f"- Mode: {'dry-run' if dry_run else 'formal update'}",
        f"- Universe size: {len(results)}",
        f"- Estimated/actual BaoStock query calls: {estimated_api_calls}",
        f"- Status counts: {counts}",
        f"- Update severity: {run_status.get('severity')}",
        f"- Update status: {run_status.get('status')}",
        f"- Latest local date: {run_status.get('latest_local_date')}",
        f"- Reason: {run_status.get('reason')}",
        f"- True failed_error: {failed_count}",
        f"- Unsupported_or_empty: {unsupported_count}",
        f"- No_new_data: {no_new_count}",
        f"- Pending_source_update: {pending_count}",
        f"- Added rows: {added_rows}",
        "- Duplicate-date rule: existing local rows win during merge.",
    ]
    DATA_UPDATE_LOG_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _status_counts(results: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in results:
        status = str(row.get("status", "unknown") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _parse_symbols(value: list[str] | None) -> set[str] | None:
    if not value:
        return None
    parts: list[str] = []
    for raw in value:
        parts.extend(str(raw).replace("，", ",").split(","))
    return {item.strip() for item in parts if item.strip()}


def _normalize_date(value: str) -> str:
    return pd.to_datetime(value).strftime("%Y-%m-%d")


if __name__ == "__main__":
    main()
