#!/usr/bin/env python3
"""Run the research-only multi-benchmark Market Exposure vector prototype."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from exposure.market_exposure_vector import (
    BENCHMARK_BASKET,
    CORE_BENCHMARK_CODE,
    LOOKBACK_WINDOWS,
    OUTPUT_BENCHMARK_COVERAGE_CSV,
    OUTPUT_BENCHMARK_REDUNDANCY_CSV,
    OUTPUT_COMPARISON_CSV,
    OUTPUT_MANIFEST_JSON,
    OUTPUT_MISSING_CSV,
    OUTPUT_VALUES_CSV,
    REDUNDANCY_REPORT,
    SUMMARY_REPORT,
    run_market_exposure_vector,
)


def main() -> None:
    universe = sys.argv[1] if len(sys.argv) > 1 else "universe_v2_qualified_research"
    manifest = run_market_exposure_vector(universe)

    vector = pd.read_csv(OUTPUT_VALUES_CSV, dtype={"etf_code": str, "benchmark_code": str})
    missing = pd.read_csv(OUTPUT_MISSING_CSV, dtype={"etf_code": str, "benchmark_code": str})
    coverage = pd.read_csv(OUTPUT_BENCHMARK_COVERAGE_CSV, dtype={"benchmark_code": str})
    redundancy = pd.read_csv(
        OUTPUT_BENCHMARK_REDUNDANCY_CSV,
        dtype={"benchmark_code_a": str, "benchmark_code_b": str},
    )
    comparison = pd.read_csv(
        OUTPUT_COMPARISON_CSV,
        dtype={
            "etf_code": str,
            "core_benchmark_code": str,
            "best_benchmark_code": str,
            "best_non_core_benchmark_code": str,
        },
    )

    validate_outputs(manifest, vector, missing, coverage, redundancy, comparison)
    SUMMARY_REPORT.write_text(
        render_summary(manifest, vector, missing, coverage, comparison),
        encoding="utf-8",
    )
    REDUNDANCY_REPORT.write_text(
        render_redundancy(manifest, redundancy),
        encoding="utf-8",
    )

    print("Market Exposure vector prototype complete")
    print(f"universe: {manifest['universe_version']}")
    print(f"calculation_date: {manifest['calculation_date']}")
    print(f"etf_count: {manifest['etf_count']}")
    print(f"available_benchmarks: {manifest['available_benchmark_count']}/{manifest['benchmark_count']}")
    print(f"vector_rows: {manifest['vector_rows']}")
    print(f"missing_rows: {manifest['missing_rows']}")
    print(f"added_explanatory_rows: {manifest['comparison_rows_with_added_explanatory_dimension']}")
    print(f"written: {OUTPUT_VALUES_CSV}")
    print(f"written: {OUTPUT_MISSING_CSV}")
    print(f"written: {OUTPUT_BENCHMARK_COVERAGE_CSV}")
    print(f"written: {OUTPUT_BENCHMARK_REDUNDANCY_CSV}")
    print(f"written: {OUTPUT_COMPARISON_CSV}")
    print(f"written: {OUTPUT_MANIFEST_JSON}")
    print(f"written: {SUMMARY_REPORT}")
    print(f"written: {REDUNDANCY_REPORT}")


def validate_outputs(
    manifest: dict,
    vector: pd.DataFrame,
    missing: pd.DataFrame,
    coverage: pd.DataFrame,
    redundancy: pd.DataFrame,
    comparison: pd.DataFrame,
) -> None:
    required_columns = {
        "etf_code",
        "benchmark_code",
        "calculation_date",
        "lookback_window",
        "beta",
        "correlation",
        "r_squared",
        "sample_size",
        "confidence",
        "PIT_status",
        "missing_flag",
        "research_only",
        "execution_allowed",
    }
    missing_columns = sorted(required_columns - set(vector.columns))
    if missing_columns:
        raise AssertionError(f"missing required output columns: {missing_columns}")

    if len(vector) != manifest["expected_vector_rows"]:
        raise AssertionError("vector row count does not match ETF x benchmark x window grain")
    if vector["etf_code"].nunique() != manifest["etf_count"]:
        raise AssertionError("ETF coverage does not match manifest")
    if vector["benchmark_code"].nunique() != manifest["benchmark_count"]:
        raise AssertionError("benchmark coverage does not match manifest")
    if set(vector["lookback_window"].astype(int)) != set(LOOKBACK_WINDOWS):
        raise AssertionError("lookback window coverage is incomplete")

    missing_flags = as_bool(vector["missing_flag"])
    if int(missing_flags.sum()) != len(missing):
        raise AssertionError("missing row count is inconsistent")
    if as_bool(vector["execution_allowed"]).any():
        raise AssertionError("execution_allowed must remain false")
    if not as_bool(vector["research_only"]).all():
        raise AssertionError("all vector rows must remain research_only")
    if manifest.get("beta_values_normalized") is not False:
        raise AssertionError("beta values must not be normalized")
    if manifest.get("predictive_claim") is not False:
        raise AssertionError("prototype must not make a predictive claim")

    calculated = vector[~missing_flags].copy()
    if calculated[["beta", "correlation", "r_squared"]].isna().any().any():
        raise AssertionError("calculated rows contain missing exposure metrics")
    if not (calculated["sample_size"].astype(int) >= calculated["lookback_window"].astype(int)).all():
        raise AssertionError("calculated rows do not satisfy minimum paired history")
    if not (pd.to_datetime(calculated["window_end_date"]) <= pd.Timestamp(manifest["calculation_date"])).all():
        raise AssertionError("PIT violation: a window ends after calculation_date")
    if set(calculated["PIT_status"]) != {"PIT_SAFE_WITH_PROXY"}:
        raise AssertionError("calculated rows have an unexpected PIT status")

    if len(coverage) != len(BENCHMARK_BASKET):
        raise AssertionError("benchmark coverage report is incomplete")
    if comparison.empty:
        raise AssertionError("single-vs-multi comparison is empty")
    if as_bool(comparison["predictive_claim"]).any():
        raise AssertionError("comparison must not make predictive claims")
    if redundancy.empty:
        raise AssertionError("benchmark redundancy output is empty")


def render_summary(
    manifest: dict,
    vector: pd.DataFrame,
    missing: pd.DataFrame,
    coverage: pd.DataFrame,
    comparison: pd.DataFrame,
) -> str:
    comparison_60 = comparison[comparison["lookback_window"].astype(int) == 60].copy()
    comparison_120 = comparison[comparison["lookback_window"].astype(int) == 120].copy()
    dominant_window = comparison_60[["etf_code", "best_benchmark_code"]].merge(
        comparison_120[["etf_code", "best_benchmark_code"]],
        on="etf_code",
        how="inner",
        suffixes=("_60d", "_120d"),
    )
    dominant_consistency = int(
        (dominant_window["best_benchmark_code_60d"] == dominant_window["best_benchmark_code_120d"]).sum()
    )

    calculated = vector[~as_bool(vector["missing_flag"])].copy()
    beta_window_stability = []
    for benchmark_code, group in calculated.groupby("benchmark_code"):
        pivot = group.pivot_table(index="etf_code", columns="lookback_window", values="beta", aggfunc="last")
        if 60 not in pivot.columns or 120 not in pivot.columns:
            rank_correlation = None
        else:
            rank_correlation = pivot[60].rank().corr(pivot[120].rank())
        beta_window_stability.append((benchmark_code, rank_correlation))

    dominant_count = comparison_120["best_benchmark_family"].nunique()
    differentiation_verdict = (
        "STRONG_DIFFERENTIATION"
        if dominant_count >= 3
        else "DIFFERENTIATION_PRESENT"
        if dominant_count >= 2
        else "LIMITED_DIFFERENTIATION"
    )
    added_count = int(as_bool(comparison["adds_explanatory_dimension"]).sum())
    added_120 = int(as_bool(comparison_120["adds_explanatory_dimension"]).sum())
    explanatory_verdict = "ADDS_EXPLANATORY_DIMENSION" if added_count > 0 else "NO_CLEAR_ADDITION"

    lines = [
        "# Market Exposure Vector Summary",
        "",
        "## Status",
        "",
        "- Phase: Exposure Framework Phase E-B - Multi-Benchmark Market Exposure Prototype",
        "- Multi-Benchmark Market Exposure Prototype: COMPLETE",
        "- Market Exposure Vector: RESEARCH_ONLY",
        f"- Universe Version: {manifest['universe_version']}",
        f"- Calculation Date: {manifest['calculation_date']}",
        f"- ETF Count: {manifest['etf_count']}",
        f"- Benchmark Basket Version: {manifest['benchmark_basket_version']}",
        f"- Available Benchmarks: {manifest['available_benchmark_count']}/{manifest['benchmark_count']}",
        f"- Vector Rows: {manifest['vector_rows']}",
        f"- Missing Rows: {manifest['missing_rows']}",
        "- Preview Research: NOT_STARTED",
        "- Formal Execution: BLOCKED",
        "",
        "## Benchmark Basket Availability",
        "",
        "| benchmark_code | family | status | data_start | data_end | return_observations | 60d | 120d |",
        "| --- | --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for _, row in coverage.sort_values("benchmark_code").iterrows():
        lines.append(
            f"| {row['benchmark_code']} | {row['benchmark_family']} | {row['data_status']} | "
            f"{row['data_start']} | {row['data_end']} | {int(row['available_return_observations'])} | "
            f"{row['supports_60d']} | {row['supports_120d']} |"
        )

    lines.extend([
        "",
        "## Coverage Validation",
        "",
        f"- Expected grain rows: {manifest['expected_vector_rows']}",
        f"- Actual rows: {len(vector)}",
        f"- ETF coverage: {vector['etf_code'].nunique()}",
        f"- Benchmark coverage: {vector['benchmark_code'].nunique()}",
        f"- Lookback windows: {', '.join(str(v) + 'd' for v in sorted(vector['lookback_window'].unique()))}",
        f"- Missing rows: {len(missing)}",
        "",
        "## Single 510300 vs Multi-Benchmark",
        "",
        f"- Explanatory verdict: {explanatory_verdict}",
        f"- Comparison rows with non-core R-squared improvement >= 0.05: {added_count}/{len(comparison)}",
        f"- 120d rows with non-core R-squared improvement >= 0.05: {added_120}/{len(comparison_120)}",
        "- Interpretation: the comparison measures contemporaneous return explanation only; it does not test or claim return prediction.",
        "",
        "## 60d vs 120d Window Comparison",
        "",
        f"- Dominant benchmark consistency: {dominant_consistency}/{len(dominant_window)} ETFs",
        "- Beta rank stability by benchmark:",
        "",
        "| benchmark | 60d vs 120d beta rank correlation |",
        "| --- | ---: |",
    ])
    for benchmark_code, rank_correlation in beta_window_stability:
        rendered = "NOT_AVAILABLE" if rank_correlation is None or pd.isna(rank_correlation) else f"{rank_correlation:.3f}"
        lines.append(f"| {benchmark_code} | {rendered} |")
    lines.extend([
        "",
        "Window differences are retained as research information. The prototype does not average or overwrite 60d and 120d vectors.",
        "",
        "## 120d ETF Differentiation",
        "",
        f"- Differentiation verdict: {differentiation_verdict}",
        f"- Distinct dominant benchmark families: {dominant_count}",
        "",
        "| ETF | name | 510300 R2 | best benchmark | best family | best R2 | fit quality | non-core delta | added dimension |",
        "| --- | --- | ---: | --- | --- | ---: | --- | ---: | --- |",
    ])
    for _, row in comparison_120.sort_values("etf_code").iterrows():
        fit_quality = "STRONG" if row["best_r_squared"] >= 0.60 else "MODERATE" if row["best_r_squared"] >= 0.30 else "WEAK"
        lines.append(
            f"| {row['etf_code']} | {row['etf_name']} | {row['core_r_squared']:.3f} | "
            f"{row['best_benchmark_code']} | {row['best_benchmark_family']} | {row['best_r_squared']:.3f} | "
            f"{fit_quality} | {row['r_squared_delta_vs_core']:.3f} | {row['adds_explanatory_dimension']} |"
        )

    lines.extend([
        "",
        "## Confidence and PIT",
        "",
        "| confidence | rows |",
        "| --- | ---: |",
    ])
    for confidence, count in vector[~as_bool(vector["missing_flag"])]["confidence"].value_counts().sort_index().items():
        lines.append(f"| {confidence} | {int(count)} |")
    lines.extend([
        "",
        "- All calculated rows are `PIT_SAFE_WITH_PROXY`.",
        "- Rolling windows use trailing paired returns ending no later than calculation date.",
        "- Beta values are raw sensitivities and are not normalized to sum to 1.",
        "",
        "## Research Interpretation",
        "",
        "The prototype adds explanatory dimensions when an ETF is more closely aligned with a non-core market segment than with 510300. The vector should be retained as a research artifact because it preserves broad, size, growth, technology, and defensive sensitivities without compressing them into one scalar.",
        "",
        "Important limits:",
        "",
        "- A highest R-squared benchmark is a relative statistical fit, not an economic classification.",
        "- Resource/cyclical ETF 561360 lacks a dedicated resource benchmark in basket V1; its defensive benchmark fit must not be interpreted as a defensive label.",
        "- ETF 159516 has weak maximum 120d R-squared, showing that basket V1 does not adequately explain every sector/thematic ETF.",
        "- 510500 and 512100 are highly correlated in both windows; future validation should test whether their ETF-level differentiation justifies retaining both.",
        "",
        "## Output Files",
        "",
        f"- Vector values: `{OUTPUT_VALUES_CSV.relative_to(PROJECT_ROOT)}`",
        f"- Missing rows: `{OUTPUT_MISSING_CSV.relative_to(PROJECT_ROOT)}`",
        f"- Benchmark coverage: `{OUTPUT_BENCHMARK_COVERAGE_CSV.relative_to(PROJECT_ROOT)}`",
        f"- Benchmark redundancy data: `{OUTPUT_BENCHMARK_REDUNDANCY_CSV.relative_to(PROJECT_ROOT)}`",
        f"- Single vs multi comparison: `{OUTPUT_COMPARISON_CSV.relative_to(PROJECT_ROOT)}`",
        f"- Manifest: `{OUTPUT_MANIFEST_JSON.relative_to(PROJECT_ROOT)}`",
        "",
        "## Boundary",
        "",
        "- Research only: true",
        "- Predictive claim: false",
        "- Replay started: false",
        "- Ranking changed: false",
        "- Score changed: false",
        "- Strategy changed: false",
        "- Preview created: false",
        "- Formal execution changed: false",
        "- Paper execution affected: false",
    ])
    return "\n".join(lines) + "\n"


def render_redundancy(manifest: dict, redundancy: pd.DataFrame) -> str:
    available = redundancy[~as_bool(redundancy["missing_flag"])].copy()
    high = available[available["redundancy_level"] == "HIGH"]
    high_share = len(high) / len(available) if len(available) else 0.0
    verdict = (
        "SEVERE_REDUNDANCY"
        if high_share >= 0.50
        else "LOCALIZED_HIGH_REDUNDANCY"
        if len(high)
        else "NO_SEVERE_REDUNDANCY"
    )
    codes = [item["benchmark_code"] for item in BENCHMARK_BASKET]
    lines = [
        "# Benchmark Redundancy Analysis",
        "",
        "## Verdict",
        "",
        f"- Benchmark Redundancy Verdict: {verdict}",
        f"- Available pair-window rows: {len(available)}",
        f"- HIGH redundancy rows (absolute correlation >= 0.90): {len(high)}",
        f"- HIGH redundancy share: {high_share:.1%}",
        "- High correlation is evaluated as basket redundancy, not as evidence that two indices are economically identical.",
    ]

    for window in LOOKBACK_WINDOWS:
        sub = available[available["lookback_window"].astype(int) == window]
        matrix = pd.DataFrame(index=codes, columns=codes, dtype=float)
        for code in codes:
            matrix.loc[code, code] = 1.0
        for _, row in sub.iterrows():
            left = row["benchmark_code_a"]
            right = row["benchmark_code_b"]
            matrix.loc[left, right] = row["correlation"]
            matrix.loc[right, left] = row["correlation"]
        lines.extend([
            "",
            f"## {window}d Correlation Matrix",
            "",
            "| benchmark | " + " | ".join(codes) + " |",
            "| --- | " + " | ".join("---:" for _ in codes) + " |",
        ])
        for code in codes:
            values = ["" if pd.isna(matrix.loc[code, other]) else f"{matrix.loc[code, other]:.3f}" for other in codes]
            lines.append(f"| {code} | " + " | ".join(values) + " |")

    lines.extend([
        "",
        "## High and Medium Redundancy Pairs",
        "",
        "| window | benchmark A | family A | benchmark B | family B | correlation | level |",
        "| ---: | --- | --- | --- | --- | ---: | --- |",
    ])
    material = available[available["redundancy_level"].isin(["HIGH", "MEDIUM"])].copy()
    if material.empty:
        lines.append("|  | NONE |  |  |  |  |  |")
    else:
        for _, row in material.sort_values(["lookback_window", "abs_correlation"], ascending=[True, False]).iterrows():
            lines.append(
                f"| {int(row['lookback_window'])} | {row['benchmark_code_a']} | {row['benchmark_family_a']} | "
                f"{row['benchmark_code_b']} | {row['benchmark_family_b']} | {row['correlation']:.3f} | {row['redundancy_level']} |"
            )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- A redundant pair may still be retained when the benchmarks represent distinct size or board definitions and create different ETF-level loadings.",
        "- If redundancy is severe across both windows, the next validation phase should test whether one benchmark can be removed without losing ETF differentiation.",
        "- This report does not change the basket automatically.",
        "",
        "## Boundary",
        "",
        f"- Calculation date: {manifest['calculation_date']}",
        "- Research only: true",
        "- Predictive claim: false",
        "- Strategy / Ranking / Score / Preview / Formal Execution: unchanged",
    ])
    return "\n".join(lines) + "\n"


def as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


if __name__ == "__main__":
    main()
