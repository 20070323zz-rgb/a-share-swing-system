"""Configuration for the research-only Exposure Framework prototype.

Phase C scope is intentionally narrow. Do not add exposures here unless a
future governance batch approves them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import DATA_DIR, ETF_DAILY_DIR, PROJECT_ROOT, REPORT_DIR


RESEARCH_OUTPUT_DIR = DATA_DIR / "research" / "exposure_prototype"
UNIVERSE_V2_REGISTRY = PROJECT_ROOT / "configs" / "universe_versions" / "universe_v2_registry.yaml"
BACKTEST_TRADE_POOL = DATA_DIR / "backtest_trade_pool.csv"

BENCHMARK_SYMBOL = "510300"
DEFAULT_UNIVERSE_VERSION = "universe_v2_qualified_research"

APPROVED_EXPOSURES = [
    "market_beta",
    "realized_volatility",
    "downside_drawdown_risk",
    "trading_liquidity",
    "return_momentum",
]


@dataclass(frozen=True)
class PrototypeWindowConfig:
    beta_windows: tuple[int, ...] = (60, 120)
    volatility_windows: tuple[int, ...] = (20, 60)
    drawdown_windows: tuple[int, ...] = (60, 120)
    liquidity_windows: tuple[int, ...] = (20, 60)
    momentum_windows: tuple[int, ...] = (20, 60, 120)
    annualization_days: int = 252


WINDOW_CONFIG = PrototypeWindowConfig()


OUTPUT_VALUES_CSV = RESEARCH_OUTPUT_DIR / "exposure_prototype_values.csv"
OUTPUT_WIDE_CSV = RESEARCH_OUTPUT_DIR / "exposure_prototype_wide.csv"
OUTPUT_MISSING_CSV = RESEARCH_OUTPUT_DIR / "exposure_prototype_missing_data.csv"
OUTPUT_COVERAGE_CSV = RESEARCH_OUTPUT_DIR / "exposure_prototype_universe_coverage.csv"
OUTPUT_MANIFEST_JSON = RESEARCH_OUTPUT_DIR / "exposure_prototype_manifest.json"

SUMMARY_REPORT = REPORT_DIR / "exposure_prototype_summary.md"
DATA_QUALITY_REPORT = REPORT_DIR / "exposure_prototype_data_quality.md"


def price_file_candidates(symbol: str) -> list[Path]:
    return [
        ETF_DAILY_DIR / f"sh_{symbol}.csv",
        ETF_DAILY_DIR / f"sz_{symbol}.csv",
    ]

