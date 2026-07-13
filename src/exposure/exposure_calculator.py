"""Research-only narrow Exposure Framework prototype calculator.

This module calculates only the five Phase C approved price/liquidity-derived
exposures. It does not read or write strategy, ranking, preview, paper-trading,
or execution files.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from exposure.exposure_config import (
    APPROVED_EXPOSURES,
    BACKTEST_TRADE_POOL,
    BENCHMARK_SYMBOL,
    DEFAULT_UNIVERSE_VERSION,
    OUTPUT_COVERAGE_CSV,
    OUTPUT_MANIFEST_JSON,
    OUTPUT_MISSING_CSV,
    OUTPUT_VALUES_CSV,
    OUTPUT_WIDE_CSV,
    RESEARCH_OUTPUT_DIR,
    UNIVERSE_V2_REGISTRY,
    WINDOW_CONFIG,
    price_file_candidates,
)


MISSING_COLUMNS = [
    "calculation_date",
    "universe_version",
    "symbol",
    "name",
    "exposure_name",
    "lookback_window",
    "missing_data_flag",
    "missing_data_reason",
    "available_observations",
    "required_observations",
    "point_in_time_status",
    "confidence_level",
    "research_only",
    "execution_allowed",
]


def run_prototype(universe: str = DEFAULT_UNIVERSE_VERSION) -> dict[str, Any]:
    universe_df = load_universe(universe)
    price_data = {symbol: load_price_data(symbol) for symbol in universe_df["symbol"].tolist()}
    benchmark = load_price_data(BENCHMARK_SYMBOL)
    calculation_date = latest_common_calculation_date(price_data, benchmark)

    values: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []

    for _, row in universe_df.iterrows():
        symbol = str(row["symbol"]).zfill(6)
        df = price_data[symbol]
        coverage_rows.append(coverage_row(symbol, row, df, calculation_date))
        calculate_symbol_exposures(
            values=values,
            missing=missing,
            symbol=symbol,
            name=str(row.get("name", symbol)),
            universe_version=universe,
            price_df=df,
            benchmark_df=benchmark,
            calculation_date=calculation_date,
        )

    values_df = pd.DataFrame(values)
    missing_df = pd.DataFrame(missing, columns=MISSING_COLUMNS)
    coverage_df = pd.DataFrame(coverage_rows)
    wide_df = build_wide(values_df)

    RESEARCH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    values_df.to_csv(OUTPUT_VALUES_CSV, index=False)
    wide_df.to_csv(OUTPUT_WIDE_CSV, index=False)
    missing_df.to_csv(OUTPUT_MISSING_CSV, index=False)
    coverage_df.to_csv(OUTPUT_COVERAGE_CSV, index=False)

    manifest = build_manifest(universe, universe_df, values_df, missing_df, coverage_df, calculation_date)
    OUTPUT_MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def load_universe(universe: str) -> pd.DataFrame:
    if universe in {"universe_v2", "universe_v2_qualified_research", "v2"}:
        records = yaml.safe_load(UNIVERSE_V2_REGISTRY.read_text(encoding="utf-8"))["records"]
        rows = []
        for record in records:
            if str(record.get("qualification_verdict")) != "QUALIFIED_RESEARCH":
                continue
            rows.append({
                "symbol": normalize_symbol(record.get("etf_code")),
                "name": record.get("etf_name", ""),
                "universe_version": "universe_v2_qualified_research",
                "qualification_verdict": record.get("qualification_verdict", ""),
                "source": str(UNIVERSE_V2_REGISTRY.relative_to(UNIVERSE_V2_REGISTRY.parents[2])),
            })
        return pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)
    if universe in {"universe_v1", "v1"}:
        df = pd.read_csv(BACKTEST_TRADE_POOL, dtype=str).fillna("")
        return pd.DataFrame({
            "symbol": df["symbol"].map(normalize_symbol),
            "name": df["name"],
            "universe_version": "universe_v1_backtest_trade_pool",
            "qualification_verdict": "V1_TRADE_POOL",
            "source": str(BACKTEST_TRADE_POOL.relative_to(BACKTEST_TRADE_POOL.parents[1])),
        }).drop_duplicates("symbol").sort_values("symbol").reset_index(drop=True)
    raise ValueError(f"unsupported universe: {universe}")


def load_price_data(symbol: str) -> pd.DataFrame:
    path = next((p for p in price_file_candidates(normalize_symbol(symbol)) if p.exists()), None)
    if path is None:
        raise FileNotFoundError(f"missing ETF daily file for {symbol}")
    df = pd.read_csv(path)
    if df.empty or "date" not in df.columns:
        raise ValueError(f"invalid ETF daily file for {symbol}: {path}")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["open", "high", "low", "close", "volume", "amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "amount" not in df.columns:
        df["amount"] = pd.NA
    if "volume" not in df.columns:
        df["volume"] = pd.NA
    df = (
        df.dropna(subset=["date", "close"])
        .sort_values("date")
        .drop_duplicates("date", keep="last")
        .reset_index(drop=True)
    )
    df["symbol"] = normalize_symbol(symbol)
    df["source_file"] = str(path)
    return df


def latest_common_calculation_date(price_data: dict[str, pd.DataFrame], benchmark: pd.DataFrame) -> pd.Timestamp:
    latest_dates = [df["date"].max() for df in price_data.values()]
    latest_dates.append(benchmark["date"].max())
    return pd.Timestamp(min(latest_dates))


def calculate_symbol_exposures(
    values: list[dict[str, Any]],
    missing: list[dict[str, Any]],
    symbol: str,
    name: str,
    universe_version: str,
    price_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    calculation_date: pd.Timestamp,
) -> None:
    price_df = price_df[price_df["date"] <= calculation_date].copy()
    benchmark_df = benchmark_df[benchmark_df["date"] <= calculation_date].copy()
    add_market_beta(values, missing, symbol, name, universe_version, price_df, benchmark_df, calculation_date)
    add_realized_volatility(values, missing, symbol, name, universe_version, price_df, calculation_date)
    add_downside_drawdown(values, missing, symbol, name, universe_version, price_df, calculation_date)
    add_trading_liquidity(values, missing, symbol, name, universe_version, price_df, calculation_date)
    add_return_momentum(values, missing, symbol, name, universe_version, price_df, calculation_date)


def add_market_beta(values: list[dict[str, Any]], missing: list[dict[str, Any]], symbol: str, name: str, universe_version: str, price_df: pd.DataFrame, benchmark_df: pd.DataFrame, calculation_date: pd.Timestamp) -> None:
    exposure = "market_beta"
    merged = pd.merge(
        price_df[["date", "close"]].rename(columns={"close": "close_symbol"}),
        benchmark_df[["date", "close"]].rename(columns={"close": "close_benchmark"}),
        on="date",
        how="inner",
    ).sort_values("date")
    merged["ret_symbol"] = merged["close_symbol"].pct_change(fill_method=None)
    merged["ret_benchmark"] = merged["close_benchmark"].pct_change(fill_method=None)
    for window in WINDOW_CONFIG.beta_windows:
        sub = merged.dropna(subset=["ret_symbol", "ret_benchmark"]).tail(window)
        if len(sub) < window:
            append_missing(missing, symbol, name, universe_version, exposure, window, calculation_date, "INSUFFICIENT_HISTORY", len(sub), window)
            continue
        variance = float(sub["ret_benchmark"].var(ddof=1))
        if variance == 0 or math.isnan(variance):
            append_missing(missing, symbol, name, universe_version, exposure, window, calculation_date, "ZERO_BENCHMARK_VARIANCE", len(sub), window)
            continue
        covariance = float(sub[["ret_symbol", "ret_benchmark"]].cov().iloc[0, 1])
        beta = covariance / variance
        correlation = float(sub["ret_symbol"].corr(sub["ret_benchmark"]))
        append_value(
            values,
            symbol,
            name,
            universe_version,
            exposure,
            "beta",
            window,
            beta,
            calculation_date,
            sub["date"].iloc[0],
            sub["date"].iloc[-1],
            "PIT_SAFE_WITH_PROXY",
            "HIGH" if window >= 120 else "MEDIUM",
            {"benchmark_symbol": BENCHMARK_SYMBOL, "correlation": correlation, "observations": len(sub)},
        )


def add_realized_volatility(values: list[dict[str, Any]], missing: list[dict[str, Any]], symbol: str, name: str, universe_version: str, price_df: pd.DataFrame, calculation_date: pd.Timestamp) -> None:
    exposure = "realized_volatility"
    returns = price_df[["date", "close"]].copy()
    returns["ret"] = returns["close"].pct_change(fill_method=None)
    for window in WINDOW_CONFIG.volatility_windows:
        sub = returns.dropna(subset=["ret"]).tail(window)
        if len(sub) < window:
            append_missing(missing, symbol, name, universe_version, exposure, window, calculation_date, "INSUFFICIENT_HISTORY", len(sub), window)
            continue
        vol = float(sub["ret"].std(ddof=1) * math.sqrt(WINDOW_CONFIG.annualization_days))
        append_value(values, symbol, name, universe_version, exposure, "annualized_volatility", window, vol, calculation_date, sub["date"].iloc[0], sub["date"].iloc[-1], "PIT_SAFE", "HIGH", {"observations": len(sub)})


def add_downside_drawdown(values: list[dict[str, Any]], missing: list[dict[str, Any]], symbol: str, name: str, universe_version: str, price_df: pd.DataFrame, calculation_date: pd.Timestamp) -> None:
    exposure = "downside_drawdown_risk"
    returns = price_df[["date", "close"]].copy()
    returns["ret"] = returns["close"].pct_change(fill_method=None)
    for window in WINDOW_CONFIG.drawdown_windows:
        price_sub = price_df.dropna(subset=["close"]).tail(window)
        ret_sub = returns.dropna(subset=["ret"]).tail(window)
        if len(price_sub) < window or len(ret_sub) < window:
            append_missing(missing, symbol, name, universe_version, exposure, window, calculation_date, "INSUFFICIENT_HISTORY", min(len(price_sub), len(ret_sub)), window)
            continue
        running_max = price_sub["close"].cummax()
        drawdown = price_sub["close"] / running_max - 1.0
        max_drawdown = float(drawdown.min())
        downside = ret_sub["ret"].where(ret_sub["ret"] < 0).dropna()
        downside_vol = float(downside.std(ddof=1) * math.sqrt(WINDOW_CONFIG.annualization_days)) if len(downside) >= 2 else 0.0
        append_value(values, symbol, name, universe_version, exposure, "max_drawdown", window, max_drawdown, calculation_date, price_sub["date"].iloc[0], price_sub["date"].iloc[-1], "PIT_SAFE", "HIGH", {"observations": len(price_sub)})
        append_value(values, symbol, name, universe_version, exposure, "downside_volatility", window, downside_vol, calculation_date, ret_sub["date"].iloc[0], ret_sub["date"].iloc[-1], "PIT_SAFE", "HIGH", {"observations": len(ret_sub), "downside_observations": len(downside)})


def add_trading_liquidity(values: list[dict[str, Any]], missing: list[dict[str, Any]], symbol: str, name: str, universe_version: str, price_df: pd.DataFrame, calculation_date: pd.Timestamp) -> None:
    exposure = "trading_liquidity"
    for window in WINDOW_CONFIG.liquidity_windows:
        sub = price_df.tail(window)
        if len(sub) < window:
            append_missing(missing, symbol, name, universe_version, exposure, window, calculation_date, "INSUFFICIENT_HISTORY", len(sub), window)
            continue
        amount = pd.to_numeric(sub.get("amount"), errors="coerce")
        volume = pd.to_numeric(sub.get("volume"), errors="coerce")
        if amount.notna().sum() >= window:
            append_value(values, symbol, name, universe_version, exposure, "avg_amount", window, float(amount.mean()), calculation_date, sub["date"].iloc[0], sub["date"].iloc[-1], "PIT_SAFE", "HIGH", {"observations": len(sub)})
        else:
            append_missing(missing, symbol, name, universe_version, exposure, window, calculation_date, "MISSING_AMOUNT", int(amount.notna().sum()), window)
        if volume.notna().sum() >= window:
            append_value(values, symbol, name, universe_version, exposure, "avg_volume", window, float(volume.mean()), calculation_date, sub["date"].iloc[0], sub["date"].iloc[-1], "PIT_SAFE", "HIGH", {"observations": len(sub)})
        else:
            append_missing(missing, symbol, name, universe_version, exposure, window, calculation_date, "MISSING_VOLUME", int(volume.notna().sum()), window)


def add_return_momentum(values: list[dict[str, Any]], missing: list[dict[str, Any]], symbol: str, name: str, universe_version: str, price_df: pd.DataFrame, calculation_date: pd.Timestamp) -> None:
    exposure = "return_momentum"
    for window in WINDOW_CONFIG.momentum_windows:
        sub = price_df.dropna(subset=["close"]).tail(window + 1)
        if len(sub) < window + 1:
            append_missing(missing, symbol, name, universe_version, exposure, window, calculation_date, "INSUFFICIENT_HISTORY", max(len(sub) - 1, 0), window)
            continue
        start = float(sub["close"].iloc[0])
        end = float(sub["close"].iloc[-1])
        if start == 0:
            append_missing(missing, symbol, name, universe_version, exposure, window, calculation_date, "ZERO_START_PRICE", len(sub) - 1, window)
            continue
        value = end / start - 1.0
        append_value(values, symbol, name, universe_version, exposure, "past_return", window, value, calculation_date, sub["date"].iloc[0], sub["date"].iloc[-1], "PIT_SAFE", "HIGH", {"observations": len(sub) - 1})


def append_value(
    values: list[dict[str, Any]],
    symbol: str,
    name: str,
    universe_version: str,
    exposure_name: str,
    metric_name: str,
    lookback_window: int,
    value: float,
    calculation_date: pd.Timestamp,
    window_start_date: pd.Timestamp,
    window_end_date: pd.Timestamp,
    pit_status: str,
    confidence_level: str,
    notes: dict[str, Any] | None = None,
) -> None:
    values.append({
        "calculation_date": fmt_date(calculation_date),
        "universe_version": universe_version,
        "symbol": symbol,
        "name": name,
        "exposure_name": exposure_name,
        "metric_name": metric_name,
        "lookback_window": int(lookback_window),
        "exposure_value": round_float(value),
        "window_start_date": fmt_date(window_start_date),
        "window_end_date": fmt_date(window_end_date),
        "point_in_time_status": pit_status,
        "confidence_level": confidence_level,
        "missing_data_flag": False,
        "missing_data_reason": "",
        "source_data": "data/etf_daily",
        "research_only": True,
        "execution_allowed": False,
        "notes": json.dumps(notes or {}, ensure_ascii=False, sort_keys=True),
    })


def append_missing(
    missing: list[dict[str, Any]],
    symbol: str,
    name: str,
    universe_version: str,
    exposure_name: str,
    lookback_window: int,
    calculation_date: pd.Timestamp,
    reason: str,
    available_observations: int,
    required_observations: int,
) -> None:
    missing.append({
        "calculation_date": fmt_date(calculation_date),
        "universe_version": universe_version,
        "symbol": symbol,
        "name": name,
        "exposure_name": exposure_name,
        "lookback_window": int(lookback_window),
        "missing_data_flag": True,
        "missing_data_reason": reason,
        "available_observations": int(available_observations),
        "required_observations": int(required_observations),
        "point_in_time_status": "INSUFFICIENT_HISTORY" if reason == "INSUFFICIENT_HISTORY" else "NOT_COMPUTED",
        "confidence_level": "LOW",
        "research_only": True,
        "execution_allowed": False,
    })


def coverage_row(symbol: str, row: pd.Series, df: pd.DataFrame, calculation_date: pd.Timestamp) -> dict[str, Any]:
    latest = pd.Timestamp(df["date"].max()) if not df.empty else pd.NaT
    return {
        "universe_version": row.get("universe_version", ""),
        "symbol": symbol,
        "name": row.get("name", symbol),
        "qualification_verdict": row.get("qualification_verdict", ""),
        "price_rows": int(len(df)),
        "data_start": fmt_date(df["date"].min()) if not df.empty else "",
        "data_end": fmt_date(latest) if not df.empty else "",
        "calculation_date": fmt_date(calculation_date),
        "is_current_for_calculation_date": bool(latest == calculation_date),
        "research_only": True,
        "execution_allowed": False,
    }


def build_wide(values_df: pd.DataFrame) -> pd.DataFrame:
    if values_df.empty:
        return pd.DataFrame()
    df = values_df.copy()
    df["column"] = df["exposure_name"] + "__" + df["metric_name"] + "__" + df["lookback_window"].astype(str) + "d"
    wide = df.pivot_table(
        index=["calculation_date", "universe_version", "symbol", "name"],
        columns="column",
        values="exposure_value",
        aggfunc="last",
    ).reset_index()
    wide.columns.name = None
    return wide


def build_manifest(universe: str, universe_df: pd.DataFrame, values_df: pd.DataFrame, missing_df: pd.DataFrame, coverage_df: pd.DataFrame, calculation_date: pd.Timestamp) -> dict[str, Any]:
    exposure_counts = values_df.groupby("exposure_name").size().to_dict() if not values_df.empty else {}
    confidence_counts = values_df.groupby("confidence_level").size().to_dict() if not values_df.empty else {}
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S CST"),
        "phase": "Exposure Framework Phase C - Narrow Prototype Development",
        "universe_version": universe,
        "calculation_date": fmt_date(calculation_date),
        "approved_exposures": APPROVED_EXPOSURES,
        "exposure_count": len(APPROVED_EXPOSURES),
        "etf_count": int(len(universe_df)),
        "value_rows": int(len(values_df)),
        "missing_rows": int(len(missing_df)),
        "coverage_rows": int(len(coverage_df)),
        "exposure_value_counts": {k: int(v) for k, v in exposure_counts.items()},
        "confidence_counts": {k: int(v) for k, v in confidence_counts.items()},
        "all_outputs_research_only": True,
        "execution_allowed": False,
        "preview_research_status": "NOT_STARTED",
        "formal_execution_status": "BLOCKED",
        "single_source_of_truth": True,
        "etf_daily_copied": False,
        "pit_safety_summary": [
            "All rolling windows end at calculation_date.",
            "No forward returns are read or generated.",
            "Benchmark beta uses only ETF and benchmark returns <= calculation_date.",
            "Missing data produces explicit missing rows and confidence flags.",
        ],
        "output_files": {
            "values_csv": str(OUTPUT_VALUES_CSV),
            "wide_csv": str(OUTPUT_WIDE_CSV),
            "missing_csv": str(OUTPUT_MISSING_CSV),
            "coverage_csv": str(OUTPUT_COVERAGE_CSV),
            "manifest_json": str(OUTPUT_MANIFEST_JSON),
        },
    }


def normalize_symbol(value: Any) -> str:
    return str(value).split(".")[-1].strip().zfill(6)


def fmt_date(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def round_float(value: float | None) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 10)
