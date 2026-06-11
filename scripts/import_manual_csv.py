"""Import validated manual ETF CSV files into data/etf_daily.

The merge rule is conservative: if a manual row and an existing data/etf_daily
row share the same date, the existing row wins. This preserves BaoStock data
and only fills historical gaps.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WATCHLIST_FILE = PROJECT_ROOT / "watchlist.csv"
MANUAL_DIR = PROJECT_ROOT / "data" / "manual_import"
ETF_DAILY_DIR = PROJECT_ROOT / "data" / "etf_daily"
REPORT_FILE = PROJECT_ROOT / "reports" / "manual_import_report.md"
DEFAULT_SYMBOLS = ["510300", "159915", "515000"]

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
REQUIRED_MANUAL_FIELDS = ["date", "open", "high", "low", "close", "volume"]


@dataclass
class EtfItem:
    symbol: str
    name: str
    group: str
    pool: str
    baostock_code: str
    target_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import validated manual ETF CSV files into data/etf_daily.")
    parser.add_argument("--all-etf", action="store_true", help="Use all ETF symbols from watchlist.csv.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview the merge without writing data/etf_daily files.")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help="Symbols to import. Defaults to the three pilot ETF symbols.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    items = select_items(args)
    results = [import_one(item, dry_run=args.dry_run) for item in items]

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(build_report(results, dry_run=args.dry_run), encoding="utf-8")

    print(build_console_summary(results, dry_run=args.dry_run))


def select_items(args: argparse.Namespace) -> list[EtfItem]:
    watchlist = read_watchlist(WATCHLIST_FILE)
    if args.all_etf:
        return watchlist

    requested = _normalize_symbols(args.symbols or DEFAULT_SYMBOLS)
    by_symbol = {item.symbol: item for item in watchlist}
    items: list[EtfItem] = []
    for symbol in requested:
        items.append(by_symbol.get(symbol) or build_item(symbol, "", "", ""))
    return items


def read_watchlist(path: Path) -> list[EtfItem]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        items = []
        for row in reader:
            symbol = str(row.get("code", "")).strip()
            if not symbol:
                continue
            if str(row.get("type", "")).strip().upper() != "ETF":
                continue
            items.append(
                build_item(
                    symbol=symbol,
                    name=str(row.get("name", "")).strip(),
                    group=str(row.get("group", "")).strip(),
                    pool=str(row.get("role", "")).strip(),
                )
            )
    return items


def build_item(symbol: str, name: str, group: str, pool: str) -> EtfItem:
    prefix = market_prefix(symbol)
    return EtfItem(
        symbol=symbol,
        name=name,
        group=group,
        pool=pool,
        baostock_code=f"{prefix}.{symbol}",
        target_path=ETF_DAILY_DIR / f"{prefix}_{symbol}.csv",
    )


def import_one(item: EtfItem, dry_run: bool) -> dict:
    manual_path = MANUAL_DIR / f"{item.symbol}.csv"
    target_path = item.target_path
    if not manual_path.exists():
        return result_for(item, "failed", manual_path, target_path, message="manual CSV not found")
    if not target_path.exists():
        return result_for(item, "failed", manual_path, target_path, message="target etf_daily CSV not found")

    try:
        manual = read_manual_csv(manual_path, item.baostock_code)
        existing = read_existing_csv(target_path)
        overlap_dates = sorted(set(manual["date"]) & set(existing["date"]))
        merged = merge_preserve_existing(manual, existing)
    except Exception as exc:
        return result_for(item, "failed", manual_path, target_path, message=str(exc))

    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(target_path, index=False)

    old_start, old_end = date_range(existing)
    manual_start, manual_end = date_range(manual)
    new_start, new_end = date_range(merged)
    return result_for(
        item,
        "dry_run_ok" if dry_run else "imported",
        manual_path,
        target_path,
        old_rows=len(existing),
        manual_rows=len(manual),
        overlap_rows=len(overlap_dates),
        new_rows=len(merged),
        old_start=old_start,
        old_end=old_end,
        manual_start=manual_start,
        manual_end=manual_end,
        new_start=new_start,
        new_end=new_end,
        message="existing data wins on duplicate dates" if overlap_dates else "existing data wins on duplicate dates; no overlapping dates found",
    )


def read_manual_csv(path: Path, baostock_code: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    missing = [col for col in REQUIRED_MANUAL_FIELDS if col not in df.columns]
    if missing:
        raise ValueError(f"{path} missing required fields: {', '.join(missing)}")

    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["code"] = baostock_code
    for col in ["open", "high", "low", "close", "volume", "amount"]:
        out[col] = pd.to_numeric(df[col], errors="coerce") if col in df.columns else pd.NA

    out = out.dropna(subset=["date", "open", "high", "low", "close", "volume"])
    if out.empty:
        raise ValueError(f"{path} has no valid rows")
    if (out[["open", "high", "low", "close", "volume"]] <= 0).any().any():
        raise ValueError(f"{path} contains non-positive OHLC or volume values")
    if (out["high"] < out["low"]).any():
        raise ValueError(f"{path} contains high < low rows")

    out = out.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    out["preclose"] = out["close"].shift(1)
    out["adjustflag"] = "1"
    out["turn"] = pd.NA
    out["tradestatus"] = "1"
    out["pctChg"] = ((out["close"] / out["preclose"] - 1) * 100).round(4)
    out.loc[out["preclose"].isna(), "pctChg"] = pd.NA
    out["isST"] = "1"
    return out[BAOSTOCK_FIELDS]


def read_existing_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"code": str})
    for col in BAOSTOCK_FIELDS:
        if col not in df.columns:
            df[col] = pd.NA
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
    return df[BAOSTOCK_FIELDS].reset_index(drop=True)


def merge_preserve_existing(manual: pd.DataFrame, existing: pd.DataFrame) -> pd.DataFrame:
    merged = pd.concat([manual[BAOSTOCK_FIELDS], existing[BAOSTOCK_FIELDS]], ignore_index=True)
    merged["date"] = pd.to_datetime(merged["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    merged = merged.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
    return merged[BAOSTOCK_FIELDS].reset_index(drop=True)


def build_console_summary(results: list[dict], dry_run: bool) -> str:
    mode = "dry-run" if dry_run else "import"
    success_count = sum(1 for row in results if row["status"] != "failed")
    failed_count = len(results) - success_count
    lines = [f"manual CSV {mode} finished: success {success_count}, failed {failed_count}"]
    for row in results:
        lines.append(
            "{symbol}: {status}, old_rows={old_rows}, manual_rows={manual_rows}, overlap_rows={overlap_rows}, "
            "new_rows={new_rows}, range={new_start} to {new_end}, target={target_rel}, message={message}".format(**row)
        )
    lines.append(f"report written: {REPORT_FILE}")
    return "\n".join(lines)


def build_report(results: list[dict], dry_run: bool) -> str:
    success_count = sum(1 for row in results if row["status"] != "failed")
    failed_count = len(results) - success_count
    lines = [
        "# 手工 CSV 导入报告",
        "",
        f"- 模式：{'dry-run' if dry_run else '正式导入'}",
        f"- 预计成功：{success_count}",
        f"- 失败：{failed_count}",
        "- 数据来源：`data/manual_import/`",
        "- 写入目录：`data/etf_daily/`",
        "- 合并规则：日期重复时保留 `data/etf_daily/` 原有行，避免覆盖 BaoStock 近期数据。",
        "- dry-run：不写入 `data/etf_daily/`" if dry_run else "- 正式导入：已写入 `data/etf_daily/`",
        "- 券商 API：未使用",
        "- 账号密码：未读取",
        "- 真实下单：未执行",
        "- 自动交易：未执行",
        "- 策略逻辑：未修改",
        "",
        "| 代码 | 名称 | group | pool | 状态 | 原行数 | 手工行数 | 重叠日期数 | 合并后行数 | 原日期范围 | 手工日期范围 | 合并后日期范围 | 目标文件 | 说明 |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for row in results:
        lines.append(
            "| {symbol} | {name} | {group} | {pool} | {status} | {old_rows} | {manual_rows} | {overlap_rows} | {new_rows} | "
            "{old_start} to {old_end} | {manual_start} to {manual_end} | {new_start} to {new_end} | `{target_rel}` | {message} |".format(
                **row
            )
        )
    return "\n".join(lines) + "\n"


def result_for(
    item: EtfItem,
    status: str,
    manual_path: Path,
    target_path: Path,
    message: str,
    old_rows: int = 0,
    manual_rows: int = 0,
    overlap_rows: int = 0,
    new_rows: int = 0,
    old_start: str = "",
    old_end: str = "",
    manual_start: str = "",
    manual_end: str = "",
    new_start: str = "",
    new_end: str = "",
) -> dict:
    return {
        "symbol": item.symbol,
        "name": escape(item.name),
        "group": escape(item.group),
        "pool": escape(item.pool),
        "status": status,
        "message": escape(message),
        "target_path": str(target_path),
        "target_rel": relative(target_path),
        "manual_path": str(manual_path),
        "manual_rel": relative(manual_path),
        "old_rows": old_rows,
        "manual_rows": manual_rows,
        "overlap_rows": overlap_rows,
        "new_rows": new_rows,
        "old_start": old_start,
        "old_end": old_end,
        "manual_start": manual_start,
        "manual_end": manual_end,
        "new_start": new_start,
        "new_end": new_end,
    }


def date_range(df: pd.DataFrame) -> tuple[str, str]:
    if df.empty or "date" not in df.columns:
        return "", ""
    dates = pd.to_datetime(df["date"], errors="coerce").dropna()
    if dates.empty:
        return "", ""
    return dates.min().strftime("%Y-%m-%d"), dates.max().strftime("%Y-%m-%d")


def market_prefix(code: str) -> str:
    text = str(code).strip()
    if text.startswith(("6", "510", "511", "512", "513", "515", "516", "518", "588")):
        return "sh"
    if text.startswith(("0", "3", "159")):
        return "sz"
    return "sh"


def _normalize_symbols(values: list[str]) -> list[str]:
    symbols: list[str] = []
    for value in values:
        for part in value.split(","):
            symbol = part.strip()
            if symbol:
                symbols.append(symbol)
    return symbols


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def escape(value: str) -> str:
    return str(value).replace("|", "/")


if __name__ == "__main__":
    main()
