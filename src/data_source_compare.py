"""Compare Tushare staging sample with formal BaoStock/local ETF data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ETF_DAILY_DIR = DATA_DIR / "etf_daily"
STAGING_CSV = DATA_DIR / "staging" / "tushare" / "tushare_etf_daily_sample.csv"
REPORT_DIR = PROJECT_ROOT / "reports"

CSV_REPORT = REPORT_DIR / "tushare_baostock_compare.csv"
JSON_REPORT = REPORT_DIR / "tushare_baostock_compare.json"
MD_REPORT = REPORT_DIR / "tushare_baostock_compare.md"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows = compare()
    df = pd.DataFrame(rows)
    df.to_csv(CSV_REPORT, index=False)
    summary = build_summary(df)
    JSON_REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_REPORT.write_text(render_md(df, summary), encoding="utf-8")
    print(f"Tushare/BaoStock compare rows: {len(df)}")
    print(f"written: {MD_REPORT}")


def compare() -> list[dict[str, Any]]:
    staging = _read_staging()
    if staging.empty:
        return []
    rows: list[dict[str, Any]] = []
    for symbol, part in staging.groupby("symbol"):
        local = _read_local(str(symbol))
        rows.append(compare_symbol(str(symbol), part, local))
    return rows


def compare_symbol(symbol: str, tushare: pd.DataFrame, local: pd.DataFrame) -> dict[str, Any]:
    base = {
        "symbol": symbol,
        "date_overlap_count": 0,
        "close_diff_abs_mean": None,
        "close_diff_abs_max": None,
        "open_diff_pct_mean": None,
        "high_diff_pct_mean": None,
        "low_diff_pct_mean": None,
        "close_diff_pct_mean": None,
        "close_diff_pct_max": None,
        "volume_diff_pct_mean": None,
        "amount_diff_pct_mean": None,
        "volume_unit_ratio_median": None,
        "amount_unit_ratio_median": None,
        "missing_in_tushare": 0,
        "missing_in_baostock": 0,
        "field_schema_match": False,
        "quality_note": "",
    }
    if local.empty:
        base["missing_in_baostock"] = int(tushare["date"].nunique()) if "date" in tushare.columns else 0
        base["quality_note"] = "local formal data missing; cannot compare"
        return base
    t = _normalize(tushare)
    b = _normalize(local)
    if not t.empty and not b.empty:
        start = str(t["date"].min())
        end = str(t["date"].max())
        b = b[(b["date"] >= start) & (b["date"] <= end)].copy()
    required = {"date", "open", "high", "low", "close", "volume", "amount"}
    base["field_schema_match"] = required.issubset(t.columns) and required.issubset(b.columns)
    t_dates = set(t["date"].astype(str))
    b_dates = set(b["date"].astype(str))
    base["missing_in_tushare"] = len(b_dates - t_dates)
    base["missing_in_baostock"] = len(t_dates - b_dates)
    merged = t.merge(b, on="date", how="inner", suffixes=("_tushare", "_baostock"))
    base["date_overlap_count"] = int(len(merged))
    if merged.empty:
        base["quality_note"] = "no overlap"
        return base
    for col in ["open", "high", "low", "close", "volume", "amount"]:
        merged[f"{col}_tushare"] = pd.to_numeric(merged[f"{col}_tushare"], errors="coerce")
        merged[f"{col}_baostock"] = pd.to_numeric(merged[f"{col}_baostock"], errors="coerce")
    close_abs = (merged["close_tushare"] - merged["close_baostock"]).abs()
    close_pct = close_abs / merged["close_baostock"].abs().replace(0, pd.NA)
    open_pct = (merged["open_tushare"] - merged["open_baostock"]).abs() / merged["open_baostock"].abs().replace(0, pd.NA)
    high_pct = (merged["high_tushare"] - merged["high_baostock"]).abs() / merged["high_baostock"].abs().replace(0, pd.NA)
    low_pct = (merged["low_tushare"] - merged["low_baostock"]).abs() / merged["low_baostock"].abs().replace(0, pd.NA)
    volume_pct = (merged["volume_tushare"] - merged["volume_baostock"]).abs() / merged["volume_baostock"].abs().replace(0, pd.NA)
    amount_pct = (merged["amount_tushare"] - merged["amount_baostock"]).abs() / merged["amount_baostock"].abs().replace(0, pd.NA)
    volume_ratio = merged["volume_baostock"].abs().replace(0, pd.NA) / merged["volume_tushare"].abs().replace(0, pd.NA)
    amount_ratio = merged["amount_baostock"].abs().replace(0, pd.NA) / merged["amount_tushare"].abs().replace(0, pd.NA)
    base.update(
        {
            "close_diff_abs_mean": _round(close_abs.mean()),
            "close_diff_abs_max": _round(close_abs.max()),
            "open_diff_pct_mean": _round(open_pct.mean()),
            "high_diff_pct_mean": _round(high_pct.mean()),
            "low_diff_pct_mean": _round(low_pct.mean()),
            "close_diff_pct_mean": _round(close_pct.mean()),
            "close_diff_pct_max": _round(close_pct.max()),
            "volume_diff_pct_mean": _round(volume_pct.mean()),
            "amount_diff_pct_mean": _round(amount_pct.mean()),
            "volume_unit_ratio_median": _round(volume_ratio.median()),
            "amount_unit_ratio_median": _round(amount_ratio.median()),
            "quality_note": quality_note(close_pct, open_pct, high_pct, low_pct, volume_pct, amount_pct, volume_ratio, amount_ratio),
        }
    )
    return base


def build_summary(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "no_staging_data",
            "baostock_compare_ready": False,
            "symbols_compared": 0,
            "close_consistent_count": 0,
            "recommended_daily_source": "baostock",
            "candidate_daily_source": "",
            "formal_source_switched": False,
            "summary": "No Tushare staging rows available; compare skipped.",
        }
    close_ok = pd.to_numeric(df["close_diff_pct_mean"], errors="coerce").fillna(999) < 0.001
    ready = bool(len(df) and close_ok.any())
    all_good = bool(len(df) and close_ok.all())
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "completed",
        "baostock_compare_ready": ready,
        "symbols_compared": int(len(df)),
        "close_consistent_count": int(close_ok.sum()),
        "volume_amount_unit_check": "review_required" if not df.empty else "missing",
        "recommended_daily_source": "baostock",
        "candidate_daily_source": "tushare" if all_good else "",
        "formal_source_switched": False,
        "summary": "Tushare sample comparison completed; keep BaoStock as formal daily source until larger staging proves stable.",
        "safety": {
            "formal_data_written": False,
            "paper_engine_changed": False,
            "broker_api": False,
            "real_order": False,
        },
    }


def render_md(df: pd.DataFrame, summary: dict[str, Any]) -> str:
    lines = [
        f"# Tushare vs BaoStock 数据对比 {summary['generated_at']}",
        "",
        "本报告只对比 Tushare staging 样本和本地正式 ETF CSV，不覆盖正式数据。",
        "",
        "## 摘要",
        f"- status: {summary['status']}",
        f"- symbols_compared: {summary.get('symbols_compared', 0)}",
        f"- close_consistent_count: {summary.get('close_consistent_count', 0)}",
        f"- recommended_daily_source: {summary.get('recommended_daily_source', 'baostock')}",
        f"- candidate_daily_source: {summary.get('candidate_daily_source', '') or 'none'}",
        f"- formal_source_switched: {summary.get('formal_source_switched', False)}",
        "",
        "## 明细",
    ]
    if df.empty:
        lines.append("无 Tushare staging 数据，无法对比。")
    else:
        lines.extend(
            [
                "| symbol | overlap | open_pct | high_pct | low_pct | close_pct | volume_pct | amount_pct | volume_ratio | amount_ratio | missing_tushare | missing_baostock | quality_note |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for row in df.to_dict(orient="records"):
            lines.append(
                f"| {row.get('symbol')} | {row.get('date_overlap_count')} | {row.get('open_diff_pct_mean')} | {row.get('high_diff_pct_mean')} | {row.get('low_diff_pct_mean')} | {row.get('close_diff_pct_mean')} | {row.get('volume_diff_pct_mean')} | {row.get('amount_diff_pct_mean')} | {row.get('volume_unit_ratio_median')} | {row.get('amount_unit_ratio_median')} | {row.get('missing_in_tushare')} | {row.get('missing_in_baostock')} | {_md(row.get('quality_note'))} |"
            )
    lines.extend(
        [
            "",
            "## 口径判断",
            "- close 若差异接近 0，可初步认为价格口径一致。",
            "- open/high/low/close 若差异接近 0，可初步认为价格口径一致。",
            "- volume / amount 若差异大，需确认 Tushare 单位、BaoStock 单位、是否手/股、千元/元口径。",
            "- 本轮不切换正式日更主源，不进入 BUY ranking 或正式回测。",
        ]
    )
    return "\n".join(lines)


def quality_note(
    close_pct: pd.Series,
    open_pct: pd.Series,
    high_pct: pd.Series,
    low_pct: pd.Series,
    volume_pct: pd.Series,
    amount_pct: pd.Series,
    volume_ratio: pd.Series,
    amount_ratio: pd.Series,
) -> str:
    close_mean = close_pct.mean()
    ohl_mean = pd.Series([open_pct.mean(), high_pct.mean(), low_pct.mean(), close_pct.mean()]).mean()
    vol_mean = volume_pct.mean()
    amt_mean = amount_pct.mean()
    vol_ratio = volume_ratio.median()
    amt_ratio = amount_ratio.median()
    notes = []
    if pd.notna(close_mean) and close_mean < 0.001 and pd.notna(ohl_mean) and ohl_mean < 0.001:
        notes.append("OHLC basically consistent")
    else:
        notes.append("OHLC needs review")
    if pd.notna(vol_mean) and vol_mean < 0.01:
        notes.append("volume unit likely consistent")
    elif pd.notna(vol_ratio) and 95 <= vol_ratio <= 105:
        notes.append("volume likely differs by 100x")
    else:
        notes.append("volume unit needs review")
    if pd.notna(amt_mean) and amt_mean < 0.01:
        notes.append("amount unit likely consistent")
    elif pd.notna(amt_ratio) and 950 <= amt_ratio <= 1050:
        notes.append("amount likely differs by 1000x")
    else:
        notes.append("amount unit needs review")
    return "; ".join(notes)


def _read_staging() -> pd.DataFrame:
    if not STAGING_CSV.exists() or STAGING_CSV.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(STAGING_CSV, dtype={"symbol": str}).fillna("")
    except Exception:
        return pd.DataFrame()


def _read_local(symbol: str) -> pd.DataFrame:
    path = _local_path(symbol)
    if path is None:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype={"symbol": str}).fillna("")
    except Exception:
        return pd.DataFrame()


def _local_path(symbol: str) -> Path | None:
    code = "".join(ch for ch in str(symbol) if ch.isdigit())[-6:]
    for prefix in ["sh", "sz"]:
        path = ETF_DAILY_DIR / f"{prefix}_{code}.csv"
        if path.exists():
            return path
    matches = sorted(ETF_DAILY_DIR.glob(f"*{code}*.csv"))
    return matches[0] if matches else None


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    rename = {"money": "amount", "日期": "date", "成交量": "volume", "成交额": "amount"}
    out = out.rename(columns={col: rename.get(str(col), col) for col in out.columns})
    for col in ["date", "open", "high", "low", "close", "volume", "amount"]:
        if col not in out.columns:
            out[col] = pd.NA
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    return out[["date", "open", "high", "low", "close", "volume", "amount"]].dropna(subset=["date"])


def _round(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), 8)


def _md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")[:240]


if __name__ == "__main__":
    main()
