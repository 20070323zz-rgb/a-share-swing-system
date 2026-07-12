"""Download manual ETF daily history from public Eastmoney quote data.

This script only fetches public historical K-line data and writes CSV files
under data/manual_import/. It does not connect to broker APIs, does not read
account credentials, and does not place orders.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import ssl
import subprocess
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WATCHLIST_FILE = PROJECT_ROOT / "watchlist.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "manual_import"
DEFAULT_REPORT_FILE = PROJECT_ROOT / "reports" / "manual_download_report.md"
EASTMONEY_KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
DEFAULT_SYMBOLS = ["510300", "159915", "515000"]
CSV_COLUMNS = ["date", "open", "high", "low", "close", "volume", "amount"]


@dataclass
class EtfItem:
    symbol: str
    name: str
    group: str
    pool: str
    market: str


@dataclass
class DownloadResult:
    symbol: str
    name: str
    group: str
    pool: str
    source: str
    status: str
    retry_count: int = 0
    skipped_existing: bool = False
    row_count: int = 0
    start_date: str = ""
    end_date: str = ""
    output_path: str = ""
    failure_reason: str = ""
    errors: list[str] | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download manual ETF history CSV files from Eastmoney.")
    parser.add_argument("--all-etf", action="store_true", help="Download all ETF symbols from watchlist.csv.")
    parser.add_argument("--failed-only", action="store_true", help="Only retry missing or previously failed ETF CSV files.")
    parser.add_argument("--start", default="2022-01-01", help="Start date, YYYY-MM-DD.")
    parser.add_argument("--end", default="2026-01-04", help="End date, YYYY-MM-DD.")
    parser.add_argument("--retry", type=int, default=3, help="Number of retries after the first failed attempt. Default: 3.")
    parser.add_argument("--delay", type=float, default=1.5, help="Seconds to sleep between symbols and before retries. Default: 1.5.")
    parser.add_argument("--batch-size", type=int, default=None, help="Only process the first N selected ETF symbols.")
    parser.add_argument("--skip-existing", dest="skip_existing", action="store_true", default=True, help="Skip existing non-empty manual CSV files. Default: true.")
    parser.add_argument("--no-skip-existing", dest="skip_existing", action="store_false", help="Do not skip existing manual CSV files.")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help="ETF symbols to download, for example: --symbols 510300 159915 515000",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for CSV files.")
    parser.add_argument("--report-file", default=str(DEFAULT_REPORT_FILE), help="Markdown download report path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start = _normalize_date(args.start)
    end = _normalize_date(args.end)
    output_dir = Path(args.output_dir)
    report_file = Path(args.report_file)
    items = select_items(args, output_dir, report_file)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_file.parent.mkdir(parents=True, exist_ok=True)

    results: list[DownloadResult] = []
    for index, item in enumerate(items):
        results.append(download_item(item, start, end, output_dir, retry=args.retry, delay=args.delay, skip_existing=args.skip_existing))
        if args.delay > 0 and index < len(items) - 1:
            time.sleep(args.delay)
    write_report(results, report_file, start, end, output_dir)

    success_count = sum(1 for result in results if result.status == "success")
    skipped_count = sum(1 for result in results if result.status == "skipped_existing")
    failed_count = sum(1 for result in results if result.status == "failed")
    print(f"manual ETF history download finished: success {success_count}, skipped {skipped_count}, failed {failed_count}")
    print(f"report written: {report_file}")


def select_items(args: argparse.Namespace, output_dir: Path, report_file: Path) -> list[EtfItem]:
    watchlist = read_watchlist(WATCHLIST_FILE)
    if args.all_etf:
        items = watchlist
    else:
        requested = _normalize_symbols(args.symbols or DEFAULT_SYMBOLS)
        by_symbol = {item.symbol: item for item in watchlist}
        items = []
        for symbol in requested:
            items.append(by_symbol.get(symbol) or EtfItem(symbol=symbol, name="", group="", pool="", market=market_id(symbol)))
    if args.failed_only:
        previous_failed = read_previous_failed_symbols(report_file)
        items = [item for item in items if should_retry_item(item, output_dir, previous_failed)]
    if args.batch_size is not None and args.batch_size > 0:
        items = items[: args.batch_size]
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
                EtfItem(
                    symbol=symbol,
                    name=str(row.get("name", "")).strip(),
                    group=str(row.get("group", "")).strip(),
                    pool=str(row.get("role", "")).strip(),
                    market=market_id(symbol),
                )
            )
    return items


def download_item(item: EtfItem, start: str, end: str, output_dir: Path, retry: int, delay: float, skip_existing: bool) -> DownloadResult:
    output_path = output_dir / f"{item.symbol}.csv"
    result = DownloadResult(
        symbol=item.symbol,
        name=item.name,
        group=item.group,
        pool=item.pool,
        source="Eastmoney push2his historical K-line",
        status="failed",
        output_path=str(output_path),
        errors=[],
    )
    if skip_existing and existing_nonempty_csv(output_path):
        result.status = "skipped_existing"
        result.skipped_existing = True
        result.row_count, result.start_date, result.end_date = csv_summary(output_path)
        return result

    max_retries = max(0, retry)
    attempts = max_retries + 1
    rows: list[dict[str, str]] = []
    for attempt in range(1, attempts + 1):
        try:
            payload = fetch_eastmoney(item.symbol, item.market, start, end)
            rows = parse_klines(payload)
            if rows:
                break
            message = "source returned no K-line rows"
        except Exception as exc:
            message = str(exc)
        result.failure_reason = message
        result.errors = (result.errors or []) + [f"attempt {attempt}: {message}"]
        if attempt < attempts and delay > 0:
            time.sleep(delay)
    result.retry_count = max(0, len(result.errors or []) - 1)

    if not rows:
        return result

    rows = merge_existing_history(output_path, rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    result.status = "success"
    result.failure_reason = ""
    result.row_count = len(rows)
    result.start_date = rows[0]["date"]
    result.end_date = rows[-1]["date"]
    return result


def merge_existing_history(path: Path, downloaded_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Preserve existing dates when a narrow-range refresh writes the cache.

    A caller may intentionally use ``--no-skip-existing`` to fetch a missing
    day. That must extend the manual cache instead of replacing its complete
    history with the requested slice. Freshly downloaded rows win only on an
    overlapping date.
    """
    by_date: dict[str, dict[str, str]] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames and set(CSV_COLUMNS).issubset(reader.fieldnames):
                for row in reader:
                    date = str(row.get("date", "")).strip()
                    if date:
                        by_date[date] = {column: str(row.get(column, "")) for column in CSV_COLUMNS}

    for row in downloaded_rows:
        date = str(row.get("date", "")).strip()
        if date:
            by_date[date] = {column: str(row.get(column, "")) for column in CSV_COLUMNS}
    return [by_date[date] for date in sorted(by_date)]


def fetch_eastmoney(symbol: str, market: str, start: str, end: str) -> dict[str, Any]:
    params = {
        "secid": f"{market}.{symbol}",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "1",
        "beg": start.replace("-", ""),
        "end": end.replace("-", ""),
    }
    url = f"{EASTMONEY_KLINE_URL}?{urlencode(params)}"
    raw = fetch_url_with_curl(url)
    if raw is None:
        raw = fetch_url_with_urllib(url)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON response: {exc}") from exc

    if payload.get("rc") != 0:
        raise RuntimeError(f"source returned rc={payload.get('rc')}: {payload.get('rt')}")
    if not payload.get("data"):
        raise RuntimeError("source returned empty data")
    return payload


def fetch_url_with_curl(url: str) -> str | None:
    command = [
        "curl",
        "-4",
        "--silent",
        "--show-error",
        "--fail",
        "--connect-timeout",
        "10",
        "--max-time",
        "30",
        "-H",
        "User-Agent: Mozilla/5.0 manual-etf-history-downloader",
        "-H",
        "Referer: https://quote.eastmoney.com/",
        "-H",
        "Accept: application/json,text/plain,*/*",
        url,
    ]
    try:
        completed = subprocess.run(command, check=False, text=True, capture_output=True)
    except FileNotFoundError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def fetch_url_with_urllib(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 manual-etf-history-downloader",
            "Referer": "https://quote.eastmoney.com/",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    try:
        with urlopen(request, timeout=20, context=_ssl_context()) as response:
            return response.read().decode("utf-8")
    except HTTPError as exc:
        raise RuntimeError(f"HTTP error {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"network error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError("network timeout") from exc


def parse_klines(payload: dict[str, Any]) -> list[dict[str, str]]:
    klines = payload.get("data", {}).get("klines") or []
    rows: list[dict[str, str]] = []
    for line in klines:
        parts = str(line).split(",")
        if len(parts) < 7:
            continue
        rows.append(
            {
                "date": parts[0],
                "open": parts[1],
                "high": parts[3],
                "low": parts[4],
                "close": parts[2],
                "volume": parts[5],
                "amount": parts[6],
            }
        )
    return rows


def write_report(results: list[DownloadResult], report_file: Path, start: str, end: str, output_dir: Path) -> None:
    lines = [
        "# Manual ETF History Download Report",
        "",
        f"- Requested range: {start} to {end}",
        f"- Output directory: {output_dir}",
        "- Broker API: not used",
        "- Account credentials: not read",
        "- Real orders: not placed",
        "- Auto trading: not used",
        "- Strategy logic: not modified",
        "- data/etf_daily: not written",
        "",
        "| Symbol | Name | Group | Pool | Final Status | Retry Count | Skipped Existing | Rows | Start Date | End Date | Output Path | Error Message | Failure Attempts |",
        "|---|---|---|---|---|---:|---|---:|---|---|---|---|---|",
    ]
    for result in results:
        lines.append(
            "| {symbol} | {name} | {group} | {pool} | {status} | {retry_count} | {skipped} | {rows} | {start_date} | {end_date} | {output} | {failure} | {errors} |".format(
                symbol=result.symbol,
                name=_escape(result.name),
                group=_escape(result.group),
                pool=_escape(result.pool),
                status=result.status,
                retry_count=result.retry_count,
                skipped="yes" if result.skipped_existing else "no",
                rows=result.row_count,
                start_date=result.start_date,
                end_date=result.end_date,
                output=_relative(result.output_path),
                failure=_escape(result.failure_reason),
                errors=_escape("; ".join(result.errors or [])),
            )
        )

    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_previous_failed_symbols(report_file: Path) -> set[str]:
    if not report_file.exists():
        return set()
    failed: set[str] = set()
    try:
        lines = report_file.read_text(encoding="utf-8").splitlines()
    except Exception:
        return set()
    for line in lines:
        if not line.startswith("|"):
            continue
        cols = [col.strip() for col in line.strip().strip("|").split("|")]
        if len(cols) < 5 or cols[0] in {"Symbol", "---"}:
            continue
        symbol = cols[0]
        status = cols[4].lower()
        if status == "failed":
            failed.add(symbol)
    return failed


def should_retry_item(item: EtfItem, output_dir: Path, previous_failed: set[str]) -> bool:
    output_path = output_dir / f"{item.symbol}.csv"
    if existing_valid_csv(output_path):
        return False
    if not output_path.exists() or not existing_nonempty_csv(output_path):
        return True
    return item.symbol in previous_failed


def existing_nonempty_csv(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    rows, _, _ = csv_summary(path)
    return rows > 0


def existing_valid_csv(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                return False
            required = {"date", "open", "high", "low", "close", "volume"}
            if not required.issubset(set(reader.fieldnames)):
                return False
            rows = [row for row in reader]
    except Exception:
        return False
    if not rows:
        return False
    dates = [row.get("date", "") for row in rows]
    try:
        _normalize_date(dates[0])
        _normalize_date(dates[-1])
    except Exception:
        return False
    return True


def csv_summary(path: Path) -> tuple[int, str, str]:
    try:
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            dates = [row.get("date", "") for row in reader if row.get("date", "")]
    except Exception:
        return 0, "", ""
    if not dates:
        return 0, "", ""
    return len(dates), dates[0], dates[-1]


def market_prefix(code: str) -> str:
    text = str(code).strip()
    if text.startswith(("6", "510", "511", "512", "513", "515", "516", "518", "588")):
        return "sh"
    if text.startswith(("0", "3", "159")):
        return "sz"
    return "sh"


def market_id(code: str) -> str:
    return "1" if market_prefix(code) == "sh" else "0"


def _normalize_date(value: str) -> str:
    return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")


def _normalize_symbols(values: list[str]) -> list[str]:
    symbols: list[str] = []
    for value in values:
        for part in value.split(","):
            symbol = part.strip()
            if symbol:
                symbols.append(symbol)
    return symbols


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def _relative(path: str) -> str:
    path_obj = Path(path)
    try:
        return str(path_obj.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path_obj)


def _escape(value: str) -> str:
    return str(value).replace("|", "/")


if __name__ == "__main__":
    main()
