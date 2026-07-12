#!/usr/bin/env python3
"""Run the research-only Exposure Framework Phase C prototype."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from exposure.exposure_calculator import run_prototype
from exposure.exposure_config import (
    APPROVED_EXPOSURES,
    DATA_QUALITY_REPORT,
    OUTPUT_COVERAGE_CSV,
    OUTPUT_MANIFEST_JSON,
    OUTPUT_MISSING_CSV,
    OUTPUT_VALUES_CSV,
    OUTPUT_WIDE_CSV,
    SUMMARY_REPORT,
)


def main() -> None:
    universe = sys.argv[1] if len(sys.argv) > 1 else "universe_v2_qualified_research"
    manifest = run_prototype(universe)
    values = pd.read_csv(OUTPUT_VALUES_CSV)
    missing = pd.read_csv(OUTPUT_MISSING_CSV)
    coverage = pd.read_csv(OUTPUT_COVERAGE_CSV)
    SUMMARY_REPORT.write_text(render_summary(manifest, values, missing, coverage), encoding="utf-8")
    DATA_QUALITY_REPORT.write_text(render_data_quality(manifest, values, missing, coverage), encoding="utf-8")
    print("Exposure prototype complete")
    print(f"universe: {manifest['universe_version']}")
    print(f"calculation_date: {manifest['calculation_date']}")
    print(f"etf_count: {manifest['etf_count']}")
    print(f"value_rows: {manifest['value_rows']}")
    print(f"missing_rows: {manifest['missing_rows']}")
    print(f"written: {OUTPUT_VALUES_CSV}")
    print(f"written: {OUTPUT_WIDE_CSV}")
    print(f"written: {OUTPUT_MISSING_CSV}")
    print(f"written: {OUTPUT_COVERAGE_CSV}")
    print(f"written: {OUTPUT_MANIFEST_JSON}")
    print(f"written: {SUMMARY_REPORT}")
    print(f"written: {DATA_QUALITY_REPORT}")


def render_summary(manifest: dict, values: pd.DataFrame, missing: pd.DataFrame, coverage: pd.DataFrame) -> str:
    lines = [
        "# Exposure Prototype Summary",
        "",
        "## Status",
        "",
        "- Phase: Exposure Framework Phase C - Narrow Prototype Development",
        "- Exposure Prototype: COMPLETE",
        "- Scope: NARROW_PRICE_LIQUIDITY_ONLY",
        f"- Universe Version: {manifest['universe_version']}",
        f"- Calculation Date: {manifest['calculation_date']}",
        f"- ETF Count: {manifest['etf_count']}",
        f"- Value Rows: {manifest['value_rows']}",
        f"- Missing Rows: {manifest['missing_rows']}",
        "- Preview Research: NOT_STARTED",
        "- Formal Execution: BLOCKED",
        "- Execution Allowed: false",
        "",
        "## Approved Exposure Scope",
        "",
    ]
    lines.extend(f"- `{name}`" for name in APPROVED_EXPOSURES)
    lines.extend([
        "",
        "No other exposure was calculated.",
        "",
        "## Output Files",
        "",
        f"- Values long format: `{OUTPUT_VALUES_CSV.relative_to(PROJECT_ROOT)}`",
        f"- Values wide format: `{OUTPUT_WIDE_CSV.relative_to(PROJECT_ROOT)}`",
        f"- Missing data: `{OUTPUT_MISSING_CSV.relative_to(PROJECT_ROOT)}`",
        f"- Universe coverage: `{OUTPUT_COVERAGE_CSV.relative_to(PROJECT_ROOT)}`",
        f"- Manifest: `{OUTPUT_MANIFEST_JSON.relative_to(PROJECT_ROOT)}`",
        "",
        "## Exposure Row Counts",
        "",
        "| exposure_name | rows |",
        "| --- | --- |",
    ])
    if values.empty:
        lines.append("| NONE | 0 |")
    else:
        for exposure, count in values.groupby("exposure_name").size().sort_index().items():
            lines.append(f"| {exposure} | {int(count)} |")
    lines.extend([
        "",
        "## Confidence Distribution",
        "",
        "| confidence_level | rows |",
        "| --- | --- |",
    ])
    if values.empty:
        lines.append("| NONE | 0 |")
    else:
        for confidence, count in values.groupby("confidence_level").size().sort_index().items():
            lines.append(f"| {confidence} | {int(count)} |")
    lines.extend([
        "",
        "## Universe Coverage",
        "",
        "| metric | value |",
        "| --- | --- |",
        f"| coverage rows | {len(coverage)} |",
        f"| current for calculation date | {int(coverage['is_current_for_calculation_date'].sum()) if not coverage.empty else 0} |",
        f"| not current for calculation date | {int((~coverage['is_current_for_calculation_date'].astype(bool)).sum()) if not coverage.empty else 0} |",
        "",
        "## PIT Safety Notes",
        "",
    ])
    lines.extend(f"- {note}" for note in manifest.get("pit_safety_summary", []))
    lines.extend([
        "",
        "## Boundary",
        "",
        "- Research only: true",
        "- ETF daily source: `data/etf_daily/`",
        "- ETF daily copied: false",
        "- Ranking changed: false",
        "- Strategy changed: false",
        "- Preview created: false",
        "- Formal execution changed: false",
    ])
    return "\n".join(lines) + "\n"


def render_data_quality(manifest: dict, values: pd.DataFrame, missing: pd.DataFrame, coverage: pd.DataFrame) -> str:
    lines = [
        "# Exposure Prototype Data Quality",
        "",
        "## Summary",
        "",
        f"- Universe Version: {manifest['universe_version']}",
        f"- Calculation Date: {manifest['calculation_date']}",
        f"- ETF Count: {manifest['etf_count']}",
        f"- Missing Rows: {manifest['missing_rows']}",
        f"- Single ETF Data Source: {manifest['single_source_of_truth']}",
        f"- ETF Daily Copied: {manifest['etf_daily_copied']}",
        "",
        "## Missing Data By Exposure",
        "",
        "| exposure_name | missing_rows | reasons |",
        "| --- | --- | --- |",
    ]
    if missing.empty:
        lines.append("| NONE | 0 |  |")
    else:
        for exposure, sub in missing.groupby("exposure_name"):
            reasons = ", ".join(f"{k}={v}" for k, v in sub["missing_data_reason"].value_counts().sort_index().items())
            lines.append(f"| {exposure} | {len(sub)} | {reasons} |")
    lines.extend([
        "",
        "## Coverage By ETF",
        "",
        "| symbol | name | price_rows | data_start | data_end | current_for_calculation_date |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for _, row in coverage.sort_values("symbol").iterrows():
        lines.append(
            f"| {row['symbol']} | {row['name']} | {int(row['price_rows'])} | {row['data_start']} | {row['data_end']} | {row['is_current_for_calculation_date']} |"
        )
    lines.extend([
        "",
        "## Metric Quality Notes",
        "",
        "- `market_beta` uses `510300` as a default A-share broad-market proxy and is marked `PIT_SAFE_WITH_PROXY`.",
        "- `realized_volatility`, `downside_drawdown_risk`, `trading_liquidity`, and `return_momentum` are calculated from each ETF's own historical daily data ending at calculation date.",
        "- Missing data is explicit; no forward fill is used for unavailable rolling windows.",
        "- This prototype does not use future returns, future classifications, holdings, constituents, strategy outputs, preview outputs, or execution data.",
    ])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()

