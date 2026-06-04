"""用 BaoStock 在用户本机下载 ETF 日线数据。

本脚本只下载公开行情并写入本地 CSV，不连接券商 API，不下单，
不读取账号、密码、验证码或任何交易账户信息。
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DATA_DOWNLOAD_REPORT_FILE, ETF_DAILY_DIR, WATCHLIST_FILE  # noqa: E402
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
    parser.add_argument("--symbols", help="只下载指定代码，逗号分隔，例如 510300,159915。")
    parser.add_argument("--adjustflag", default="2", choices=["1", "2", "3"], help="复权类型：1 后复权，2 前复权，3 不复权；默认 2。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start = _normalize_date(args.start)
    end = _normalize_date(args.end)
    symbols = _parse_symbols(args.symbols)

    watchlist = read_watchlist(WATCHLIST_FILE)
    items = _select_items(watchlist, symbols)
    ETF_DAILY_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DOWNLOAD_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    if _is_empty_items(items):
        results.append({"code": "", "name": "", "status": "failed", "message": "没有匹配到可下载 ETF。"})
        _write_report(results, args.adjustflag)
        print(f"未匹配到可下载 ETF，已生成报告：{DATA_DOWNLOAD_REPORT_FILE}")
        return

    try:
        import baostock as bs
    except Exception as exc:
        results.append({"code": "", "name": "", "status": "failed", "message": f"BaoStock 导入失败：{exc}"})
        _write_report(results, args.adjustflag)
        raise SystemExit("BaoStock 导入失败，请确认在本机 .venv 中已安装 baostock。")

    login_result = bs.login()
    if getattr(login_result, "error_code", "") != "0":
        message = f"BaoStock 登录失败：{getattr(login_result, 'error_msg', '')}"
        results.append({"code": "", "name": "", "status": "failed", "message": message})
        _write_report(results, args.adjustflag)
        raise SystemExit(message)

    try:
        for _, item in items.iterrows():
            results.append(_download_one(bs, item, start, end, args.adjustflag))
    finally:
        bs.logout()

    _write_report(results, args.adjustflag)
    success_count = sum(1 for row in results if row.get("status") != "failed")
    failed_count = sum(1 for row in results if row.get("status") == "failed")
    print(f"ETF 数据下载完成：成功/已有 {success_count} 个，失败 {failed_count} 个。")
    print(f"已生成下载报告：{DATA_DOWNLOAD_REPORT_FILE}")


def _select_items(watchlist: pd.DataFrame, symbols: set[str] | None) -> pd.DataFrame:
    df = watchlist.copy()
    df["code"] = df["code"].astype(str).str.strip()
    if symbols:
        df = df[df["code"].isin(symbols)]
    pool_mask = df["role"].isin(["trade_pool", "observe_pool"])
    etf_mask = df["type"].astype(str).str.upper() == "ETF"
    return df[pool_mask & etf_mask].copy()


def _is_empty_items(items: object) -> bool:
    if items is None:
        return True
    if isinstance(items, pd.DataFrame):
        return items.empty
    if isinstance(items, (list, dict, tuple, set)):
        return len(items) == 0
    return False


def _download_one(bs: object, item: pd.Series, default_start: str, end: str, adjustflag: str) -> dict:
    code = str(item["code"]).strip()
    name = str(item.get("name", code)).strip()
    bs_code = baostock_code(code)
    output_path = ETF_DAILY_DIR / f"{bs_code.replace('.', '_')}.csv"
    old = _read_existing(output_path)
    ranges = _download_ranges(old, default_start, end)
    if not ranges:
        return _result(
            item,
            bs_code,
            output_path,
            "already_up_to_date",
            old,
            requested_start=default_start,
            requested_end=end,
            message="本地 CSV 已覆盖本次 start/end 范围。",
        )

    backfill_frames: list[pd.DataFrame] = []
    forward_frames: list[pd.DataFrame] = []
    messages: list[str] = []
    for range_start, range_end, range_mode in ranges:
        fetched, message = _query_baostock_daily(bs, bs_code, range_start, range_end, adjustflag)
        messages.append(f"{range_mode} {range_start}~{range_end}: {message}")
        if fetched is not None and not fetched.empty:
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
        return _result(
            item,
            bs_code,
            output_path,
            "failed",
            old,
            requested_start=default_start,
            requested_end=end,
            backfill_needed=any(item[2] == "backfill" for item in ranges),
            forward_needed=any(item[2] == "forward" for item in ranges),
            message="需要下载缺口，但 BaoStock 未返回可合并的新数据；" + "；".join(messages),
        )

    merged = _merge_daily(old, backfill_new, forward_new)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    if backfill_rows > 0 and forward_rows > 0:
        status = "backfilled_and_forward_updated"
    elif backfill_rows > 0:
        status = "backfilled"
    else:
        status = "forward_updated"
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
        message="；".join(messages) + "；保存成功。",
    )


def _download_ranges(old: pd.DataFrame | None, default_start: str, end: str) -> list[tuple[str, str, str]]:
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
    if first_date > requested_start and requested_start <= backward_end:
        ranges.append((requested_start.strftime("%Y-%m-%d"), backward_end.strftime("%Y-%m-%d"), "backfill"))

    forward_start = last_date + pd.Timedelta(days=1)
    if last_date < requested_end and forward_start <= requested_end:
        ranges.append((forward_start.strftime("%Y-%m-%d"), requested_end.strftime("%Y-%m-%d"), "forward"))

    return ranges


def _query_baostock_daily(bs: object, bs_code: str, start: str, end: str, adjustflag: str) -> tuple[pd.DataFrame | None, str]:
    try:
        rs = bs.query_history_k_data_plus(
            bs_code,
            ",".join(BAOSTOCK_FIELDS),
            start_date=start,
            end_date=end,
            frequency="d",
            adjustflag=adjustflag,
        )
    except Exception as exc:
        return None, f"BaoStock 请求异常：{exc}"

    if getattr(rs, "error_code", "") != "0":
        return None, f"BaoStock 返回错误：{getattr(rs, 'error_msg', '')}"

    rows = []
    while rs.next():
        rows.append(rs.get_row_data())
    if not rows:
        return pd.DataFrame(columns=BAOSTOCK_FIELDS), "返回空数据"
    return pd.DataFrame(rows, columns=BAOSTOCK_FIELDS), f"返回 {len(rows)} 行"


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
    merged = merged.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
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


def _write_report(results: list[dict], adjustflag: str) -> None:
    lines = [
        f"# ETF 本机数据下载报告 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "本报告来自本机 BaoStock ETF 下载脚本。脚本只下载行情数据，不接券商 API，不下单，不读取账号密码。",
        "",
        f"- 保存目录：`data/etf_daily/`",
        f"- 复权参数 adjustflag：{adjustflag}",
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


def _parse_symbols(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {item.strip() for item in value.replace("，", ",").split(",") if item.strip()}


def _normalize_date(value: str) -> str:
    return pd.to_datetime(value).strftime("%Y-%m-%d")


if __name__ == "__main__":
    main()
