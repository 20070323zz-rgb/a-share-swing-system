"""Compare staged JQData ETF CSV files with local ETF daily CSV files.

This script only reads local CSV files and writes a comparison report. It does
not connect to broker APIs, does not place orders, does not read account
credentials, and does not write to data/etf_daily/ or modify strategy logic.
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
REPORT_PATH = PROJECT_ROOT / "reports" / "jqdata_local_compare_report.md"
DEFAULT_SYMBOLS = ["510300", "159915", "515000"]

PRICE_MEAN_PCT_TOLERANCE = 0.001
PRICE_MAX_PCT_TOLERANCE = 0.005
VOLUME_MEAN_PCT_TOLERANCE = 0.01
MONEY_MEAN_PCT_TOLERANCE = 0.01


@dataclass(frozen=True)
class CompareTarget:
    symbol: str
    jqdata_path: Path
    local_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare JQData staging CSV files with local ETF daily CSV files.")
    parser.add_argument("--all-etf", action="store_true", help="Compare all CSV files in data/staging/jqdata/.")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help="Symbols to compare. Defaults to the three pilot ETF symbols.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    targets = select_targets(args)
    rows = [compare_one(target) for target in targets]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(rows), encoding="utf-8")

    ok_count = sum(1 for row in rows if row["status"] == "ok")
    failed_count = len(rows) - ok_count
    print(f"jqdata local comparison finished: compared {ok_count}, failed {failed_count}")
    print(f"report written: {relative(REPORT_PATH)}")


def select_targets(args: argparse.Namespace) -> list[CompareTarget]:
    if args.all_etf:
        symbols = [extract_six_digit_code(path.name) for path in sorted(JQDATA_DIR.glob("*.csv"))]
        symbols = [symbol for symbol in symbols if symbol]
    else:
        symbols = normalize_symbols(args.symbols or DEFAULT_SYMBOLS)

    return [build_target(symbol) for symbol in symbols]


def build_target(symbol: str) -> CompareTarget:
    code = extract_six_digit_code(symbol) or symbol
    return CompareTarget(symbol=code, jqdata_path=resolve_jqdata_csv(code), local_path=resolve_local_csv(code))


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
    if matches:
        return sorted(matches, key=lambda path: jqdata_priority(path, code, exchange))[0]
    return JQDATA_DIR / f"{code}.{jq_exchange}.csv"


def resolve_local_csv(symbol: str) -> Path:
    code = extract_six_digit_code(symbol) or symbol
    exchange = infer_exchange(code)
    prefix = exchange.lower()
    candidates = [
        LOCAL_DIR / f"{prefix}_{code}.csv",
        LOCAL_DIR / f"{prefix}.{code}.csv",
        LOCAL_DIR / f"{code}.csv",
        LOCAL_DIR / f"{code}.{exchange}.csv",
    ]
    for path in candidates:
        if path.exists():
            return path

    matches = [path for path in LOCAL_DIR.glob("*.csv") if code in path.name]
    if matches:
        return sorted(matches, key=lambda path: local_priority(path, code, prefix))[0]
    return LOCAL_DIR / f"{prefix}_{code}.csv"


def compare_one(target: CompareTarget) -> dict:
    base = {
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
        "volume_mean_pct_diff": "",
        "money_amount_mean_pct_diff": "",
        "price_consistent": "否",
        "volume_money_scale_consistent": "否",
        "recommended_import_source": "否",
        "message": "",
    }
    if not target.jqdata_path.exists():
        base["message"] = f"JQData CSV not found: {relative(target.jqdata_path)}"
        return base
    if not target.local_path.exists():
        base["message"] = f"local CSV not found: {relative(target.local_path)}"
        return base

    try:
        jqdata = read_market_csv(target.jqdata_path, money_col="money")
        local = read_market_csv(target.local_path, money_col="amount")
    except Exception as exc:
        base["message"] = str(exc)
        return base

    merged = jqdata.merge(local, on="date", suffixes=("_jqdata", "_local")).sort_values("date")
    if merged.empty:
        base["message"] = "no overlapping dates"
        return base

    close_abs_diff = (merged["close_jqdata"] - merged["close_local"]).abs()
    close_pct_diff = pct_diff(merged["close_jqdata"], merged["close_local"])
    volume_pct_diff = pct_diff(merged["volume_jqdata"], merged["volume_local"])
    money_pct_diff = pct_diff(merged["money_jqdata"], merged["money_local"])

    close_mean_pct = safe_mean(close_pct_diff)
    close_max_pct = safe_max(close_pct_diff)
    volume_mean_pct = safe_mean(volume_pct_diff)
    money_mean_pct = safe_mean(money_pct_diff)
    price_consistent = (
        close_mean_pct <= PRICE_MEAN_PCT_TOLERANCE
        and close_max_pct <= PRICE_MAX_PCT_TOLERANCE
    )
    volume_money_scale_consistent = (
        volume_mean_pct <= VOLUME_MEAN_PCT_TOLERANCE
        and money_mean_pct <= MONEY_MEAN_PCT_TOLERANCE
    )
    recommended = price_consistent and volume_money_scale_consistent

    base.update(
        {
            "status": "ok",
            "overlap_start": merged["date"].min().strftime("%Y-%m-%d"),
            "overlap_end": merged["date"].max().strftime("%Y-%m-%d"),
            "overlap_rows": len(merged),
            "close_mean_abs_diff": format_number(safe_mean(close_abs_diff)),
            "close_max_abs_diff": format_number(safe_max(close_abs_diff)),
            "close_mean_pct_diff": format_pct(close_mean_pct),
            "volume_mean_pct_diff": format_pct(volume_mean_pct),
            "money_amount_mean_pct_diff": format_pct(money_mean_pct),
            "price_consistent": "是" if price_consistent else "否",
            "volume_money_scale_consistent": "是" if volume_money_scale_consistent else "否",
            "recommended_import_source": "是" if recommended else "否",
            "message": "ok" if recommended else build_non_recommended_message(price_consistent, volume_money_scale_consistent),
        }
    )
    return base


def read_market_csv(path: Path, money_col: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    df = df.rename(columns=lambda col: str(col).strip())
    required = ["date", "close", "volume", money_col]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{relative(path)} missing fields: {', '.join(missing)}")

    out = pd.DataFrame()
    out["date"] = parse_dates(df["date"])
    out["close"] = pd.to_numeric(df["close"], errors="coerce")
    out["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    out["money"] = pd.to_numeric(df[money_col], errors="coerce")
    out = out.dropna(subset=["date", "close", "volume", "money"])
    out = out.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"{relative(path)} has no comparable rows")
    return out


def build_report(rows: list[dict]) -> str:
    ok_count = sum(1 for row in rows if row["status"] == "ok")
    failed_count = len(rows) - ok_count
    recommended_count = sum(1 for row in rows if row["recommended_import_source"] == "是")
    lines = [
        "# JQData staging 与本地 ETF 日线重叠区间对比报告",
        "",
        f"- JQData staging 目录：`{relative(JQDATA_DIR)}/`",
        f"- 本地正式数据目录：`{relative(LOCAL_DIR)}/`",
        f"- 对比成功：{ok_count}",
        f"- 对比失败：{failed_count}",
        f"- 建议作为后续直接导入源：{recommended_count}",
        "- 安全边界：未接券商 API，未真实下单，未读取或保存账号密码，未写入 `data/etf_daily/`，未修改策略逻辑。",
        "",
        "| symbol | overlap_start | overlap_end | overlap_rows | close_mean_abs_diff | close_max_abs_diff | close_mean_pct_diff | volume_mean_pct_diff | money_amount_mean_pct_diff | 价格口径基本一致 | 成交量/成交额量纲一致 | 建议作为后续导入源 | 说明 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {symbol} | {overlap_start} | {overlap_end} | {overlap_rows} | {close_mean_abs_diff} | "
            "{close_max_abs_diff} | {close_mean_pct_diff} | {volume_mean_pct_diff} | "
            "{money_amount_mean_pct_diff} | {price_consistent} | {volume_money_scale_consistent} | "
            "{recommended_import_source} | {message} |".format(**row)
        )
    return "\n".join(lines) + "\n"


def build_non_recommended_message(price_consistent: bool, volume_money_scale_consistent: bool) -> str:
    messages = []
    if not price_consistent:
        messages.append("价格口径需继续核验")
    if not volume_money_scale_consistent:
        messages.append("成交量/成交额量纲需继续核验")
    return "；".join(messages)


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


def jqdata_priority(path: Path, code: str, exchange: str) -> tuple[int, str]:
    name = path.name
    jq_exchange = "XSHG" if exchange == "SH" else "XSHE"
    if name == f"{code}.{jq_exchange}.csv":
        return (1, name)
    if name == f"{code}.csv":
        return (2, name)
    return (3, name)


def local_priority(path: Path, code: str, prefix: str) -> tuple[int, str]:
    name = path.name
    if name == f"{prefix}_{code}.csv":
        return (1, name)
    if name == f"{code}.csv":
        return (2, name)
    return (3, name)


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
