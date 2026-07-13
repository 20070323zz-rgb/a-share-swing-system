"""Research-only multi-benchmark Market Exposure vector prototype.

The prototype calculates pairwise beta, correlation, and R-squared for each
Universe V2 research ETF against a versioned basket of ETF benchmark proxies.
It does not read or write strategy, ranking, preview, paper-trading, or formal
execution artifacts.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from itertools import combinations
from typing import Any

import pandas as pd

from config import DATA_DIR, REPORT_DIR
from exposure.exposure_calculator import fmt_date, load_price_data, load_universe, round_float


UNIVERSE_VERSION = "universe_v2_qualified_research"
BENCHMARK_BASKET_VERSION = "market_benchmark_basket_v1"
CORE_BENCHMARK_CODE = "510300"
LOOKBACK_WINDOWS = (60, 120)

BENCHMARK_BASKET = (
    {
        "benchmark_code": "510300",
        "benchmark_name": "沪深300ETF",
        "benchmark_family": "core_market",
        "role": "A-share large/core market anchor",
    },
    {
        "benchmark_code": "510500",
        "benchmark_name": "中证500ETF",
        "benchmark_family": "mid_cap",
        "role": "A-share mid-cap market proxy",
    },
    {
        "benchmark_code": "512100",
        "benchmark_name": "中证1000ETF代理",
        "benchmark_family": "small_cap",
        "role": "A-share small-cap market proxy",
    },
    {
        "benchmark_code": "159915",
        "benchmark_name": "创业板ETF",
        "benchmark_family": "growth",
        "role": "ChiNext growth-board proxy",
    },
    {
        "benchmark_code": "588000",
        "benchmark_name": "科创50ETF",
        "benchmark_family": "technology",
        "role": "STAR hard-technology proxy",
    },
    {
        "benchmark_code": "510880",
        "benchmark_name": "红利ETF",
        "benchmark_family": "defensive",
        "role": "Dividend/defensive equity proxy",
    },
)

OUTPUT_DIR = DATA_DIR / "research" / "exposure_prototype"
OUTPUT_VALUES_CSV = OUTPUT_DIR / "market_exposure_vector_values.csv"
OUTPUT_MISSING_CSV = OUTPUT_DIR / "market_exposure_vector_missing.csv"
OUTPUT_BENCHMARK_COVERAGE_CSV = OUTPUT_DIR / "market_exposure_vector_benchmark_coverage.csv"
OUTPUT_BENCHMARK_REDUNDANCY_CSV = OUTPUT_DIR / "market_exposure_vector_benchmark_redundancy.csv"
OUTPUT_COMPARISON_CSV = OUTPUT_DIR / "market_exposure_vector_single_vs_multi.csv"
OUTPUT_MANIFEST_JSON = OUTPUT_DIR / "market_exposure_vector_manifest.json"

SUMMARY_REPORT = REPORT_DIR / "market_exposure_vector_summary.md"
REDUNDANCY_REPORT = REPORT_DIR / "benchmark_redundancy_analysis.md"

VECTOR_COLUMNS = [
    "calculation_date",
    "universe_version",
    "benchmark_basket_version",
    "etf_code",
    "etf_name",
    "benchmark_code",
    "benchmark_name",
    "benchmark_family",
    "lookback_window",
    "beta",
    "correlation",
    "r_squared",
    "sample_size",
    "window_start_date",
    "window_end_date",
    "confidence",
    "PIT_status",
    "missing_flag",
    "missing_reason",
    "source_data",
    "research_only",
    "execution_allowed",
]


def run_market_exposure_vector(universe: str = UNIVERSE_VERSION) -> dict[str, Any]:
    universe_df = load_universe(universe)
    etf_data = {
        str(row["symbol"]).zfill(6): load_price_data(str(row["symbol"]).zfill(6))
        for _, row in universe_df.iterrows()
    }

    benchmark_data: dict[str, pd.DataFrame | None] = {}
    benchmark_errors: dict[str, str] = {}
    for benchmark in BENCHMARK_BASKET:
        code = benchmark["benchmark_code"]
        try:
            benchmark_data[code] = load_price_data(code)
        except (FileNotFoundError, ValueError) as exc:
            benchmark_data[code] = None
            benchmark_errors[code] = str(exc)

    available_benchmarks = [df for df in benchmark_data.values() if df is not None]
    if not available_benchmarks:
        raise RuntimeError("no benchmark data is available")

    latest_dates = [df["date"].max() for df in etf_data.values()]
    latest_dates.extend(df["date"].max() for df in available_benchmarks)
    calculation_date = pd.Timestamp(min(latest_dates))

    vector_rows: list[dict[str, Any]] = []
    for _, etf in universe_df.iterrows():
        etf_code = str(etf["symbol"]).zfill(6)
        etf_name = str(etf.get("name", etf_code))
        for benchmark in BENCHMARK_BASKET:
            benchmark_code = benchmark["benchmark_code"]
            benchmark_df = benchmark_data[benchmark_code]
            for window in LOOKBACK_WINDOWS:
                vector_rows.append(
                    calculate_vector_row(
                        universe_version=universe,
                        etf_code=etf_code,
                        etf_name=etf_name,
                        etf_df=etf_data[etf_code],
                        benchmark=benchmark,
                        benchmark_df=benchmark_df,
                        benchmark_error=benchmark_errors.get(benchmark_code, ""),
                        lookback_window=window,
                        calculation_date=calculation_date,
                    )
                )

    vector_df = pd.DataFrame(vector_rows, columns=VECTOR_COLUMNS)
    missing_df = vector_df[vector_df["missing_flag"].astype(bool)].copy()
    coverage_df = build_benchmark_coverage(benchmark_data, benchmark_errors, calculation_date)
    redundancy_df = build_benchmark_redundancy(benchmark_data, calculation_date)
    comparison_df = build_single_vs_multi_comparison(vector_df)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    vector_df.to_csv(OUTPUT_VALUES_CSV, index=False)
    missing_df.to_csv(OUTPUT_MISSING_CSV, index=False)
    coverage_df.to_csv(OUTPUT_BENCHMARK_COVERAGE_CSV, index=False)
    redundancy_df.to_csv(OUTPUT_BENCHMARK_REDUNDANCY_CSV, index=False)
    comparison_df.to_csv(OUTPUT_COMPARISON_CSV, index=False)

    manifest = build_manifest(
        universe=universe,
        universe_df=universe_df,
        vector_df=vector_df,
        missing_df=missing_df,
        coverage_df=coverage_df,
        redundancy_df=redundancy_df,
        comparison_df=comparison_df,
        calculation_date=calculation_date,
    )
    OUTPUT_MANIFEST_JSON.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def calculate_vector_row(
    universe_version: str,
    etf_code: str,
    etf_name: str,
    etf_df: pd.DataFrame,
    benchmark: dict[str, str],
    benchmark_df: pd.DataFrame | None,
    benchmark_error: str,
    lookback_window: int,
    calculation_date: pd.Timestamp,
) -> dict[str, Any]:
    base = {
        "calculation_date": fmt_date(calculation_date),
        "universe_version": universe_version,
        "benchmark_basket_version": BENCHMARK_BASKET_VERSION,
        "etf_code": etf_code,
        "etf_name": etf_name,
        "benchmark_code": benchmark["benchmark_code"],
        "benchmark_name": benchmark["benchmark_name"],
        "benchmark_family": benchmark["benchmark_family"],
        "lookback_window": int(lookback_window),
        "beta": None,
        "correlation": None,
        "r_squared": None,
        "sample_size": 0,
        "window_start_date": "",
        "window_end_date": "",
        "confidence": "NOT_AVAILABLE",
        "PIT_status": "NOT_AVAILABLE",
        "missing_flag": True,
        "missing_reason": "",
        "source_data": "data/etf_daily",
        "research_only": True,
        "execution_allowed": False,
    }
    if benchmark_df is None:
        base["missing_reason"] = f"BENCHMARK_NOT_AVAILABLE: {benchmark_error}"
        return base

    paired = paired_returns(etf_df, benchmark_df, calculation_date)
    sample = paired.tail(lookback_window)
    base["sample_size"] = int(len(sample))
    if len(sample) < lookback_window:
        base["missing_reason"] = "INSUFFICIENT_PAIRED_HISTORY"
        base["PIT_status"] = "INSUFFICIENT_HISTORY"
        return base

    variance = float(sample["benchmark_return"].var(ddof=1))
    correlation = float(sample["etf_return"].corr(sample["benchmark_return"]))
    if variance == 0 or math.isnan(variance):
        base["missing_reason"] = "ZERO_BENCHMARK_VARIANCE"
        return base
    if math.isnan(correlation):
        base["missing_reason"] = "CORRELATION_NOT_AVAILABLE"
        return base

    covariance = float(sample[["etf_return", "benchmark_return"]].cov().iloc[0, 1])
    beta = covariance / variance
    base.update({
        "beta": round_float(beta),
        "correlation": round_float(correlation),
        "r_squared": round_float(correlation * correlation),
        "window_start_date": fmt_date(sample["date"].iloc[0]),
        "window_end_date": fmt_date(sample["date"].iloc[-1]),
        "confidence": "MEDIUM" if abs(correlation) >= 0.30 else "LOW",
        "PIT_status": "PIT_SAFE_WITH_PROXY",
        "missing_flag": False,
        "missing_reason": "",
    })
    return base


def paired_returns(
    etf_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    calculation_date: pd.Timestamp,
) -> pd.DataFrame:
    etf_returns = daily_returns(etf_df, calculation_date, "etf_return")
    benchmark_returns = daily_returns(benchmark_df, calculation_date, "benchmark_return")
    return (
        pd.merge(etf_returns, benchmark_returns, on="date", how="inner")
        .dropna(subset=["etf_return", "benchmark_return"])
        .sort_values("date")
        .reset_index(drop=True)
    )


def daily_returns(df: pd.DataFrame, calculation_date: pd.Timestamp, column: str) -> pd.DataFrame:
    values = df.loc[df["date"] <= calculation_date, ["date", "close"]].copy()
    values = values.sort_values("date").drop_duplicates("date", keep="last")
    values[column] = values["close"].pct_change(fill_method=None)
    return values[["date", column]].dropna(subset=[column])


def build_benchmark_coverage(
    benchmark_data: dict[str, pd.DataFrame | None],
    benchmark_errors: dict[str, str],
    calculation_date: pd.Timestamp,
) -> pd.DataFrame:
    rows = []
    for benchmark in BENCHMARK_BASKET:
        code = benchmark["benchmark_code"]
        df = benchmark_data[code]
        if df is None:
            rows.append({
                **benchmark,
                "data_status": "NOT_AVAILABLE",
                "data_rows": 0,
                "data_start": "",
                "data_end": "",
                "calculation_date": fmt_date(calculation_date),
                "available_return_observations": 0,
                "supports_60d": False,
                "supports_120d": False,
                "missing_reason": benchmark_errors.get(code, "BENCHMARK_NOT_AVAILABLE"),
            })
            continue
        current = df[df["date"] <= calculation_date].copy()
        return_observations = max(len(current) - 1, 0)
        rows.append({
            **benchmark,
            "data_status": "AVAILABLE",
            "data_rows": int(len(current)),
            "data_start": fmt_date(current["date"].min()),
            "data_end": fmt_date(current["date"].max()),
            "calculation_date": fmt_date(calculation_date),
            "available_return_observations": int(return_observations),
            "supports_60d": bool(return_observations >= 60),
            "supports_120d": bool(return_observations >= 120),
            "missing_reason": "",
        })
    return pd.DataFrame(rows)


def build_benchmark_redundancy(
    benchmark_data: dict[str, pd.DataFrame | None],
    calculation_date: pd.Timestamp,
) -> pd.DataFrame:
    rows = []
    for window in LOOKBACK_WINDOWS:
        for left, right in combinations(BENCHMARK_BASKET, 2):
            left_df = benchmark_data[left["benchmark_code"]]
            right_df = benchmark_data[right["benchmark_code"]]
            row = {
                "calculation_date": fmt_date(calculation_date),
                "lookback_window": window,
                "benchmark_code_a": left["benchmark_code"],
                "benchmark_family_a": left["benchmark_family"],
                "benchmark_code_b": right["benchmark_code"],
                "benchmark_family_b": right["benchmark_family"],
                "correlation": None,
                "abs_correlation": None,
                "sample_size": 0,
                "redundancy_level": "NOT_AVAILABLE",
                "missing_flag": True,
            }
            if left_df is None or right_df is None:
                rows.append(row)
                continue
            paired = paired_returns(left_df, right_df, calculation_date).tail(window)
            row["sample_size"] = int(len(paired))
            if len(paired) < window:
                rows.append(row)
                continue
            correlation = float(paired["etf_return"].corr(paired["benchmark_return"]))
            if math.isnan(correlation):
                rows.append(row)
                continue
            abs_correlation = abs(correlation)
            level = "HIGH" if abs_correlation >= 0.90 else "MEDIUM" if abs_correlation >= 0.75 else "LOW"
            row.update({
                "correlation": round_float(correlation),
                "abs_correlation": round_float(abs_correlation),
                "redundancy_level": level,
                "missing_flag": False,
            })
            rows.append(row)
    return pd.DataFrame(rows)


def build_single_vs_multi_comparison(vector_df: pd.DataFrame) -> pd.DataFrame:
    available = vector_df[~vector_df["missing_flag"].astype(bool)].copy()
    rows = []
    for (etf_code, etf_name, window), group in available.groupby(
        ["etf_code", "etf_name", "lookback_window"], sort=True
    ):
        core = group[group["benchmark_code"] == CORE_BENCHMARK_CODE]
        if core.empty:
            continue
        core_row = core.iloc[0]
        best = group.sort_values(["r_squared", "correlation"], ascending=False).iloc[0]
        non_core = group[group["benchmark_code"] != CORE_BENCHMARK_CODE]
        best_non_core = non_core.sort_values(["r_squared", "correlation"], ascending=False).iloc[0]
        delta = float(best_non_core["r_squared"] - core_row["r_squared"])
        rows.append({
            "calculation_date": core_row["calculation_date"],
            "universe_version": core_row["universe_version"],
            "etf_code": etf_code,
            "etf_name": etf_name,
            "lookback_window": int(window),
            "core_benchmark_code": CORE_BENCHMARK_CODE,
            "core_beta": core_row["beta"],
            "core_correlation": core_row["correlation"],
            "core_r_squared": core_row["r_squared"],
            "best_benchmark_code": best["benchmark_code"],
            "best_benchmark_family": best["benchmark_family"],
            "best_beta": best["beta"],
            "best_correlation": best["correlation"],
            "best_r_squared": best["r_squared"],
            "best_non_core_benchmark_code": best_non_core["benchmark_code"],
            "best_non_core_benchmark_family": best_non_core["benchmark_family"],
            "best_non_core_r_squared": best_non_core["r_squared"],
            "r_squared_delta_vs_core": round_float(delta),
            "adds_explanatory_dimension": bool(delta >= 0.05),
            "predictive_claim": False,
            "research_only": True,
            "execution_allowed": False,
        })
    return pd.DataFrame(rows)


def build_manifest(
    universe: str,
    universe_df: pd.DataFrame,
    vector_df: pd.DataFrame,
    missing_df: pd.DataFrame,
    coverage_df: pd.DataFrame,
    redundancy_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    calculation_date: pd.Timestamp,
) -> dict[str, Any]:
    available_benchmarks = int((coverage_df["data_status"] == "AVAILABLE").sum())
    high_redundancy = int((redundancy_df["redundancy_level"] == "HIGH").sum())
    explanatory_additions = int(comparison_df["adds_explanatory_dimension"].sum()) if not comparison_df.empty else 0
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S CST"),
        "phase": "Exposure Framework Phase E-B - Multi-Benchmark Market Exposure Prototype",
        "prototype_status": "COMPLETE",
        "universe_version": universe,
        "calculation_date": fmt_date(calculation_date),
        "benchmark_basket_version": BENCHMARK_BASKET_VERSION,
        "benchmark_codes": [item["benchmark_code"] for item in BENCHMARK_BASKET],
        "benchmark_count": len(BENCHMARK_BASKET),
        "available_benchmark_count": available_benchmarks,
        "etf_count": int(len(universe_df)),
        "lookback_windows": list(LOOKBACK_WINDOWS),
        "expected_vector_rows": int(len(universe_df) * len(BENCHMARK_BASKET) * len(LOOKBACK_WINDOWS)),
        "vector_rows": int(len(vector_df)),
        "missing_rows": int(len(missing_df)),
        "benchmark_pair_rows": int(len(redundancy_df)),
        "high_redundancy_pair_rows": high_redundancy,
        "comparison_rows": int(len(comparison_df)),
        "comparison_rows_with_added_explanatory_dimension": explanatory_additions,
        "research_only": True,
        "execution_allowed": False,
        "beta_values_normalized": False,
        "predictive_claim": False,
        "replay_started": False,
        "preview_research_status": "NOT_STARTED",
        "formal_execution_status": "BLOCKED",
        "pit_safety_summary": [
            "All ETF and benchmark return observations are at or before calculation_date.",
            "Each rolling window uses only trailing paired daily returns.",
            "ETF benchmark proxies are marked PIT_SAFE_WITH_PROXY.",
            "Missing benchmarks or insufficient paired history produce explicit missing rows.",
        ],
        "output_files": {
            "values_csv": str(OUTPUT_VALUES_CSV),
            "missing_csv": str(OUTPUT_MISSING_CSV),
            "benchmark_coverage_csv": str(OUTPUT_BENCHMARK_COVERAGE_CSV),
            "benchmark_redundancy_csv": str(OUTPUT_BENCHMARK_REDUNDANCY_CSV),
            "single_vs_multi_csv": str(OUTPUT_COMPARISON_CSV),
            "manifest_json": str(OUTPUT_MANIFEST_JSON),
        },
    }
