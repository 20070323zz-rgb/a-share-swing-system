"""Diagnose JQData staging units against local ETF daily files.

The script only reads local CSV files and writes a diagnosis report. It does
not connect to broker APIs, place orders, read credentials, write account
information, or modify strategy logic.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
JQDATA_DIR = PROJECT_ROOT / "data" / "staging" / "jqdata"
LOCAL_DIR = PROJECT_ROOT / "data" / "etf_daily"
REPORT_PATH = PROJECT_ROOT / "reports" / "jqdata_unit_diagnosis_report.md"
DEFAULT_SYMBOLS = ["510300", "159915", "515000"]

PRICE_MEAN_PCT_TOLERANCE = 0.001
PRICE_MAX_PCT_TOLERANCE = 0.005
MONEY_RATIO_TOLERANCE = 0.001
VOLUME_RATIO_TARGETS = [1.0, 100.0, 0.01]
VOLUME_RATIO_TARGET_TOLERANCE = 0.02
VOLUME_RATIO_CV_TOLERANCE = 0.02
CLOSE_RATIO_CV_TOLERANCE = 0.002
CLOSE_ADJUSTED_MAX_PCT_TOLERANCE = 0.002
VOLUME_STABLE_CV_TOLERANCE = 0.002
MIN_OVERLAP_ROWS = 20


@dataclass(frozen=True)
class Target:
    symbol: str
    jqdata_path: Path
    local_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose JQData staging units against local ETF daily files.")
    parser.add_argument("--all-etf", action="store_true", help="Diagnose all CSV files in data/staging/jqdata/.")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help="Symbols to diagnose. Defaults to the three pilot ETF symbols.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = [diagnose_one(target) for target in select_targets(args)]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(rows), encoding="utf-8")

    ok_count = sum(1 for row in rows if row["status"] == "ok")
    recommended_count = sum(1 for row in rows if row["recommended_import_source"] == "yes")
    print(f"jqdata unit diagnosis finished: diagnosed {ok_count}, recommended {recommended_count}, total {len(rows)}")
    print(f"report written: {relative(REPORT_PATH)}")


def select_targets(args: argparse.Namespace) -> list[Target]:
    if args.all_etf:
        symbols = [extract_six_digit_code(path.name) for path in sorted(JQDATA_DIR.glob("*.csv"))]
        symbols = [symbol for symbol in symbols if symbol]
    else:
        symbols = normalize_symbols(args.symbols or DEFAULT_SYMBOLS)
    return [build_target(symbol) for symbol in symbols]


def build_target(symbol: str) -> Target:
    code = extract_six_digit_code(symbol) or symbol
    return Target(symbol=code, jqdata_path=resolve_jqdata_csv(code), local_path=resolve_local_csv(code))


def diagnose_one(target: Target) -> dict:
    row = empty_row(target)
    if not target.jqdata_path.exists():
        row["message"] = f"JQData CSV not found: {relative(target.jqdata_path)}"
        return row
    if not target.local_path.exists():
        row["message"] = f"local CSV not found: {relative(target.local_path)}"
        return row

    try:
        jqdata = read_market_csv(target.jqdata_path, money_col="money")
        local = read_market_csv(target.local_path, money_col="amount")
    except Exception as exc:
        row["message"] = str(exc)
        return row

    merged = jqdata.merge(local, on="date", suffixes=("_jqdata", "_local")).sort_values("date")
    if len(merged) < MIN_OVERLAP_ROWS:
        row["message"] = f"insufficient overlapping rows: {len(merged)}"
        return row

    close_abs_diff = (merged["close_jqdata"] - merged["close_local"]).abs()
    close_pct_diff = pct_diff(merged["close_jqdata"], merged["close_local"])
    close_ratio = safe_ratio(merged["close_jqdata"], merged["close_local"])
    volume_ratio = safe_ratio(merged["volume_jqdata"], merged["volume_local"])
    money_ratio = safe_ratio(merged["money_jqdata"], merged["money_local"])

    close_mean_pct = safe_mean(close_pct_diff)
    close_max_pct = safe_max(close_pct_diff)
    close_profile = diagnose_close_ratio(close_ratio, merged)
    price_consistent = close_profile["stable"]

    volume_profile = diagnose_volume_ratio(volume_ratio)
    money_profile = diagnose_money_ratio(money_ratio)
    recommended = price_consistent and volume_profile["stable"] and money_profile["consistent"]

    row.update(
        {
            "status": "ok",
            "overlap_start": merged["date"].min().strftime("%Y-%m-%d"),
            "overlap_end": merged["date"].max().strftime("%Y-%m-%d"),
            "overlap_rows": len(merged),
            "close_mean_abs_diff": format_number(safe_mean(close_abs_diff)),
            "close_max_abs_diff": format_number(safe_max(close_abs_diff)),
            "close_mean_pct_diff": format_pct(close_mean_pct),
            "close_max_pct_diff": format_pct(close_max_pct),
            "close_conversion_factor": format_number(close_profile["conversion_factor"]),
            "close_adjusted_max_pct_diff": format_pct(close_profile["adjusted_max_pct_diff"]),
            "close_diff_top_dates": format_top_close_dates(merged, close_abs_diff, close_pct_diff),
            "volume_ratio_median": format_number(volume_profile["median"]),
            "volume_ratio_mean": format_number(volume_profile["mean"]),
            "volume_ratio_std": format_number(volume_profile["std"]),
            "volume_ratio_min": format_number(volume_profile["min"]),
            "volume_ratio_max": format_number(volume_profile["max"]),
            "volume_conversion_factor": format_number(volume_profile["conversion_factor"]),
            "money_amount_ratio_median": format_number(money_profile["median"]),
            "money_amount_ratio_mean": format_number(money_profile["mean"]),
            "money_amount_ratio_std": format_number(money_profile["std"]),
            "close_same_basis": "yes" if price_consistent else "no",
            "volume_stable_unit_diff": "yes" if volume_profile["stable"] else "no",
            "money_amount_same_unit": "yes" if money_profile["consistent"] else "no",
            "recommended_import_source": "yes" if recommended else "no",
            "message": "ok" if recommended else build_reason(price_consistent, volume_profile, money_profile),
        }
    )
    return row


def empty_row(target: Target) -> dict:
    return {
        "symbol": target.symbol,
        "jqdata_file": relative(target.jqdata_path),
        "local_file": relative(target.local_path),
        "status": "failed",
        "overlap_start": "",
        "overlap_end": "",
        "overlap_rows": 0,
        "close_mean_abs_diff": "",
        "close_max_abs_diff": "",
        "close_mean_pct_diff": "",
        "close_max_pct_diff": "",
        "close_conversion_factor": "",
        "close_adjusted_max_pct_diff": "",
        "close_diff_top_dates": "",
        "volume_ratio_median": "",
        "volume_ratio_mean": "",
        "volume_ratio_std": "",
        "volume_ratio_min": "",
        "volume_ratio_max": "",
        "volume_conversion_factor": "",
        "money_amount_ratio_median": "",
        "money_amount_ratio_mean": "",
        "money_amount_ratio_std": "",
        "close_same_basis": "no",
        "volume_stable_unit_diff": "no",
        "money_amount_same_unit": "no",
        "recommended_import_source": "no",
        "message": "",
    }


def diagnose_close_ratio(ratio: pd.Series, merged: pd.DataFrame) -> dict:
    clean = ratio.dropna()
    median = safe_median(clean)
    mean = safe_mean(clean)
    std = safe_std(clean)
    cv = abs(std / mean) if pd.notna(std) and pd.notna(mean) and mean else float("nan")
    conversion_factor = 1 / median if pd.notna(median) and median else float("nan")
    adjusted_pct = pct_diff(merged["close_jqdata"] * conversion_factor, merged["close_local"])
    adjusted_max_pct = safe_max(adjusted_pct)
    stable = (
        pd.notna(cv)
        and pd.notna(adjusted_max_pct)
        and cv <= CLOSE_RATIO_CV_TOLERANCE
        and adjusted_max_pct <= CLOSE_ADJUSTED_MAX_PCT_TOLERANCE
    )
    return {
        "median": median,
        "mean": mean,
        "std": std,
        "cv": cv,
        "conversion_factor": conversion_factor if stable else float("nan"),
        "adjusted_max_pct_diff": adjusted_max_pct,
        "stable": stable,
    }


def diagnose_volume_ratio(ratio: pd.Series) -> dict:
    clean = ratio.dropna()
    median = safe_median(clean)
    mean = safe_mean(clean)
    std = safe_std(clean)
    min_value = safe_min(clean)
    max_value = safe_max(clean)
    target = nearest_target(median, VOLUME_RATIO_TARGETS)
    target_diff = abs(median / target - 1) if target and pd.notna(median) else float("nan")
    cv = abs(std / mean) if pd.notna(std) and pd.notna(mean) and mean else float("nan")
    stable = pd.notna(cv) and cv <= VOLUME_STABLE_CV_TOLERANCE
    return {
        "median": median,
        "mean": mean,
        "std": std,
        "min": min_value,
        "max": max_value,
        "target": target,
        "target_diff": target_diff,
        "cv": cv,
        "stable": stable,
        "conversion_factor": 1 / median if stable else float("nan"),
    }


def diagnose_money_ratio(ratio: pd.Series) -> dict:
    clean = ratio.dropna()
    median = safe_median(clean)
    mean = safe_mean(clean)
    std = safe_std(clean)
    consistent = pd.notna(median) and abs(median - 1.0) <= MONEY_RATIO_TOLERANCE and pd.notna(std) and std <= MONEY_RATIO_TOLERANCE
    return {"median": median, "mean": mean, "std": std, "consistent": consistent}


def read_market_csv(path: Path, money_col: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    df = df.rename(columns=lambda col: str(col).strip())
    required = ["date", "open", "high", "low", "close", "volume", money_col]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{relative(path)} missing fields: {', '.join(missing)}")

    out = pd.DataFrame()
    out["date"] = parse_dates(df["date"])
    for field in ["open", "high", "low", "close", "volume"]:
        out[field] = pd.to_numeric(df[field], errors="coerce")
    out["money"] = pd.to_numeric(df[money_col], errors="coerce")
    out = out.dropna(subset=["date", "open", "high", "low", "close", "volume", "money"])
    out = out.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"{relative(path)} has no comparable rows")
    return out


def build_report(rows: list[dict]) -> str:
    ok_count = sum(1 for row in rows if row["status"] == "ok")
    recommended_count = sum(1 for row in rows if row["recommended_import_source"] == "yes")
    lines = [
        "# JQData Unit Diagnosis Report",
        "",
        f"- JQData staging directory: `{relative(JQDATA_DIR)}/`",
        f"- Local ETF directory: `{relative(LOCAL_DIR)}/`",
        f"- Diagnosed symbols: {ok_count}",
        f"- Recommended import sources: {recommended_count}",
        "- Safety: no broker API, no real orders, no account credentials, no writes to `data/etf_daily/`, no strategy changes.",
        "",
        "| symbol | overlap_start | overlap_end | overlap_rows | close_mean_abs_diff | close_max_abs_diff | close_mean_pct_diff | close_max_pct_diff | close_conversion_factor | close_adjusted_max_pct_diff | volume_ratio_median | volume_ratio_mean | volume_ratio_std | volume_ratio_min | volume_ratio_max | money_amount_ratio_median | money_amount_ratio_mean | money_amount_ratio_std | close_same_basis | volume_stable_unit_diff | money_amount_same_unit | recommended_import_source | message |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {symbol} | {overlap_start} | {overlap_end} | {overlap_rows} | {close_mean_abs_diff} | {close_max_abs_diff} | "
            "{close_mean_pct_diff} | {close_max_pct_diff} | {close_conversion_factor} | {close_adjusted_max_pct_diff} | "
            "{volume_ratio_median} | {volume_ratio_mean} | "
            "{volume_ratio_std} | {volume_ratio_min} | {volume_ratio_max} | {money_amount_ratio_median} | "
            "{money_amount_ratio_mean} | {money_amount_ratio_std} | {close_same_basis} | {volume_stable_unit_diff} | "
            "{money_amount_same_unit} | {recommended_import_source} | {message} |".format(**row)
        )
    lines.extend(["", "## Close Difference Top Dates", ""])
    for row in rows:
        lines.append(f"### {row['symbol']}")
        lines.append("")
        lines.append(row["close_diff_top_dates"] or "No comparable close rows.")
        lines.append("")
    return "\n".join(lines) + "\n"


def build_reason(price_consistent: bool, volume_profile: dict, money_profile: dict) -> str:
    reasons = []
    if not price_consistent:
        reasons.append("close basis inconsistent")
    if not volume_profile["stable"]:
        reasons.append(
            "volume ratio not stable "
            f"(median={format_number(volume_profile['median'])}, std={format_number(volume_profile['std'])}, "
            f"min={format_number(volume_profile['min'])}, max={format_number(volume_profile['max'])})"
        )
    if not money_profile["consistent"]:
        reasons.append(
            "money/amount ratio inconsistent "
            f"(median={format_number(money_profile['median'])}, std={format_number(money_profile['std'])})"
        )
    return "; ".join(reasons)


def format_top_close_dates(merged: pd.DataFrame, abs_diff: pd.Series, pct: pd.Series) -> str:
    top = pd.DataFrame(
        {
            "date": merged["date"],
            "jq_close": merged["close_jqdata"],
            "local_close": merged["close_local"],
            "abs_diff": abs_diff,
            "pct_diff": pct,
        }
    ).sort_values(["abs_diff", "date"], ascending=[False, True]).head(10)
    lines = ["| date | jq_close | local_close | abs_diff | pct_diff |", "| --- | ---: | ---: | ---: | ---: |"]
    for _, item in top.iterrows():
        lines.append(
            f"| {item['date'].strftime('%Y-%m-%d')} | {format_number(item['jq_close'])} | "
            f"{format_number(item['local_close'])} | {format_number(item['abs_diff'])} | {format_pct(item['pct_diff'])} |"
        )
    return "\n".join(lines)


def resolve_jqdata_csv(symbol: str) -> Path:
    code = extract_six_digit_code(symbol) or symbol
    exchange = infer_exchange(code)
    jq_exchange = "XSHG" if exchange == "SH" else "XSHE"
    candidates = [
        JQDATA_DIR / f"{code}.{jq_exchange}.csv",
        JQDATA_DIR / f"{code}.csv",
        JQDATA_DIR / f"{code}.{exchange}.csv",
        JQDATA_DIR / f"{exchange.lower()}_{code}.csv",
        JQDATA_DIR / f"{exchange.lower()}.{code}.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    matches = [path for path in JQDATA_DIR.glob("*.csv") if code in path.name]
    return sorted(matches)[0] if matches else JQDATA_DIR / f"{code}.{jq_exchange}.csv"


def resolve_local_csv(symbol: str) -> Path:
    code = extract_six_digit_code(symbol) or symbol
    prefix = infer_exchange(code).lower()
    candidates = [LOCAL_DIR / f"{prefix}_{code}.csv", LOCAL_DIR / f"{code}.csv"]
    for path in candidates:
        if path.exists():
            return path
    matches = [path for path in LOCAL_DIR.glob("*.csv") if code in path.name]
    return sorted(matches)[0] if matches else LOCAL_DIR / f"{prefix}_{code}.csv"


def safe_ratio(left: pd.Series, right: pd.Series) -> pd.Series:
    return left.where(right != 0) / right.where(right != 0)


def pct_diff(left: pd.Series, right: pd.Series) -> pd.Series:
    denominator = right.abs()
    return (left - right).abs().where(denominator > 0) / denominator.where(denominator > 0)


def parse_dates(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip()
    parsed = pd.to_datetime(text, errors="coerce")
    fallback_mask = parsed.isna() & text.str.fullmatch(r"\d{8}")
    parsed.loc[fallback_mask] = pd.to_datetime(text.loc[fallback_mask], format="%Y%m%d", errors="coerce")
    return parsed


def extract_six_digit_code(symbol: str) -> str:
    match = re.search(r"(?<!\d)(\d{6})(?!\d)", str(symbol).strip())
    return match.group(1) if match else ""


def infer_exchange(code: str) -> str:
    if code.startswith(("5", "6")):
        return "SH"
    if code.startswith(("0", "1", "3")):
        return "SZ"
    return "SH"


def nearest_target(value: float, targets: list[float]) -> float:
    return min(targets, key=lambda target: abs(value / target - 1)) if pd.notna(value) else float("nan")


def normalize_symbols(values: list[str]) -> list[str]:
    symbols: list[str] = []
    for value in values:
        for part in value.split(","):
            symbol = part.strip()
            if symbol:
                symbols.append(symbol)
    return symbols


def safe_mean(series: pd.Series) -> float:
    value = series.dropna().mean()
    return float(value) if pd.notna(value) else float("nan")


def safe_median(series: pd.Series) -> float:
    value = series.dropna().median()
    return float(value) if pd.notna(value) else float("nan")


def safe_std(series: pd.Series) -> float:
    value = series.dropna().std()
    return float(value) if pd.notna(value) else float("nan")


def safe_min(series: pd.Series) -> float:
    value = series.dropna().min()
    return float(value) if pd.notna(value) else float("nan")


def safe_max(series: pd.Series) -> float:
    value = series.dropna().max()
    return float(value) if pd.notna(value) else float("nan")


def format_number(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{value:.6f}"


def format_pct(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{value * 100:.4f}%"


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()
