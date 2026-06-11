"""Safely test JQData ETF daily data availability on the local machine.

This script only validates read-only JQData market data access. It does not
connect to broker APIs, does not place orders, does not read broker accounts,
does not save credentials, and never writes to data/etf_daily/.

Credentials are read only from environment variables:
  JQDATA_USER
  JQDATA_PASSWORD
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import os
from pathlib import Path
from types import ModuleType
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "staging" / "jqdata"
DEFAULT_REPORT_FILE = PROJECT_ROOT / "reports" / "jqdata_test_report.md"
WATCHLIST_FILE = PROJECT_ROOT / "watchlist.csv"
DEFAULT_SYMBOLS = ["510300.XSHG", "159915.XSHE", "515000.XSHG"]
DEFAULT_START = "2025-03-01"
DEFAULT_END = "2026-03-01"
JQ_FIELDS = ["open", "high", "low", "close", "volume", "money"]
REQUIRED_IMPORT_FIELDS = ["date", "open", "high", "low", "close", "volume"]


@dataclass
class EtfRequest:
    symbol: str
    jq_symbol: str


@dataclass
class TestResult:
    symbol: str
    jq_symbol: str
    status: str
    rows: int = 0
    start_date: str = ""
    end_date: str = ""
    fields: str = ""
    required_fields_ok: bool = False
    fallback_used: bool = False
    output_path: str = ""
    failure_reason: str = ""
    recommend_backfill_candidate: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test JQData ETF daily data access safely.")
    parser.add_argument("--all-etf", action="store_true", help="Read all type=ETF symbols from watchlist.csv.")
    parser.add_argument("--start", default=DEFAULT_START, help="Start date, YYYY-MM-DD. Default: 2025-03-01.")
    parser.add_argument("--end", default=DEFAULT_END, help="End date, YYYY-MM-DD. Default: 2026-03-01.")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help="ETF symbols to test, accepting formats like sh_510300, 510300, 510300.SH, or 510300.XSHG.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="CSV output directory. Must not be data/etf_daily/.")
    parser.add_argument("--report-file", default=str(DEFAULT_REPORT_FILE), help="Markdown report file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    report_file = Path(args.report_file).resolve()
    ensure_safe_paths(output_dir, report_file)

    start = normalize_date(args.start)
    end = normalize_date(args.end)
    requests = select_requests(args)

    jq, import_ok, sdk_version, import_error = import_jqdata()
    user_present = bool(os.environ.get("JQDATA_USER"))
    password_present = bool(os.environ.get("JQDATA_PASSWORD"))

    auth_ok = False
    auth_message = ""
    results: list[TestResult]

    if not import_ok:
        auth_message = "jqdatasdk is not installed. Install with: python3 -m pip install jqdatasdk"
        results = [
            build_failed_result(item, output_dir, "import_failed", import_error)
            for item in requests
        ]
        write_report(report_file, import_ok, sdk_version, user_present, password_present, auth_ok, auth_message, start, end, output_dir, results)
        print("jqdatasdk is not installed.")
        print("Install it on this machine with: python3 -m pip install jqdatasdk")
        print(f"report written: {report_file}")
        return

    if not user_present or not password_present:
        auth_message = (
            "JQData credential environment variables are not fully set. "
            "Set the account and password environment variables in your terminal before running the test."
        )
        results = [
            build_failed_result(item, output_dir, "missing_env", "JQData environment variables are missing.")
            for item in requests
        ]
        write_report(report_file, import_ok, sdk_version, user_present, password_present, auth_ok, auth_message, start, end, output_dir, results)
        print("JQData credentials were not found in environment variables.")
        print("Set the JQData account and password environment variables in your terminal before running the test.")
        print(f"report written: {report_file}")
        return

    auth_ok, auth_message = authenticate(jq)
    if not auth_ok:
        results = [
            build_failed_result(item, output_dir, "auth_failed", auth_message)
            for item in requests
        ]
        write_report(report_file, import_ok, sdk_version, user_present, password_present, auth_ok, auth_message, start, end, output_dir, results)
        print("JQData authentication failed. Check JQDATA_USER/JQDATA_PASSWORD in your terminal environment.")
        print(f"report written: {report_file}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    results = [fetch_one(jq, item, start, end, output_dir) for item in requests]
    write_report(report_file, import_ok, sdk_version, user_present, password_present, auth_ok, auth_message, start, end, output_dir, results)
    success_count = sum(1 for result in results if result.status == "success")
    failed_count = len(results) - success_count
    print(f"JQData ETF daily test finished: success {success_count}, failed {failed_count}")
    print(f"report written: {report_file}")


def ensure_safe_paths(output_dir: Path, report_file: Path) -> None:
    etf_daily_dir = (PROJECT_ROOT / "data" / "etf_daily").resolve()
    if output_dir == etf_daily_dir or etf_daily_dir in output_dir.parents:
        raise SystemExit("Refusing to write JQData test output under data/etf_daily/. Use data/staging/jqdata/.")
    if not is_relative_to(output_dir, PROJECT_ROOT):
        raise SystemExit("Refusing to write JQData test output outside the project.")
    if not is_relative_to(report_file, PROJECT_ROOT):
        raise SystemExit("Refusing to write JQData test report outside the project.")


def import_jqdata() -> tuple[ModuleType | None, bool, str, str]:
    try:
        import jqdatasdk as jq
    except Exception as exc:
        return None, False, "", str(exc)
    return jq, True, str(getattr(jq, "__version__", "unknown")), ""


def build_failed_result(item: EtfRequest, output_dir: Path, status: str, reason: str) -> TestResult:
    return TestResult(
        symbol=item.symbol,
        jq_symbol=item.jq_symbol,
        status=status,
        output_path=relative(output_dir / f"{item.jq_symbol}.csv"),
        failure_reason=reason,
    )


def authenticate(jq: ModuleType) -> tuple[bool, str]:
    user = os.environ.get("JQDATA_USER", "")
    password = os.environ.get("JQDATA_PASSWORD", "")
    try:
        jq.auth(user, password)
        is_auth = getattr(jq, "is_auth", None)
        if callable(is_auth) and not is_auth():
            return False, "jqdatasdk auth returned, but is_auth() is false."
        return True, "authentication succeeded."
    except Exception as exc:
        return False, f"authentication failed: {exc}"


def fetch_one(jq: ModuleType, item: EtfRequest, start: str, end: str, output_dir: Path) -> TestResult:
    output_path = output_dir / f"{item.jq_symbol}.csv"
    result = TestResult(symbol=item.symbol, jq_symbol=item.jq_symbol, status="failed", output_path=relative(output_path))
    try:
        raw = get_price(jq, item.jq_symbol, start, end)
        df = normalize_price(raw)
    except Exception as first_exc:
        fallback_start, fallback_end = trial_fallback_range(start, end)
        if fallback_start > fallback_end:
            result.failure_reason = f"initial request failed and no fallback range is available: {first_exc}"
            return result
        try:
            raw = get_price(jq, item.jq_symbol, fallback_start, fallback_end)
            df = normalize_price(raw)
            result.fallback_used = True
        except Exception as second_exc:
            result.failure_reason = f"initial request failed: {first_exc}; fallback request failed: {second_exc}"
            return result

    if df.empty:
        result.failure_reason = "JQData returned no daily rows."
        return result

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    result.status = "success"
    result.rows = len(df)
    result.start_date = str(df["date"].iloc[0])
    result.end_date = str(df["date"].iloc[-1])
    result.fields = ", ".join(df.columns)
    result.required_fields_ok = all(field in df.columns for field in REQUIRED_IMPORT_FIELDS)
    result.recommend_backfill_candidate = result.required_fields_ok and result.rows > 0
    return result


def get_price(jq: ModuleType, symbol: str, start: str, end: str) -> Any:
    return jq.get_price(
        symbol,
        start_date=start,
        end_date=end,
        frequency="daily",
        fields=JQ_FIELDS,
        skip_paused=False,
        fq="pre",
    )


def normalize_price(raw: Any) -> pd.DataFrame:
    df = pd.DataFrame(raw).copy()
    if df.empty:
        return pd.DataFrame(columns=["date", *JQ_FIELDS])
    if "date" not in df.columns:
        df["date"] = pd.Series(df.index, index=df.index)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for column in JQ_FIELDS:
        if column not in df.columns:
            df[column] = pd.NA
    for column in JQ_FIELDS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df[["date", *JQ_FIELDS]].dropna(subset=["date", "open", "high", "low", "close"])
    df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    return df


def trial_fallback_range(start: str, end: str) -> tuple[str, str]:
    requested_start = datetime.strptime(start, "%Y-%m-%d").date()
    requested_end = datetime.strptime(end, "%Y-%m-%d").date()
    today = date.today()
    allowed_start = subtract_months(today, 15)
    allowed_end = subtract_months(today, 3) - timedelta(days=1)
    fallback_start = max(requested_start, allowed_start)
    fallback_end = min(requested_end, allowed_end)
    if (fallback_end - fallback_start).days > 365:
        fallback_start = fallback_end - timedelta(days=365)
    return fallback_start.strftime("%Y-%m-%d"), fallback_end.strftime("%Y-%m-%d")


def subtract_months(value: date, months: int) -> date:
    month_index = value.month - 1 - months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, days_in_month(year, month))
    return date(year, month, day)


def days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day


def write_report(
    report_file: Path,
    import_ok: bool,
    sdk_version: str,
    user_present: bool,
    password_present: bool,
    auth_ok: bool,
    auth_message: str,
    start: str,
    end: str,
    output_dir: Path,
    results: list[TestResult],
) -> None:
    report_file.parent.mkdir(parents=True, exist_ok=True)
    success_count = sum(1 for result in results if result.status == "success")
    failed_count = len(results) - success_count
    candidate_count = sum(1 for result in results if result.recommend_backfill_candidate)
    success_ranges = {(result.start_date, result.end_date) for result in results if result.status == "success"}
    success_range_consistent = len(success_ranges) <= 1 and success_count > 0
    all_success_fields_ok = all(result.required_fields_ok for result in results if result.status == "success") and success_count > 0
    lines = [
        "# JQData ETF 日线本机可用性测试报告",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- jqdatasdk import：{'成功' if import_ok else '失败'}",
        f"- jqdatasdk 版本：{sdk_version or '未检测到'}",
        f"- 检测到账号环境变量：{'是' if user_present else '否'}",
        f"- 检测到密码环境变量：{'是' if password_present else '否'}",
        f"- 认证成功：{'是' if auth_ok else '否'}",
        f"- 测试区间：{start} 到 {end}",
        f"- 输出目录：`{relative(output_dir)}`",
        f"- 选中 ETF 数：{len(results)}",
        f"- 成功返回数据 ETF 数：{success_count}",
        f"- 失败 ETF 数：{failed_count}",
        f"- 成功数据日期范围一致：{'是' if success_range_consistent else '否'}",
        f"- 成功数据字段均满足项目标准：{'是' if all_success_fields_ok else '否'}",
        f"- 建议作为历史补齐候选源 ETF 数：{candidate_count}",
        "- 安全边界：不接券商 API；不真实下单；不读取券商账号；不保存任何密码；不自动交易；不写入 `data/etf_daily/`。",
        "",
        "## 认证与环境",
        "",
        f"- 认证/环境说明：{escape_text(auth_message)}",
        "",
        "## ETF 结果",
        "",
        "| symbol | jq_symbol | status | rows | start_date | end_date | fields | required_fields_ok | fallback_used | failure_reason | recommend_backfill_candidate | output_path |",
        "|---|---|---:|---:|---|---|---|---:|---:|---|---:|---|",
    ]
    for result in results:
        lines.append(
            "| {symbol} | {jq_symbol} | {status} | {rows} | {start_date} | {end_date} | {fields} | {required} | {fallback} | {reason} | {candidate} | `{output}` |".format(
                symbol=escape_table(result.symbol),
                jq_symbol=escape_table(result.jq_symbol),
                status=escape_table(result.status),
                rows=result.rows,
                start_date=escape_table(result.start_date),
                end_date=escape_table(result.end_date),
                fields=escape_table(result.fields),
                required="是" if result.required_fields_ok else "否",
                fallback="是" if result.fallback_used else "否",
                reason=escape_table(result.failure_reason),
                candidate="是" if result.recommend_backfill_candidate else "否",
                output=escape_table(result.output_path),
            )
        )
    lines += [
        "",
        "## 结论",
        "",
        f"1. JQData SDK 是否可用：{'是' if import_ok else '否'}。",
        f"2. 是否能认证：{'是' if auth_ok else '否'}。",
        f"3. 选中 ETF 是否全部返回数据：{'是' if success_count == len(results) and results else '否'}。",
        f"4. 数据字段是否满足项目标准：{'是' if all_success_fields_ok else '否'}。",
        f"5. 是否能用于补齐部分历史段：{'是' if candidate_count > 0 else '否'}。",
        "6. 是否保持安全边界不变：是。",
    ]
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def normalize_date(value: str) -> str:
    return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")


def select_requests(args: argparse.Namespace) -> list[EtfRequest]:
    if args.all_etf:
        return read_watchlist_etfs(WATCHLIST_FILE)
    return [build_request(symbol) for symbol in (args.symbols or DEFAULT_SYMBOLS)]


def read_watchlist_etfs(path: Path) -> list[EtfRequest]:
    requests: list[EtfRequest] = []
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if str(row.get("type", "")).strip().upper() != "ETF":
                continue
            symbol = str(row.get("code", "")).strip()
            if symbol:
                requests.append(build_request(symbol))
    return requests


def build_request(value: str) -> EtfRequest:
    symbol = value.strip()
    if not symbol:
        raise SystemExit("Empty ETF symbol is not allowed.")
    return EtfRequest(symbol=symbol, jq_symbol=to_jq_symbol(symbol))


def to_jq_symbol(value: str) -> str:
    normalized = value.strip().upper().replace("-", "_")
    if normalized.startswith("SH_"):
        return f"{digits_only(normalized[3:])}.XSHG"
    if normalized.startswith("SZ_"):
        return f"{digits_only(normalized[3:])}.XSHE"
    if normalized.endswith(".XSHG") or normalized.endswith(".XSHE"):
        code, exchange = normalized.split(".", 1)
        return f"{digits_only(code)}.{exchange}"
    if normalized.endswith(".SH"):
        return f"{digits_only(normalized[:-3])}.XSHG"
    if normalized.endswith(".SZ"):
        return f"{digits_only(normalized[:-3])}.XSHE"
    code = digits_only(normalized)
    if code.startswith(("5", "6", "9")):
        return f"{code}.XSHG"
    if code.startswith(("0", "1", "2", "3")):
        return f"{code}.XSHE"
    raise SystemExit(f"Cannot infer JQData exchange suffix for ETF symbol: {value}")


def digits_only(value: str) -> str:
    code = "".join(char for char in value if char.isdigit())
    if len(code) != 6:
        raise SystemExit(f"ETF symbol must contain a 6-digit code: {value}")
    return code


def is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base.resolve())
    except ValueError:
        return False
    return True


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def escape_table(value: object) -> str:
    return escape_text(value).replace("|", "\\|")


def escape_text(value: object) -> str:
    text = str(value).replace("\n", " ").strip()
    for env_name in ["JQDATA_PASSWORD", "JQDATA_USER"]:
        secret = os.environ.get(env_name)
        if secret:
            text = text.replace(secret, "<redacted>")
    return text


if __name__ == "__main__":
    main()
