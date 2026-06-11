"""Safely probe QMT/miniQMT xtdata ETF daily data access.

This script is a read-only market-data test skeleton. It intentionally does
not import xttrader, does not connect to a trading account, does not read
credentials, does not query assets or positions, and does not place orders.

By default it does not download data. Add --run explicitly to call xtdata
history methods. Output is restricted to data/staging/qmt/ and
reports/qmt_test_report.md.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "staging" / "qmt"
DEFAULT_REPORT_FILE = PROJECT_ROOT / "reports" / "qmt_test_report.md"
DEFAULT_SYMBOLS = ["510300.SH", "159915.SZ", "515000.SH"]
DEFAULT_START = "2022-01-04"
DEFAULT_END = "2026-06-03"
OUTPUT_COLUMNS = ["date", "open", "high", "low", "close", "volume", "amount"]
QMT_FIELDS = ["time", "open", "high", "low", "close", "volume", "amount"]


@dataclass
class TestResult:
    symbol: str
    status: str
    rows: int = 0
    start_date: str = ""
    end_date: str = ""
    output_path: str = ""
    message: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safe QMT/miniQMT xtdata read-only ETF daily data probe.")
    parser.add_argument("--run", action="store_true", help="Actually call xtdata history methods. Default is dry-run only.")
    parser.add_argument("--start", default=DEFAULT_START, help="Start date, YYYY-MM-DD. Default: 2022-01-04.")
    parser.add_argument("--end", default=DEFAULT_END, help="End date, YYYY-MM-DD. Default: 2026-06-03.")
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS, help="QMT symbols, for example 510300.SH 159915.SZ.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="CSV output directory. Must not be data/etf_daily/.")
    parser.add_argument("--report-file", default=str(DEFAULT_REPORT_FILE), help="Markdown report file.")
    parser.add_argument(
        "--dividend-type",
        default="none",
        choices=["none", "front", "back", "front_ratio", "back_ratio"],
        help="QMT dividend_type for K-line data. Default: none.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    report_file = Path(args.report_file).resolve()
    ensure_safe_paths(output_dir, report_file)

    start = normalize_date(args.start)
    end = normalize_date(args.end)
    symbols = normalize_symbols(args.symbols)

    xtdata, import_error = import_xtdata()
    if import_error:
        results = [TestResult(symbol=symbol, status="import_failed", message=import_error) for symbol in symbols]
        write_report(report_file, args.run, False, import_error, start, end, output_dir, results)
        print("xtquant.xtdata import failed. Install and run inside the QMT/miniQMT environment.")
        print(f"report written: {report_file}")
        if args.run:
            raise SystemExit(1)
        return

    if not args.run:
        results = [
            TestResult(
                symbol=symbol,
                status="dry_run",
                message="xtquant.xtdata import succeeded; no real download was executed because --run was not provided.",
            )
            for symbol in symbols
        ]
        write_report(report_file, False, True, "", start, end, output_dir, results)
        print("dry-run complete: xtquant.xtdata import succeeded; no QMT data request was executed.")
        print(f"report written: {report_file}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    results = run_readonly_probe(xtdata, symbols, start, end, output_dir, args.dividend_type)
    write_report(report_file, True, True, "", start, end, output_dir, results)
    success_count = sum(1 for result in results if result.status == "success")
    failed_count = len(results) - success_count
    print(f"QMT xtdata read-only probe finished: success {success_count}, failed {failed_count}")
    print(f"report written: {report_file}")


def ensure_safe_paths(output_dir: Path, report_file: Path) -> None:
    etf_daily_dir = (PROJECT_ROOT / "data" / "etf_daily").resolve()
    if output_dir == etf_daily_dir or etf_daily_dir in output_dir.parents:
        raise SystemExit("Refusing to write QMT test output under data/etf_daily/. Use data/staging/qmt/.")
    if not is_relative_to(output_dir, PROJECT_ROOT):
        raise SystemExit("Refusing to write QMT test output outside the project.")
    if not is_relative_to(report_file, PROJECT_ROOT):
        raise SystemExit("Refusing to write QMT test report outside the project.")


def import_xtdata() -> tuple[ModuleType | None, str]:
    try:
        from xtquant import xtdata
    except Exception as exc:
        return None, str(exc)
    return xtdata, ""


def run_readonly_probe(
    xtdata: ModuleType,
    symbols: list[str],
    start: str,
    end: str,
    output_dir: Path,
    dividend_type: str,
) -> list[TestResult]:
    connect_market_data_if_available(xtdata)
    results = []
    for symbol in symbols:
        results.append(fetch_daily_to_staging(xtdata, symbol, start, end, output_dir, dividend_type))
    return results


def connect_market_data_if_available(xtdata: ModuleType) -> None:
    connect = getattr(xtdata, "connect", None)
    if callable(connect):
        connect()


def fetch_daily_to_staging(
    xtdata: ModuleType,
    symbol: str,
    start: str,
    end: str,
    output_dir: Path,
    dividend_type: str,
) -> TestResult:
    output_path = output_dir / f"{symbol}.csv"
    start_compact = start.replace("-", "")
    end_compact = end.replace("-", "")
    result = TestResult(symbol=symbol, status="failed", output_path=relative(output_path))

    try:
        download_history = getattr(xtdata, "download_history_data", None)
        if callable(download_history):
            download_history(symbol, period="1d", start_time=start_compact, end_time=end_compact)

        get_market_data_ex = getattr(xtdata, "get_market_data_ex", None)
        if not callable(get_market_data_ex):
            result.message = "xtdata.get_market_data_ex is not available in this environment."
            return result

        raw = get_market_data_ex(
            field_list=QMT_FIELDS,
            stock_list=[symbol],
            period="1d",
            start_time=start_compact,
            end_time=end_compact,
            count=-1,
            dividend_type=dividend_type,
            fill_data=True,
        )
        daily = normalize_xtdata_result(raw, symbol)
    except Exception as exc:
        result.message = f"xtdata history request failed: {exc}"
        return result

    if daily.empty:
        result.message = "xtdata returned no daily rows."
        return result

    output_path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(output_path, index=False)
    result.status = "success"
    result.rows = len(daily)
    result.start_date = str(daily["date"].iloc[0])
    result.end_date = str(daily["date"].iloc[-1])
    result.message = "saved to staging output."
    return result


def normalize_xtdata_result(raw: Any, symbol: str) -> pd.DataFrame:
    if isinstance(raw, dict):
        frame = raw.get(symbol)
        if frame is None and raw:
            frame = next(iter(raw.values()))
    else:
        frame = raw

    if frame is None:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    df = pd.DataFrame(frame).copy()
    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    if "date" not in df.columns:
        if "time" in df.columns:
            df["date"] = df["time"].map(format_qmt_time)
        else:
            df["date"] = pd.Series(df.index, index=df.index).map(format_qmt_time)

    for column in OUTPUT_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[OUTPUT_COLUMNS].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for column in ["open", "high", "low", "close", "volume", "amount"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=["date", "open", "high", "low", "close"])
    df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    return df


def format_qmt_time(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    if text.isdigit():
        if len(text) >= 13:
            return datetime.fromtimestamp(int(text[:13]) / 1000).strftime("%Y-%m-%d")
        if len(text) >= 8:
            return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.strftime("%Y-%m-%d")


def write_report(
    report_file: Path,
    run_requested: bool,
    import_ok: bool,
    import_error: str,
    start: str,
    end: str,
    output_dir: Path,
    results: list[TestResult],
) -> None:
    report_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# QMT / miniQMT xtdata 只读行情测试报告",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 是否显式执行真实下载：{'是' if run_requested else '否'}",
        f"- xtquant.xtdata 导入：{'成功' if import_ok else '失败'}",
        f"- 测试区间：{start} 到 {end}",
        f"- 输出目录：`{relative(output_dir)}`",
        f"- 安全边界：未导入 xttrader；不连接交易账户；不读取账号密码；不查资金；不查持仓；不下单；不写入 data/etf_daily/。",
        "",
    ]
    if import_error:
        lines += ["## 导入错误", "", f"```text\n{import_error}\n```", ""]
    lines += [
        "## 标的结果",
        "",
        "| symbol | status | rows | start_date | end_date | output_path | message |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for result in results:
        lines.append(
            "| {symbol} | {status} | {rows} | {start} | {end} | `{path}` | {message} |".format(
                symbol=escape_table(result.symbol),
                status=escape_table(result.status),
                rows=result.rows,
                start=escape_table(result.start_date),
                end=escape_table(result.end_date),
                path=escape_table(result.output_path),
                message=escape_table(result.message),
            )
        )
    lines += ["", "## 下一步", ""]
    if not run_requested:
        lines.append("1. 如需真实验证 QMT 历史日线，请在已开通 QMT / miniQMT 且确认只读行情边界后运行 `python3 scripts/test_qmt_xtdata.py --run`。")
    elif import_ok:
        lines.append("1. 检查 staging CSV 的日期覆盖、字段、成交量单位和成交额单位。")
        lines.append("2. 不要把 staging 文件复制或导入 `data/etf_daily/`，除非后续重新确认正式导入流程。")
    else:
        lines.append("1. 请先确认本机是否安装并启动东方证券 QMT / miniQMT 环境，以及 Python 是否能导入 `xtquant.xtdata`。")
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def normalize_date(value: str) -> str:
    parsed = datetime.strptime(value, "%Y-%m-%d")
    return parsed.strftime("%Y-%m-%d")


def normalize_symbols(values: list[str]) -> list[str]:
    symbols = []
    for value in values:
        symbol = value.strip().upper()
        if not symbol:
            continue
        if "." not in symbol:
            raise SystemExit(f"QMT symbol must include market suffix, for example 510300.SH: {value}")
        symbols.append(symbol)
    return symbols


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base.resolve())
    except ValueError:
        return False
    return True


def escape_table(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
