"""Validate manual ETF CSV files before importing them.

This script only reads local manual CSV files. It does not connect to broker
APIs, does not place orders, does not read account credentials, and does not
write to data/etf_daily/ or modify strategy logic.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANUAL_DIR = PROJECT_ROOT / "data" / "manual_import"
DEFAULT_SYMBOLS = ["510300", "159915", "515000"]
REQUIRED_FIELDS = ["date", "open", "high", "low", "close", "volume"]
OHLC_FIELDS = ["open", "high", "low", "close"]
NONNEGATIVE_FIELDS = ["volume", "money", "amount"]


@dataclass(frozen=True)
class CsvTarget:
    path: Path
    missing_message: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate manual ETF CSV files.")
    parser.add_argument(
        "--input-dir",
        default=str(MANUAL_DIR),
        help="Directory containing manual CSV files. Default: data/manual_import/.",
    )
    parser.add_argument("--all-etf", action="store_true", help="Validate all CSV files in --input-dir.")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help="Symbols to validate. Defaults to the three pilot ETF symbols.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = resolve_input_dir(args.input_dir)
    if not input_dir.exists():
        print(f"input directory not found: {relative(input_dir)}")
        return
    if not input_dir.is_dir():
        print(f"input path is not a directory: {relative(input_dir)}")
        return

    targets = select_csv_targets(args, input_dir)
    results = [validate_one(target) for target in targets]
    for result in results:
        path_text = relative(result["path"])
        if result["valid"]:
            print(f"{path_text} passed validation.")
        else:
            print(f"{path_text} failed validation: {result['message']}")

    valid_count = sum(1 for result in results if result["valid"])
    failed_count = len(results) - valid_count
    print(f"manual CSV validation finished: valid {valid_count}, failed {failed_count}")


def select_csv_targets(args: argparse.Namespace, input_dir: Path) -> list[CsvTarget]:
    if args.all_etf:
        return [
            CsvTarget(path)
            for path in sorted(path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() == ".csv")
        ]

    symbols = normalize_symbols(args.symbols or DEFAULT_SYMBOLS)
    return [resolve_symbol_csv(input_dir, symbol) for symbol in symbols]


def resolve_symbol_csv(input_dir: Path, symbol: str) -> CsvTarget:
    code = extract_six_digit_code(symbol)
    if not code:
        return CsvTarget(
            input_dir / f"{symbol}.csv",
            f"manual CSV not found for symbol {symbol} in {relative(input_dir)}",
        )

    exchange = infer_exchange(code)
    lower_exchange = exchange.lower()
    jq_exchange = "XSHG" if exchange == "SH" else "XSHE"
    candidates = [
        input_dir / f"{code}.csv",
        input_dir / f"{code}.{jq_exchange}.csv",
        input_dir / f"{lower_exchange}_{code}.csv",
        input_dir / f"{lower_exchange}.{code}.csv",
        input_dir / f"{code}.{exchange}.csv",
    ]
    for path in candidates:
        if path.exists():
            return CsvTarget(path)

    matches = [path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() == ".csv" and code in path.name]
    if matches:
        return CsvTarget(sorted(matches, key=lambda path: fallback_priority(path, code, exchange))[0])

    return CsvTarget(
        input_dir / f"{code}.csv",
        f"manual CSV not found for symbol {symbol} in {relative(input_dir)}",
    )


def extract_six_digit_code(symbol: str) -> str:
    match = re.search(r"(?<!\d)(\d{6})(?!\d)", str(symbol).strip())
    return match.group(1) if match else ""


def infer_exchange(code: str) -> str:
    if code.startswith(("5", "6")):
        return "SH"
    if code.startswith(("0", "1", "3")):
        return "SZ"
    return "SH"


def fallback_priority(path: Path, code: str, exchange: str) -> tuple[int, str]:
    name = path.name
    lower_exchange = exchange.lower()
    jq_exchange = "XSHG" if exchange == "SH" else "XSHE"
    if name == f"{code}.csv":
        return (1, name)
    if name == f"{code}.{jq_exchange}.csv":
        return (2, name)
    if name == f"{lower_exchange}_{code}.csv":
        return (3, name)
    return (4, name)


def validate_one(target: CsvTarget) -> dict:
    path = target.path
    result = {"path": path, "valid": False, "message": ""}
    if not path.exists():
        result["message"] = target.missing_message or "manual CSV not found"
        return result
    if not path.is_file():
        result["message"] = "manual CSV path is not a file"
        return result

    try:
        df = pd.read_csv(path, dtype=str)
    except Exception as exc:
        result["message"] = f"read failed: {exc}"
        return result

    df = df.rename(columns=lambda col: str(col).strip())
    problems: list[str] = []
    missing = [field for field in REQUIRED_FIELDS if field not in df.columns]
    if missing:
        result["message"] = f"missing required fields: {', '.join(missing)}"
        return result
    if df.empty:
        result["message"] = "CSV has no rows"
        return result

    parsed_dates = parse_dates(df["date"])
    date_parse_errors = int(parsed_dates.isna().sum())
    if date_parse_errors:
        problems.append(f"date parse errors: {date_parse_errors}")

    duplicate_dates = int(parsed_dates.dropna().dt.strftime("%Y-%m-%d").duplicated().sum())
    if duplicate_dates:
        problems.append(f"duplicate dates: {duplicate_dates}")

    numeric = {field: pd.to_numeric(df[field], errors="coerce") for field in REQUIRED_FIELDS if field != "date"}
    ohlc = pd.DataFrame({field: numeric[field] for field in OHLC_FIELDS})
    ohlc_bad = int((ohlc.isna().any(axis=1) | (ohlc <= 0).any(axis=1)).sum())
    if ohlc_bad:
        problems.append(f"bad OHLC rows: {ohlc_bad}")

    high_lt_low = int((numeric["high"] < numeric["low"]).sum())
    if high_lt_low:
        problems.append(f"high < low rows: {high_lt_low}")

    ohlc_outside_range = int(
        (
            (numeric["open"] > numeric["high"])
            | (numeric["open"] < numeric["low"])
            | (numeric["close"] > numeric["high"])
            | (numeric["close"] < numeric["low"])
        ).sum()
    )
    if ohlc_outside_range:
        problems.append(f"OHLC outside high/low range rows: {ohlc_outside_range}")

    for field in NONNEGATIVE_FIELDS:
        if field not in df.columns:
            continue
        values = numeric[field] if field in numeric else pd.to_numeric(df[field], errors="coerce")
        bad_count = int((values.isna() | (values < 0)).sum())
        if bad_count:
            problems.append(f"{field} negative or invalid rows: {bad_count}")

    result["valid"] = not problems
    result["message"] = "ok" if not problems else "; ".join(problems)
    return result


def parse_dates(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip()
    parsed = pd.to_datetime(text, errors="coerce")
    fallback_mask = parsed.isna() & text.str.fullmatch(r"\d{8}")
    parsed.loc[fallback_mask] = pd.to_datetime(text.loc[fallback_mask], format="%Y%m%d", errors="coerce")
    return parsed


def normalize_symbols(values: list[str]) -> list[str]:
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


def resolve_input_dir(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


if __name__ == "__main__":
    main()
