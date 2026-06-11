"""Import safe JQData staging CSV files into local ETF daily files.

This importer is conservative:
- dry-run mode never writes to data/etf_daily/
- formal import preserves existing local rows on duplicate dates
- validation-failed staging CSVs are skipped instead of blocking the whole run
- new ETF files without a local CSV are allowed after self-quality validation

It does not connect to broker APIs, place orders, read account credentials, or
modify strategy logic.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from diagnose_jqdata_units import (
    MONEY_RATIO_TOLERANCE,
    CLOSE_ADJUSTED_MAX_PCT_TOLERANCE,
    CLOSE_RATIO_CV_TOLERANCE,
    VOLUME_STABLE_CV_TOLERANCE,
    extract_six_digit_code,
    infer_exchange,
    parse_dates,
    pct_diff,
    safe_max,
    safe_mean,
    safe_median,
    safe_ratio,
    safe_std,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data" / "staging" / "jqdata"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "etf_daily"
REPORT_PATH = PROJECT_ROOT / "reports" / "jqdata_import_report.md"
EXPANSION_REPORT_PATH = PROJECT_ROOT / "reports" / "etf_expansion_import_report.md"
RESULTS_CSV_PATH = PROJECT_ROOT / "reports" / "etf_expansion_import_results.csv"
DEFAULT_SYMBOLS = ["510300", "159915", "515000"]
MIN_OVERLAP_ROWS = 20

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


@dataclass(frozen=True)
class Target:
    symbol: str
    jq_symbol: str
    input_path: Path
    output_path: Path
    code_value: str


class ValidationError(ValueError):
    """Raised when a staging CSV fails self-quality validation."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import safe JQData staging CSV files into data/etf_daily/.")
    parser.add_argument("--all-etf", action="store_true", help="Import all CSV files in --input-dir.")
    parser.add_argument("--symbols", nargs="+", default=None, help="Symbols to import. Defaults to the pilot ETF symbols.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview without writing data/etf_daily/.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR), help="Input staging directory. Default: data/staging/jqdata.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory. Default: data/etf_daily.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = resolve_dir(args.input_dir)
    output_dir = resolve_dir(args.output_dir)
    targets = select_targets(args, input_dir, output_dir)
    rows = [import_one(target, dry_run=args.dry_run) for target in targets]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report_text = build_report(rows, dry_run=args.dry_run, input_dir=input_dir, output_dir=output_dir)
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    EXPANSION_REPORT_PATH.write_text(report_text, encoding="utf-8")
    pd.DataFrame(rows).to_csv(RESULTS_CSV_PATH, index=False)

    success_count = sum(1 for row in rows if row["status"] in {"dry_run_ok", "imported"})
    failed_count = sum(1 for row in rows if row["status"] == "failed")
    validation_failed = sum(1 for row in rows if row["status"] == "validation_failed")
    mode = "dry-run" if args.dry_run else "import"
    print(f"jqdata staging {mode} finished: success {success_count}, failed {failed_count}, validation_failed {validation_failed}")
    print(f"report written: {relative(REPORT_PATH)}")
    print(f"expansion report written: {relative(EXPANSION_REPORT_PATH)}")
    print(f"results csv written: {relative(RESULTS_CSV_PATH)}")


def select_targets(args: argparse.Namespace, input_dir: Path, output_dir: Path) -> list[Target]:
    if args.all_etf:
        return [build_target_from_path(path, output_dir) for path in sorted(input_dir.glob("*.csv"))]
    symbols = normalize_symbols(args.symbols or DEFAULT_SYMBOLS)
    return [build_target_from_symbol(symbol, input_dir, output_dir) for symbol in symbols]


def build_target_from_path(path: Path, output_dir: Path) -> Target:
    code = extract_six_digit_code(path.name) or path.stem.split(".")[0]
    jq_exchange = extract_jq_exchange(path.name) or ("XSHG" if infer_exchange(code) == "SH" else "XSHE")
    local_exchange = "sh" if jq_exchange == "XSHG" else "sz"
    return Target(
        symbol=code,
        jq_symbol=f"{code}.{jq_exchange}",
        input_path=path,
        output_path=output_dir / f"{local_exchange}_{code}.csv",
        code_value=f"{local_exchange}.{code}",
    )


def build_target_from_symbol(symbol: str, input_dir: Path, output_dir: Path) -> Target:
    input_path = resolve_jqdata_csv(input_dir, symbol)
    if input_path.exists():
        return build_target_from_path(input_path, output_dir)
    code = extract_six_digit_code(symbol) or symbol
    exchange = infer_exchange(code)
    jq_exchange = "XSHG" if exchange == "SH" else "XSHE"
    prefix = exchange.lower()
    return Target(
        symbol=code,
        jq_symbol=f"{code}.{jq_exchange}",
        input_path=input_path,
        output_path=output_dir / f"{prefix}_{code}.csv",
        code_value=f"{prefix}.{code}",
    )


def import_one(target: Target, dry_run: bool) -> dict:
    row = empty_row(target, dry_run=dry_run)
    if not target.input_path.exists():
        row["failure_reason"] = f"JQData CSV not found: {relative(target.input_path)}"
        return row

    try:
        jq_raw = read_jqdata_csv(target.input_path)
    except ValidationError as exc:
        row["status"] = "validation_failed"
        row["failure_reason"] = str(exc)
        return row
    except Exception as exc:
        row["failure_reason"] = str(exc)
        return row

    try:
        local_exists = target.output_path.exists()
        local = read_local_csv(target.output_path) if local_exists else empty_local_frame()
        diagnosis = choose_diagnosis(jq_raw, local, local_exists)
    except Exception as exc:
        row["jq_rows"] = len(jq_raw)
        row["failure_reason"] = str(exc)
        return row

    row.update(
        {
            "jq_rows": len(jq_raw),
            "local_existing_rows": len(local),
            "overlap_rows": diagnosis["overlap_rows"],
            "volume_conversion_applied": diagnosis["volume_conversion_label"],
            "amount_conversion_applied": diagnosis["amount_conversion_label"],
            "close_basis_check": diagnosis["close_basis_check"],
            "close_conversion_applied": diagnosis["close_conversion_label"],
        }
    )
    if not diagnosis["safe_to_import"]:
        row["failure_reason"] = diagnosis["reason"]
        return row

    try:
        standardized = standardize_jqdata(
            jq_raw,
            target,
            close_factor=diagnosis["close_conversion_factor"],
            volume_factor=diagnosis["volume_conversion_factor"],
        )
        merged, overlap_rows, new_rows_to_add = merge_preserve_existing(standardized, local)
    except Exception as exc:
        row["failure_reason"] = str(exc)
        return row

    start_date, end_date = date_range(merged)
    row.update(
        {
            "status": "dry_run_ok" if dry_run else "imported",
            "overlap_rows": overlap_rows,
            "new_rows_to_add": new_rows_to_add,
            "final_rows_after_merge": len(merged),
            "start_date_after_merge": start_date,
            "end_date_after_merge": end_date,
            "written": "no" if dry_run else "yes",
            "failure_reason": "ok",
        }
    )

    if not dry_run:
        target.output_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(target.output_path, index=False)
    return row


def choose_diagnosis(jq_raw: pd.DataFrame, local: pd.DataFrame, local_exists: bool) -> dict:
    if not local_exists or local.empty:
        return self_only_diagnosis("new ETF file; no local CSV exists")
    jq_dates = set(jq_raw["date"].dt.strftime("%Y-%m-%d"))
    local_dates = set(pd.to_datetime(local["date"], errors="coerce").dt.strftime("%Y-%m-%d"))
    overlap_rows = len(jq_dates & local_dates)
    if overlap_rows < MIN_OVERLAP_ROWS:
        return self_only_diagnosis(f"insufficient local overlap for unit comparison: {overlap_rows}", overlap_rows=overlap_rows)
    return diagnose_units(jq_raw, local)


def self_only_diagnosis(reason: str, overlap_rows: int = 0) -> dict:
    return {
        "safe_to_import": True,
        "reason": reason,
        "overlap_rows": overlap_rows,
        "close_conversion_factor": 1.0,
        "close_conversion_label": "OHLC * 1.00000000 (self-quality only)",
        "volume_conversion_factor": 1.0,
        "volume_conversion_label": "volume * 1.00000000 (self-quality only)",
        "amount_conversion_label": "money -> amount, factor 1.0",
        "close_basis_check": "self_quality_only",
    }


def diagnose_units(jq_raw: pd.DataFrame, local: pd.DataFrame) -> dict:
    merged = jq_raw.merge(local, on="date", suffixes=("_jqdata", "_local")).sort_values("date")
    if len(merged) < MIN_OVERLAP_ROWS:
        return self_only_diagnosis(f"insufficient local overlap for unit comparison: {len(merged)}", overlap_rows=len(merged))

    close_ratio = safe_ratio(merged["close_jqdata"], merged["close_local"]).dropna()
    close_median = safe_median(close_ratio)
    close_mean = safe_mean(close_ratio)
    close_std = safe_std(close_ratio)
    close_cv = abs(close_std / close_mean) if pd.notna(close_std) and pd.notna(close_mean) and close_mean else float("nan")
    close_factor = 1 / close_median if pd.notna(close_median) and close_median else float("nan")
    close_adjusted_pct = pct_diff(merged["close_jqdata"] * close_factor, merged["close_local"])
    close_adjusted_max_pct = safe_max(close_adjusted_pct)
    close_ok = (
        pd.notna(close_cv)
        and pd.notna(close_adjusted_max_pct)
        and close_cv <= CLOSE_RATIO_CV_TOLERANCE
        and close_adjusted_max_pct <= CLOSE_ADJUSTED_MAX_PCT_TOLERANCE
    )

    volume_ratio = safe_ratio(merged["volume_jqdata"], merged["volume_local"]).dropna()
    volume_median = safe_median(volume_ratio)
    volume_mean = safe_mean(volume_ratio)
    volume_std = safe_std(volume_ratio)
    volume_cv = abs(volume_std / volume_mean) if pd.notna(volume_std) and pd.notna(volume_mean) and volume_mean else float("nan")
    volume_ok = pd.notna(volume_cv) and volume_cv <= VOLUME_STABLE_CV_TOLERANCE

    money_ratio = safe_ratio(merged["money"], merged["amount"]).dropna()
    money_median = safe_median(money_ratio)
    money_std = safe_std(money_ratio)
    money_ok = pd.notna(money_median) and abs(money_median - 1.0) <= MONEY_RATIO_TOLERANCE and pd.notna(money_std) and money_std <= MONEY_RATIO_TOLERANCE

    reasons = []
    if not close_ok:
        reasons.append(
            "close basis inconsistent: "
            f"ratio_median={close_median:.6f}, ratio_std={close_std:.6f}, "
            f"adjusted_max_pct={close_adjusted_max_pct:.6f}"
        )
    if not volume_ok:
        reasons.append(
            "volume ratio not stable: "
            f"median={volume_median:.6f}, mean={volume_mean:.6f}, std={volume_std:.6f}, cv={volume_cv:.6f}"
        )
    if not money_ok:
        reasons.append(f"money/amount ratio inconsistent: median={money_median:.6f}, std={money_std:.6f}")

    safe_to_import = not reasons
    volume_factor = 1 / volume_median if safe_to_import else float("nan")
    return {
        "safe_to_import": safe_to_import,
        "reason": "ok" if safe_to_import else "; ".join(reasons),
        "overlap_rows": len(merged),
        "close_conversion_factor": close_factor if safe_to_import else float("nan"),
        "close_conversion_label": f"OHLC * {close_factor:.8f}" if safe_to_import else "not applied",
        "volume_conversion_factor": volume_factor,
        "volume_conversion_label": f"volume * {volume_factor:.8f}" if safe_to_import else "not applied",
        "amount_conversion_label": "money -> amount, factor 1.0" if money_ok else "not applied",
        "close_basis_check": "pass" if close_ok else "fail",
    }


def read_jqdata_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str).rename(columns=lambda col: str(col).strip())
    required = ["date", "open", "high", "low", "close", "volume", "money"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValidationError(f"{relative(path)} missing fields: {', '.join(missing)}")
    if df.empty:
        raise ValidationError(f"{relative(path)} CSV has no rows")

    parsed_dates = parse_dates(df["date"])
    problems: list[str] = []
    date_parse_errors = int(parsed_dates.isna().sum())
    if date_parse_errors:
        problems.append(f"date parse errors: {date_parse_errors}")
    duplicate_dates = int(parsed_dates.dropna().dt.strftime("%Y-%m-%d").duplicated().sum())
    if duplicate_dates:
        problems.append(f"duplicate dates: {duplicate_dates}")

    numeric = {field: pd.to_numeric(df[field], errors="coerce") for field in ["open", "high", "low", "close", "volume", "money"]}
    ohlc = pd.DataFrame({field: numeric[field] for field in ["open", "high", "low", "close"]})
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
    for field in ["volume", "money"]:
        bad_count = int((numeric[field].isna() | (numeric[field] < 0)).sum())
        if bad_count:
            problems.append(f"{field} negative or invalid rows: {bad_count}")
    if problems:
        raise ValidationError("; ".join(problems))

    out = pd.DataFrame()
    out["date"] = parsed_dates
    for field in ["open", "high", "low", "close", "volume", "money"]:
        out[field] = numeric[field]
    out = out.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    if out.empty:
        raise ValidationError(f"{relative(path)} has no valid rows")
    return out


def read_local_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"code": str})
    for field in BAOSTOCK_FIELDS:
        if field not in df.columns:
            df[field] = pd.NA
    df["date"] = parse_dates(df["date"])
    for field in ["open", "high", "low", "close", "volume", "amount"]:
        df[field] = pd.to_numeric(df[field], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    return df[BAOSTOCK_FIELDS]


def empty_local_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=BAOSTOCK_FIELDS)


def standardize_jqdata(jq_raw: pd.DataFrame, target: Target, close_factor: float, volume_factor: float) -> pd.DataFrame:
    out = pd.DataFrame()
    out["date"] = jq_raw["date"].dt.strftime("%Y-%m-%d")
    out["code"] = target.code_value
    for field in ["open", "high", "low", "close"]:
        out[field] = jq_raw[field] * close_factor
    out["volume"] = (jq_raw["volume"] * volume_factor).round(0)
    out["amount"] = jq_raw["money"]
    out = out.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    out["preclose"] = out["close"].shift(1)
    out["adjustflag"] = "jqdata_pre"
    out["turn"] = pd.NA
    out["tradestatus"] = "1"
    out["pctChg"] = ((out["close"] / out["preclose"] - 1) * 100).round(4)
    out.loc[out["preclose"].isna(), "pctChg"] = pd.NA
    out["isST"] = "0"
    return out[BAOSTOCK_FIELDS]


def merge_preserve_existing(jqdata: pd.DataFrame, local: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    jq_dates = set(jqdata["date"])
    if local.empty:
        local_dates: set[str] = set()
        local_out = empty_local_frame()
    else:
        local_dates = set(local["date"].dt.strftime("%Y-%m-%d") if pd.api.types.is_datetime64_any_dtype(local["date"]) else local["date"])
        local_out = local[BAOSTOCK_FIELDS].copy()
        local_out["date"] = pd.to_datetime(local_out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    overlap_rows = len(jq_dates & local_dates)
    new_rows_to_add = len(jq_dates - local_dates)

    jq_out = jqdata[BAOSTOCK_FIELDS].copy()
    jq_out["_source_priority"] = 0
    local_out["_source_priority"] = 1
    merged = pd.concat([jq_out, local_out], ignore_index=True)
    merged["date"] = pd.to_datetime(merged["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    merged = (
        merged.dropna(subset=["date"])
        .sort_values(["date", "_source_priority"])
        .drop_duplicates("date", keep="last")
        .drop(columns=["_source_priority"])
        .reset_index(drop=True)
    )
    return merged[BAOSTOCK_FIELDS], overlap_rows, new_rows_to_add


def build_report(rows: list[dict], dry_run: bool, input_dir: Path, output_dir: Path) -> str:
    success_count = sum(1 for row in rows if row["status"] in {"dry_run_ok", "imported"})
    failed_count = sum(1 for row in rows if row["status"] == "failed")
    validation_failed = sum(1 for row in rows if row["status"] == "validation_failed")
    validation_valid = len(rows) - validation_failed
    written_count = sum(1 for row in rows if row["written"] == "yes")
    dry_run_success = sum(1 for row in rows if row["status"] == "dry_run_ok")
    dry_run_failed = sum(1 for row in rows if row["status"] in {"failed", "validation_failed"}) if dry_run else 0
    formal_imports = sum(1 for row in rows if row["status"] == "imported")
    total_new_rows = sum(int(row["new_rows_to_add"] or 0) for row in rows if row["status"] in {"dry_run_ok", "imported"})
    lines = [
        "# ETF Expansion Import Report",
        "",
        f"- Generated on: {date.today().isoformat()}",
        f"- Mode: {'dry-run' if dry_run else 'formal import'}",
        f"- Input directory: `{relative(input_dir)}/`",
        f"- Output directory: `{relative(output_dir)}/`",
        f"- Staging CSV total: {len(rows)}",
        f"- Validation valid: {validation_valid}",
        f"- Validation failed: {validation_failed}",
        f"- Dry-run success: {dry_run_success}",
        f"- Dry-run failed: {dry_run_failed}",
        f"- Formal imports: {formal_imports}",
        f"- Success: {success_count}",
        f"- Failed: {failed_count}",
        f"- Files written: {written_count}",
        f"- Total new rows to add: {total_new_rows}",
        "- BaoStock API calls: 0",
        "- Non-imported reasons: validation failures are skipped; remaining failures are listed per symbol below.",
        "- Merge rule: local existing rows win on duplicate dates; no overwrite of existing local/BaoStock rows.",
        "- Safety: no broker API, no real orders, no account credentials, no automatic trading, no strategy changes.",
        "",
        "| symbol | jq_symbol | local_file | status | dry_run | jq_rows | local_existing_rows | overlap_rows | new_rows_to_add | final_rows_after_merge | start_date_after_merge | end_date_after_merge | close_conversion_applied | volume_conversion_applied | amount_conversion_applied | close_basis_check | written | failure_reason |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {symbol} | {jq_symbol} | `{local_file}` | {status} | {dry_run} | {jq_rows} | {local_existing_rows} | "
            "{overlap_rows} | {new_rows_to_add} | {final_rows_after_merge} | {start_date_after_merge} | "
            "{end_date_after_merge} | {close_conversion_applied} | {volume_conversion_applied} | {amount_conversion_applied} | "
            "{close_basis_check} | {written} | {failure_reason} |".format(**clean_row(row))
        )
    return "\n".join(lines) + "\n"


def clean_row(row: dict) -> dict:
    return {key: str(value).replace("|", "/") for key, value in row.items()}


def empty_row(target: Target, dry_run: bool) -> dict:
    return {
        "symbol": target.symbol,
        "jq_symbol": target.jq_symbol,
        "local_file": relative(target.output_path),
        "status": "failed",
        "dry_run": "yes" if dry_run else "no",
        "jq_rows": 0,
        "local_existing_rows": 0,
        "overlap_rows": 0,
        "new_rows_to_add": 0,
        "final_rows_after_merge": 0,
        "start_date_after_merge": "",
        "end_date_after_merge": "",
        "volume_conversion_applied": "",
        "close_conversion_applied": "",
        "amount_conversion_applied": "",
        "close_basis_check": "",
        "written": "no",
        "failure_reason": "",
    }


def resolve_jqdata_csv(input_dir: Path, symbol: str) -> Path:
    code = extract_six_digit_code(symbol) or symbol
    exchange_from_symbol = extract_jq_exchange(symbol)
    exchange = exchange_from_symbol or ("XSHG" if infer_exchange(code) == "SH" else "XSHE")
    local_exchange = "SH" if exchange == "XSHG" else "SZ"
    candidates = [
        input_dir / f"{code}.{exchange}.csv",
        input_dir / f"{code}.csv",
        input_dir / f"{code}.{local_exchange}.csv",
        input_dir / f"{local_exchange.lower()}_{code}.csv",
        input_dir / f"{local_exchange.lower()}.{code}.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    matches = [path for path in input_dir.glob("*.csv") if code in path.name]
    return sorted(matches)[0] if matches else input_dir / f"{code}.{exchange}.csv"


def extract_jq_exchange(value: str) -> str:
    match = re.search(r"\.(XSHG|XSHE)(?:\.csv)?$", str(value), flags=re.IGNORECASE)
    return match.group(1).upper() if match else ""


def normalize_symbols(values: list[str]) -> list[str]:
    symbols: list[str] = []
    for value in values:
        for part in value.split(","):
            symbol = part.strip()
            if symbol:
                symbols.append(symbol)
    return symbols


def date_range(df: pd.DataFrame) -> tuple[str, str]:
    dates = pd.to_datetime(df["date"], errors="coerce").dropna()
    if dates.empty:
        return "", ""
    return dates.min().strftime("%Y-%m-%d"), dates.max().strftime("%Y-%m-%d")


def resolve_dir(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()
