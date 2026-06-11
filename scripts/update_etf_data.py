"""用 BaoStock 在用户本机下载 ETF 日线数据。

本脚本只下载公开行情并写入本地 CSV，不连接券商 API，不下单，
不读取账号、密码、验证码或任何交易账户信息。
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date
from pathlib import Path
import re
import signal
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DATA_DOWNLOAD_REPORT_FILE, DATA_UPDATE_LOG_FILE, ETF_DAILY_DIR, WATCHLIST_FILE  # noqa: E402
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="本机 BaoStock ETF 日线下载脚本")
    parser.add_argument("--start", default="2018-01-01", help="没有本地 CSV 时的默认起始日期，默认 2018-01-01。")
    parser.add_argument("--end", default=date.today().strftime("%Y-%m-%d"), help="结束日期，默认今天。")
    parser.add_argument("--symbols", nargs="*", help="只下载指定代码，可空格或逗号分隔，例如 510300 159915。")
    parser.add_argument("--all-etf", action="store_true", help="更新正式 data/etf_daily/ 中全部 ETF CSV，并合并 watchlist/candidate imported ETF。")
    parser.add_argument("--source", default="baostock", choices=["baostock"], help="数据源；当前仅支持 baostock。")
    parser.add_argument("--dry-run", action="store_true", help="只估算和报告，不调用 BaoStock，不写入 CSV。")
    parser.add_argument("--skip-existing", action="store_true", help="已有日期不重复下载；当前合并逻辑始终本地原行优先。")
    parser.add_argument("--skip-backfill", action="store_true", help="只补本地最新日期之后的数据，不反复尝试更早历史；适合 daily_close。")
    parser.add_argument("--max-api-calls", type=int, default=50000, help="每日最大 BaoStock 调用数，默认 50000。")
    parser.add_argument("--adjustflag", default="2", choices=["1", "2", "3"], help="复权类型：1 后复权，2 前复权，3 不复权；默认 2。")
    parser.add_argument("--request-timeout", type=int, default=20, help="单次 BaoStock 请求超时秒数，默认 20，避免网络等待卡住自动化。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start = _normalize_date(args.start)
    end = _normalize_date(args.end)
    symbols = _parse_symbols(args.symbols)

    watchlist = read_watchlist(WATCHLIST_FILE)
    items = _select_items(watchlist, symbols, all_etf=args.all_etf)
    ETF_DAILY_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DOWNLOAD_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    estimated_api_calls = _estimate_api_calls(items, start, end, skip_backfill=args.skip_backfill)
    if estimated_api_calls > args.max_api_calls:
        results.append({"code": "", "name": "", "status": "failed_error", "message": f"estimated_api_calls {estimated_api_calls} exceeds max_api_calls {args.max_api_calls}; stopped before BaoStock login."})
        _write_report(results, args.adjustflag, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
        _write_update_log(results, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
        raise SystemExit(f"estimated_api_calls {estimated_api_calls} exceeds max_api_calls {args.max_api_calls}")

    if _is_empty_items(items):
        results.append({"code": "", "name": "", "status": "unsupported_or_empty", "message": "没有匹配到可下载 ETF。"})
        _write_report(results, args.adjustflag, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
        _write_update_log(results, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
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
        _write_report(results, args.adjustflag, estimated_api_calls=estimated_api_calls, dry_run=True)
        _write_update_log(results, estimated_api_calls=estimated_api_calls, dry_run=True)
        print(f"ETF 数据下载 dry-run 完成：计划调用 {estimated_api_calls} 次，标的 {len(items)} 个。")
        print(f"已生成下载报告：{DATA_DOWNLOAD_REPORT_FILE}")
        return

    try:
        import baostock as bs
    except Exception as exc:
        results.append({"code": "", "name": "", "status": "failed_error", "message": f"BaoStock 导入失败：{exc}"})
        _write_report(results, args.adjustflag, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
        _write_update_log(results, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
        raise SystemExit("BaoStock 导入失败，请确认在本机 .venv 中已安装 baostock。")

    login_result = bs.login()
    if getattr(login_result, "error_code", "") != "0":
        message = f"BaoStock 登录失败：{getattr(login_result, 'error_msg', '')}"
        results.append({"code": "", "name": "", "status": "failed_error", "message": message})
        _write_report(results, args.adjustflag, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
        _write_update_log(results, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
        raise SystemExit(message)

    try:
        for _, item in items.iterrows():
            results.append(_download_one(bs, item, start, end, args.adjustflag, args.request_timeout, skip_backfill=args.skip_backfill))
    finally:
        bs.logout()

    _write_report(results, args.adjustflag, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
    _write_update_log(results, estimated_api_calls=estimated_api_calls, dry_run=args.dry_run)
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
    print(f"已生成下载报告：{DATA_DOWNLOAD_REPORT_FILE}")


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


def _write_report(results: list[dict], adjustflag: str, estimated_api_calls: int = 0, dry_run: bool = False) -> None:
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


def _write_update_log(results: list[dict], estimated_api_calls: int = 0, dry_run: bool = False) -> None:
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
