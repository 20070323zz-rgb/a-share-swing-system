"""ETF risk profile layer.

Research-only module. It builds a data-driven ETF risk/style profile from
local daily bars and local metadata. It does not modify rankings, paper trades,
paper positions, strategy rules, or execution code.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config import DATA_DIR, ETF_DAILY_DIR, PAPER_POSITIONS_FILE, PROJECT_ROOT, REPORT_DIR, WATCHLIST_FILE
from data_loader import read_formal_data_universe
from etf_style_profile import classify_style_profile, load_style_overrides, structural_profile_from_score, structural_risk_components


CANDIDATES_FILE = DATA_DIR / "etf_pool_expansion_candidates.csv"
CLASSIFICATION_FILE = DATA_DIR / "etf_classification.csv"
JQDATA_CANDIDATES_FILE = DATA_DIR / "staging" / "etf_candidates" / "jqdata_etf_candidates.csv"
RESOLVED_CANDIDATES_FILE = DATA_DIR / "staging" / "etf_candidates" / "resolved_etf_expansion_candidates.csv"
BENCHMARK_CODE = "510300"

PROFILE_CSV = REPORT_DIR / "etf_risk_profile.csv"
PROFILE_JSON = REPORT_DIR / "etf_risk_profile.json"
PROFILE_MD = REPORT_DIR / "etf_risk_profile.md"
STYLE_UNKNOWN_CSV = REPORT_DIR / "etf_style_unknown_audit.csv"
STYLE_UNKNOWN_MD = REPORT_DIR / "etf_style_unknown_audit.md"
STRUCTURAL_ANALYSIS_CSV = REPORT_DIR / "structural_vs_realized_risk_analysis.csv"
STRUCTURAL_ANALYSIS_JSON = REPORT_DIR / "structural_vs_realized_risk_analysis.json"
STRUCTURAL_ANALYSIS_MD = REPORT_DIR / "structural_vs_realized_risk_analysis.md"
SOURCE_AUDIT_MD = REPORT_DIR / "etf_risk_profile_source_audit.md"
SOURCE_AUDIT_JSON = REPORT_DIR / "etf_risk_profile_source_audit.json"
BUY_ANALYSIS_MD = REPORT_DIR / "buy_ranking_risk_profile_analysis.md"
BUY_ANALYSIS_JSON = REPORT_DIR / "buy_ranking_risk_profile_analysis.json"
CONSISTENCY_MD = REPORT_DIR / "etf_risk_profile_consistency_audit.md"
CONSISTENCY_JSON = REPORT_DIR / "etf_risk_profile_consistency_audit.json"
PHASE_MD = REPORT_DIR / "regime_risk_phase1_etf_profile.md"
PHASE_JSON = REPORT_DIR / "regime_risk_phase1_etf_profile.json"
PHASE_1_5_MD = REPORT_DIR / "regime_risk_phase1_5_style_structural_profile.md"
PHASE_1_5_JSON = REPORT_DIR / "regime_risk_phase1_5_style_structural_profile.json"

RISK_WEIGHTS = {
    "volatility_60d": 0.25,
    "beta_60d": 0.20,
    "max_drawdown_120d_abs": 0.20,
    "downside_volatility_60d": 0.15,
    "down_capture_60d": 0.10,
    "concentration_style_penalty": 0.10,
}

BROAD_BASE_CODES = {"510300", "510500", "512100", "510050", "510180", "510210", "510230", "510760"}
QUASI_BROAD_CODES = {"159915", "588000", "588080", "159901", "159949", "159967", "588030", "588200"}
FOCUS_SYMBOLS = ["512800", "515000", "512880", "512010", "588000", "159915", "510300", "510500", "510180"]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    profile_payload = build_risk_profile()
    rows = profile_payload["rows"]
    df = pd.DataFrame(rows)
    df.to_csv(PROFILE_CSV, index=False)
    PROFILE_JSON.write_text(_json_dumps(profile_payload), encoding="utf-8")
    PROFILE_MD.write_text(render_profile_report(profile_payload), encoding="utf-8")

    unknown_audit = build_style_unknown_audit(df)
    unknown_audit["csv_path"] = str(STYLE_UNKNOWN_CSV.relative_to(PROJECT_ROOT))
    pd.DataFrame(unknown_audit.get("rows", [])).to_csv(STYLE_UNKNOWN_CSV, index=False)
    STYLE_UNKNOWN_MD.write_text(render_style_unknown_audit(unknown_audit), encoding="utf-8")

    structural_analysis = build_structural_vs_realized_analysis(df)
    pd.DataFrame(structural_analysis.get("rows", [])).to_csv(STRUCTURAL_ANALYSIS_CSV, index=False)
    STRUCTURAL_ANALYSIS_JSON.write_text(_json_dumps(structural_analysis), encoding="utf-8")
    STRUCTURAL_ANALYSIS_MD.write_text(render_structural_analysis(structural_analysis), encoding="utf-8")

    source_audit = build_source_audit(df)
    SOURCE_AUDIT_JSON.write_text(_json_dumps(source_audit), encoding="utf-8")
    SOURCE_AUDIT_MD.write_text(render_source_audit(source_audit), encoding="utf-8")

    buy_analysis = build_buy_ranking_analysis(df)
    BUY_ANALYSIS_JSON.write_text(_json_dumps(buy_analysis), encoding="utf-8")
    BUY_ANALYSIS_MD.write_text(render_buy_analysis(buy_analysis), encoding="utf-8")

    consistency = build_consistency_audit(df)
    CONSISTENCY_JSON.write_text(_json_dumps(consistency), encoding="utf-8")
    CONSISTENCY_MD.write_text(render_consistency_audit(consistency), encoding="utf-8")

    phase_payload = build_phase_report_payload(profile_payload, source_audit, buy_analysis, consistency)
    PHASE_JSON.write_text(_json_dumps(phase_payload), encoding="utf-8")
    PHASE_MD.write_text(render_phase_report(phase_payload), encoding="utf-8")

    phase_1_5_payload = build_phase_1_5_payload(profile_payload, unknown_audit, structural_analysis, buy_analysis, consistency)
    PHASE_1_5_JSON.write_text(_json_dumps(phase_1_5_payload), encoding="utf-8")
    PHASE_1_5_MD.write_text(render_phase_1_5_report(phase_1_5_payload), encoding="utf-8")

    print(f"ETF risk profile rows: {len(df)}")
    print(f"written: {PROFILE_MD}")
    print(f"written: {STYLE_UNKNOWN_MD}")
    print(f"written: {STRUCTURAL_ANALYSIS_MD}")
    print(f"written: {BUY_ANALYSIS_MD}")
    print(f"written: {CONSISTENCY_MD}")


def build_risk_profile() -> dict[str, Any]:
    universe = _load_universe()
    meta = _metadata_map(universe)
    _merge_candidate_metadata(meta)
    classification = _classification_map()
    for symbol, row in classification.items():
        meta.setdefault(symbol, {}).update({k: v for k, v in row.items() if v not in ("", None)})
    _merge_candidate_metadata(meta)
    style_overrides = load_style_overrides()

    price_map = _load_price_map()
    benchmark = price_map.get(BENCHMARK_CODE, pd.DataFrame())
    benchmark_warning = _benchmark_warning(benchmark)
    benchmark_returns = _daily_returns(benchmark)

    rows: list[dict[str, Any]] = []
    for symbol, prices in sorted(price_map.items()):
        symbol_meta = meta.get(symbol, {})
        row = _profile_row(symbol, prices, symbol_meta, benchmark_returns, style_overrides.get(symbol, {}))
        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = _score_profiles(df)
        rows = df.to_dict(orient="records")

    positions = _portfolio_risk(rows)
    buy_analysis = _buy_top_profile(rows)
    summary = _profile_summary(rows, benchmark_warning, positions, buy_analysis)
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "benchmark_code": BENCHMARK_CODE,
        "benchmark_warning": benchmark_warning,
        "risk_score_method": {
            "range": "0-100",
            "meaning": "compatibility alias for realized_risk_score; higher means recent realized risk is higher",
            "normalization": "cross-sectional percentile rank over available ETF metrics",
            "weights": RISK_WEIGHTS,
            "missing_feature_policy": "missing metrics are not filled with zero; available weights are re-normalized per ETF",
            "execution_connected": False,
            "compatibility_alias": "risk_score = realized_risk_score; risk_profile = realized_risk_profile",
        },
        "structural_risk_method": {
            "range": "0-100",
            "meaning": "higher means structural offensive/high-risk character is stronger",
            "weights": {
                "asset_class_and_concentration": 0.30,
                "style_attribute": 0.25,
                "long_cycle_risk_features": 0.35,
                "diversification_concentration_adjustment": 0.10,
            },
            "profile_thresholds": "0-25 DEFENSIVE, 25-45 CORE, 45-60 BALANCED, 60-80 OFFENSIVE, 80-100 HIGH_BETA, with asset-type constraints",
            "execution_connected": False,
        },
        "summary": summary,
        "portfolio_risk_profile": positions,
        "buy_ranking_risk_profile": buy_analysis,
        "risk_profile_distribution": _value_counts(rows, "risk_profile"),
        "realized_risk_profile_distribution": _value_counts(rows, "realized_risk_profile"),
        "structural_risk_profile_distribution": _value_counts(rows, "structural_risk_profile"),
        "style_profile_distribution": _value_counts(rows, "style_profile"),
        "rows": rows,
        "research_only": True,
        "execution_allowed": False,
        "safety": _safety_payload(),
    }


def _load_universe() -> pd.DataFrame:
    try:
        return read_formal_data_universe(WATCHLIST_FILE, ETF_DAILY_DIR, CANDIDATES_FILE)
    except Exception:
        return pd.DataFrame()


def _load_price_map() -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    for path in sorted(ETF_DAILY_DIR.glob("*.csv")):
        symbol = _symbol_from_path(path)
        if not symbol:
            continue
        df = _read_price_file(path)
        if not df.empty:
            result[symbol] = df
    return result


def _read_price_file(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, dtype={"date": str}, keep_default_na=False)
    except Exception:
        return pd.DataFrame()
    rename = {"money": "amount"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns and v not in df.columns})
    if "date" not in df.columns or "close" not in df.columns:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["open", "high", "low", "close", "volume", "amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "close"]).drop_duplicates("date", keep="last").sort_values("date")
    return df.reset_index(drop=True)


def _metadata_map(universe: pd.DataFrame) -> dict[str, dict[str, Any]]:
    meta: dict[str, dict[str, Any]] = {}
    if not universe.empty:
        for _, row in universe.iterrows():
            symbol = _clean_symbol(row.get("code"))
            if not symbol:
                continue
            meta[symbol] = {
                "name": row.get("name") or symbol,
                "group": row.get("group") or "",
                "type": row.get("type") or "ETF",
                "pool": row.get("role") or row.get("pool") or "",
                "source": row.get("source") or "",
            }
    return meta


def _merge_candidate_metadata(meta: dict[str, dict[str, Any]]) -> None:
    """Fill missing ETF names/groups from local candidate lists.

    This is metadata-only and does not affect price data or execution rules.
    """
    candidate_sources = []
    if JQDATA_CANDIDATES_FILE.exists():
        candidate_sources.append((JQDATA_CANDIDATES_FILE, "code", "display_name", "", "jqdata_candidate_display_name"))
    if RESOLVED_CANDIDATES_FILE.exists():
        candidate_sources.append((RESOLVED_CANDIDATES_FILE, "original_code", "original_name", "group", "resolved_expansion_candidate"))
        candidate_sources.append((RESOLVED_CANDIDATES_FILE, "resolved_jq_code", "resolved_display_name", "group", "resolved_jq_candidate"))
    if CANDIDATES_FILE.exists():
        candidate_sources.append((CANDIDATES_FILE, "code", "name", "group", "expansion_candidate"))

    for path, code_col, name_col, group_col, source_label in candidate_sources:
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")
        except Exception:
            continue
        if code_col not in df.columns or name_col not in df.columns:
            continue
        for _, row in df.iterrows():
            symbol = _clean_symbol(row.get(code_col))
            if not symbol:
                continue
            item = meta.setdefault(symbol, {})
            name = str(row.get(name_col) or "").strip()
            current_name = str(item.get("name") or "").strip()
            if name and (not current_name or current_name == symbol or current_name.isdigit()):
                item["name"] = name
                item["metadata_name_source"] = source_label
            group = str(row.get(group_col) or "").strip() if group_col else ""
            current_group = str(item.get("group") or "").strip()
            if group and (not current_group or current_group in {"unknown", "expanded_formal_data"}):
                item["group"] = group


def _classification_map() -> dict[str, dict[str, Any]]:
    if not CLASSIFICATION_FILE.exists():
        return {}
    try:
        df = pd.read_csv(CLASSIFICATION_FILE, dtype=str, keep_default_na=False).fillna("")
    except Exception:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for _, row in df.iterrows():
        symbol = _clean_symbol(row.get("symbol") or row.get("code"))
        if symbol:
            result[symbol] = row.to_dict()
    return result


def _profile_row(symbol: str, prices: pd.DataFrame, meta: dict[str, Any], benchmark_returns: pd.Series, style_override: dict[str, str] | None = None) -> dict[str, Any]:
    returns = _daily_returns(prices)
    name = str(meta.get("name") or symbol)
    group = str(meta.get("group") or "unknown")
    etf_type = str(meta.get("etf_type") or meta.get("type") or "ETF")
    text = f"{symbol} {name} {group} {etf_type}".lower()

    row: dict[str, Any] = {
        "symbol": symbol,
        "name": name,
        "group": group,
        "type": etf_type,
        "pool": meta.get("pool", ""),
        "data_start": _date_str(prices["date"].min()) if not prices.empty else "",
        "data_end": _date_str(prices["date"].max()) if not prices.empty else "",
        "row_count": int(len(prices)),
        "return_20d": _window_return(prices, 20),
        "return_60d": _window_return(prices, 60),
        "return_120d": _window_return(prices, 120),
        "volatility_20d": _annualized_volatility(returns, 20),
        "volatility_60d": _annualized_volatility(returns, 60),
        "volatility_120d": _annualized_volatility(returns, 120),
        "beta_60d": _beta(returns, benchmark_returns, 60),
        "beta_120d": _beta(returns, benchmark_returns, 120),
        "max_drawdown_60d": _max_drawdown(prices, 60),
        "max_drawdown_120d": _max_drawdown(prices, 120),
        "downside_volatility_60d": _downside_volatility(returns, 60),
        "up_capture_60d": _capture_ratio(returns, benchmark_returns, 60, up=True),
        "down_capture_60d": _capture_ratio(returns, benchmark_returns, 60, up=False),
    }
    flags = _style_flags(symbol, name, group, etf_type, text, row)
    row.update(flags)
    row["concentration_profile"] = _concentration_profile(flags)
    style_profile, style_overridden, style_reason = classify_style_profile(symbol, name, group, etf_type, flags, style_override)
    row["style_profile"] = style_profile
    row["style_classification_override"] = bool(style_overridden)
    row["style_classification_reason"] = style_reason
    row["data_quality"] = _data_quality(row)
    row["risk_reasons"] = _risk_reasons_pre_score(row)
    row["missing_feature_count"] = 0
    row["risk_score"] = None
    row["risk_profile"] = "INSUFFICIENT_DATA"
    row["realized_risk_score"] = None
    row["realized_risk_profile"] = "INSUFFICIENT_DATA"
    row["realized_risk_percentile"] = None
    row["structural_risk_score"] = None
    row["structural_risk_profile"] = "INSUFFICIENT_DATA"
    row["structural_risk_percentile"] = None
    row["structural_risk_reason"] = ""
    row["classification_override"] = False
    row["override_reason"] = ""
    row["structural_classification_override"] = False
    row["structural_override_reason"] = ""
    row["research_only"] = True
    row["execution_allowed"] = False
    return row


def _score_profiles(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["max_drawdown_120d_abs"] = pd.to_numeric(out.get("max_drawdown_120d"), errors="coerce").abs()
    out["concentration_style_penalty"] = out.apply(_concentration_style_penalty, axis=1)
    for metric in RISK_WEIGHTS:
        values = pd.to_numeric(out[metric], errors="coerce")
        out[f"{metric}_pct_rank"] = values.rank(pct=True, na_option="keep")

    scores = []
    missing_counts = []
    for _, row in out.iterrows():
        available_score = 0.0
        available_weight = 0.0
        missing = 0
        for metric, weight in RISK_WEIGHTS.items():
            value = row.get(f"{metric}_pct_rank")
            if pd.isna(value):
                missing += 1
                continue
            available_score += float(value) * weight
            available_weight += weight
        if available_weight <= 0:
            scores.append(np.nan)
        else:
            scores.append(round(available_score / available_weight * 100.0, 4))
        missing_counts.append(missing)
    out["risk_score"] = scores
    out["realized_risk_score"] = scores
    out["missing_feature_count"] = missing_counts

    valid_scores = pd.to_numeric(out["risk_score"], errors="coerce")
    score_pct = valid_scores.rank(pct=True, na_option="keep")
    profile_results = [
        _risk_profile_from_pct(score, pct, row)
        for score, pct, (_, row) in zip(valid_scores.tolist(), score_pct.tolist(), out.iterrows())
    ]
    out["risk_profile"] = [item[0] for item in profile_results]
    out["realized_risk_profile"] = out["risk_profile"]
    out["realized_risk_percentile"] = [None if pd.isna(value) else round(float(value) * 100.0, 4) for value in score_pct.tolist()]
    out["classification_override"] = [item[1] for item in profile_results]
    out["override_reason"] = [item[2] for item in profile_results]
    out["is_high_beta"] = out.apply(lambda row: bool(row.get("is_high_beta")) or row.get("risk_profile") == "HIGH_BETA", axis=1)
    structural_rows = []
    for _, row in out.iterrows():
        if row.get("data_quality") == "insufficient":
            structural_rows.append({
                "structural_risk_score": np.nan,
                "structural_risk_profile": "INSUFFICIENT_DATA",
                "structural_risk_reason": "data_quality=insufficient",
                "structural_classification_override": False,
                "structural_override_reason": "",
            })
            continue
        components = structural_risk_components(row.to_dict())
        profile, overridden, reason = structural_profile_from_score(float(components["structural_risk_score"]), row.to_dict(), load_style_overrides().get(str(row.get("symbol")), {}))
        structural_rows.append({
            **components,
            "structural_risk_profile": profile,
            "structural_classification_override": overridden,
            "structural_override_reason": reason,
        })
    structural_df = pd.DataFrame(structural_rows)
    for col in structural_df.columns:
        out[col] = structural_df[col].values
    structural_scores = pd.to_numeric(out["structural_risk_score"], errors="coerce")
    structural_pct = structural_scores.rank(pct=True, na_option="keep")
    out["structural_risk_percentile"] = [None if pd.isna(value) else round(float(value) * 100.0, 4) for value in structural_pct.tolist()]
    out["risk_reasons"] = out.apply(_risk_reasons_after_score, axis=1)
    for col in ["max_drawdown_120d_abs", "concentration_style_penalty", *[f"{m}_pct_rank" for m in RISK_WEIGHTS]]:
        if col not in _output_columns():
            out = out.drop(columns=[col], errors="ignore")
    return out[_output_columns()]


def _risk_profile_from_pct(score: float, pct: float, row: pd.Series) -> tuple[str, bool, str]:
    if pd.isna(score) or row.get("data_quality") == "insufficient":
        return "INSUFFICIENT_DATA", False, ""
    if _bool(row.get("is_bond")):
        if pd.notna(pct) and pct > 0.40:
            return "CORE", True, "bond_cash structure override to DEFENSIVE/CORE"
        return ("DEFENSIVE" if pd.isna(pct) or pct <= 0.30 else "CORE"), False, ""
    if pct <= 0.20:
        return "DEFENSIVE", False, ""
    if pct <= 0.40:
        return "CORE", False, ""
    if pct <= 0.60:
        return "BALANCED", False, ""
    if pct <= 0.80:
        return "OFFENSIVE", False, ""
    return "HIGH_BETA", False, ""


def _output_columns() -> list[str]:
    return [
        "symbol", "name", "group", "type", "pool", "data_start", "data_end", "row_count",
        "return_20d", "return_60d", "return_120d",
        "volatility_20d", "volatility_60d", "volatility_120d",
        "beta_60d", "beta_120d",
        "max_drawdown_60d", "max_drawdown_120d",
        "downside_volatility_60d", "up_capture_60d", "down_capture_60d",
        "is_broad_base", "is_quasi_broad_base", "is_sector", "is_theme", "is_bond",
        "is_dividend", "is_low_vol", "is_growth", "is_high_beta",
        "concentration_profile", "style_profile",
        "realized_risk_score", "realized_risk_profile", "realized_risk_percentile",
        "structural_risk_score", "structural_risk_profile", "structural_risk_percentile",
        "risk_score", "risk_profile",
        "risk_reasons", "data_quality", "missing_feature_count",
        "style_classification_override", "style_classification_reason",
        "classification_override", "override_reason",
        "structural_classification_override", "structural_override_reason", "structural_risk_reason",
        "asset_class_score", "style_attribute_score", "long_cycle_risk_score", "concentration_adjustment_score",
        "research_only", "execution_allowed",
    ]


def _style_flags(symbol: str, name: str, group: str, etf_type: str, text: str, metrics: dict[str, Any]) -> dict[str, bool]:
    cn_text = f"{symbol} {name} {group} {etf_type}"
    is_broad = symbol in BROAD_BASE_CODES or _has(cn_text, ["沪深300", "中证500", "中证1000", "上证50", "上证180", "中证A500", "A500", "A50", "宽基"])
    is_quasi = symbol in QUASI_BROAD_CODES or _has(cn_text, ["创业板", "科创50", "科创100", "科创200", "中证2000", "北证50", "深100"])
    is_bond = etf_type == "bond_cash" or symbol.startswith("511") or _has(cn_text, ["债", "货币", "现金", "短融"])
    is_qdii = etf_type == "qdii" or _has(cn_text, ["QDII", "港股", "恒生", "中概", "纳指", "标普", "日经", "德国", "印度"])
    is_theme = etf_type == "theme" or _has(cn_text, ["机器人", "低空", "商业航天", "AI", "人工智能", "算力", "芯片", "半导体", "创新药", "新能源", "光伏", "电池", "游戏", "传媒"])
    is_sector = etf_type in {"sector", "commodity_resource", "high_beta"} or _has(cn_text, ["银行", "证券", "券商", "医药", "医疗", "消费", "煤炭", "有色", "军工", "电力", "公用事业", "红利"])
    is_dividend = _has(cn_text, ["红利", "高股息", "央企", "分红", "现金流"])
    is_low_vol = is_bond or _has(cn_text, ["低波", "质量", "稳健"])
    is_growth = is_quasi or _has(cn_text, ["科技", "成长", "创业板", "科创", "芯片", "半导体", "AI", "人工智能", "新能源", "创新药"])
    beta = _float(metrics.get("beta_60d"), fallback=np.nan)
    vol = _float(metrics.get("volatility_60d"), fallback=np.nan)
    is_high_beta = etf_type == "high_beta" or _has(cn_text, ["证券", "券商", "非银"]) or (pd.notna(beta) and beta >= 1.20) or (pd.notna(vol) and vol >= 0.35)
    return {
        "is_broad_base": bool(is_broad and not is_qdii),
        "is_quasi_broad_base": bool(is_quasi and not is_broad and not is_qdii),
        "is_sector": bool(is_sector and not is_broad and not is_quasi and not is_bond and not is_qdii),
        "is_theme": bool(is_theme and not is_bond and not is_qdii),
        "is_bond": bool(is_bond),
        "is_dividend": bool(is_dividend),
        "is_low_vol": bool(is_low_vol),
        "is_growth": bool(is_growth),
        "is_high_beta": bool(is_high_beta),
        "is_qdii": bool(is_qdii),
    }


def _concentration_profile(flags: dict[str, bool]) -> str:
    if flags.get("is_bond"):
        return "bond_cash"
    if flags.get("is_broad_base"):
        return "broad_base"
    if flags.get("is_quasi_broad_base"):
        return "quasi_broad_base"
    if flags.get("is_theme"):
        return "theme_concentrated"
    if flags.get("is_sector"):
        return "sector_concentrated"
    if flags.get("is_qdii"):
        return "qdii_observation"
    return "unknown"


def _style_profile(symbol: str, name: str, group: str, etf_type: str, flags: dict[str, bool]) -> str:
    text = f"{symbol} {name} {group} {etf_type}"
    if flags.get("is_bond"):
        return "BOND"
    if flags.get("is_qdii"):
        return "QDII_OBSERVATION"
    if flags.get("is_dividend"):
        return "DIVIDEND"
    if flags.get("is_low_vol") and not flags.get("is_growth"):
        return "LOW_VOL"
    if flags.get("is_high_beta") and flags.get("is_theme"):
        return "HIGH_BETA_THEME"
    if flags.get("is_broad_base") and _has(text, ["沪深300", "上证50", "上证180", "A50"]):
        return "CORE_LARGE_CAP"
    if flags.get("is_broad_base"):
        return "CORE_MID_CAP"
    if flags.get("is_quasi_broad_base") and flags.get("is_growth"):
        return "GROWTH_BROAD"
    if flags.get("is_theme") and flags.get("is_growth"):
        return "GROWTH_THEME"
    if _has(text, ["煤炭", "有色", "黄金", "钢铁", "能源", "油气", "化工", "资源"]):
        return "COMMODITY_CYCLICAL"
    if _has(text, ["医药", "医疗", "消费", "食品", "家电", "电力", "公用事业"]):
        return "SECTOR_DEFENSIVE"
    if flags.get("is_sector"):
        return "SECTOR_CYCLICAL"
    return "UNKNOWN"


def _concentration_style_penalty(row: pd.Series) -> float:
    score = 0.0
    if _bool(row.get("is_bond")):
        score += 0.05
    if _bool(row.get("is_broad_base")):
        score += 0.20
    if _bool(row.get("is_quasi_broad_base")):
        score += 0.38
    if _bool(row.get("is_sector")):
        score += 0.58
    if _bool(row.get("is_theme")):
        score += 0.78
    if _bool(row.get("is_high_beta")):
        score += 0.20
    if _bool(row.get("is_growth")):
        score += 0.08
    if str(row.get("style_profile")) == "UNKNOWN":
        score += 0.10
    return min(score, 1.0)


def _data_quality(row: dict[str, Any]) -> str:
    row_count = int(row.get("row_count") or 0)
    missing_core = sum(pd.isna(row.get(key)) for key in ["volatility_60d", "beta_60d", "max_drawdown_120d", "downside_volatility_60d"])
    if row_count < 60:
        return "insufficient"
    if row_count < 120:
        return "short_history"
    if missing_core >= 2:
        return "partial"
    return "ok"


def _risk_reasons_pre_score(row: dict[str, Any]) -> str:
    reasons = []
    if row.get("is_high_beta"):
        reasons.append("high_beta flag from type/name/beta/volatility")
    if row.get("is_theme"):
        reasons.append("theme concentration")
    if row.get("is_bond"):
        reasons.append("bond/cash low-vol structure")
    if row.get("data_quality") != "ok":
        reasons.append(f"data_quality={row.get('data_quality')}")
    return "; ".join(reasons) or "data-driven profile pending score"


def _risk_reasons_after_score(row: pd.Series) -> str:
    reasons = []
    score = _float(row.get("risk_score"), fallback=np.nan)
    if pd.notna(score):
        reasons.append(f"risk_score={score:.2f}")
    for key, label in [
        ("volatility_60d", "60d volatility"),
        ("beta_60d", "60d beta"),
        ("max_drawdown_120d", "120d max drawdown"),
        ("downside_volatility_60d", "60d downside vol"),
        ("down_capture_60d", "60d down capture"),
    ]:
        value = _float(row.get(key), fallback=np.nan)
        if pd.notna(value):
            reasons.append(f"{label}={value:.4f}")
    if _bool(row.get("is_high_beta")):
        reasons.append("high_beta flag")
    if _bool(row.get("is_bond")):
        reasons.append("bond/cash structural low-risk constraint")
    if row.get("data_quality") != "ok":
        reasons.append(f"data_quality={row.get('data_quality')}")
    return "; ".join(reasons)


def _profile_summary(rows: list[dict[str, Any]], benchmark_warning: str, portfolio: dict[str, Any], buy: dict[str, Any]) -> dict[str, Any]:
    valid = [row for row in rows if row.get("risk_profile") != "INSUFFICIENT_DATA"]
    insufficient = [row for row in rows if row.get("risk_profile") == "INSUFFICIENT_DATA" or row.get("data_quality") in {"insufficient", "short_history"}]
    unknown_style = [row for row in rows if row.get("style_profile") == "UNKNOWN"]
    return {
        "total_etf": len(rows),
        "valid_profile_count": len(valid),
        "insufficient_data_count": len(insufficient),
        "unknown_style_count": len(unknown_style),
        "benchmark_warning": benchmark_warning,
        "risk_profile_distribution": _value_counts(rows, "risk_profile"),
        "realized_risk_profile_distribution": _value_counts(rows, "realized_risk_profile"),
        "structural_risk_profile_distribution": _value_counts(rows, "structural_risk_profile"),
        "style_profile_distribution": _value_counts(rows, "style_profile"),
        "risk_score_top10": _top_rows(rows, descending=True, limit=10),
        "risk_score_bottom10": _top_rows(rows, descending=False, limit=10),
        "focus_symbols": {symbol: _row_by_symbol(rows, symbol) for symbol in FOCUS_SYMBOLS},
        "portfolio_weighted_risk_score": portfolio.get("weighted_risk_score"),
        "portfolio_weighted_realized_risk_score": portfolio.get("weighted_realized_risk_score"),
        "portfolio_weighted_structural_risk_score": portfolio.get("weighted_structural_risk_score"),
        "buy_top10_avg_risk_score": buy.get("top10_avg_risk_score"),
        "buy_top10_avg_realized_risk_score": buy.get("top10_avg_realized_risk_score"),
        "buy_top10_avg_structural_risk_score": buy.get("top10_avg_structural_risk_score"),
        "research_only": True,
        "execution_allowed": False,
    }


def _portfolio_risk(rows: list[dict[str, Any]]) -> dict[str, Any]:
    positions = _read_csv(PAPER_POSITIONS_FILE)
    by_symbol = {str(row.get("symbol")): row for row in rows}
    position_rows = []
    if positions.empty:
        return {
            "position_count": 0,
            "avg_risk_score": None,
            "weighted_risk_score": None,
            "avg_realized_risk_score": None,
            "weighted_realized_risk_score": None,
            "avg_structural_risk_score": None,
            "weighted_structural_risk_score": None,
            "risk_profile_distribution": {},
            "structural_risk_profile_distribution": {},
            "style_profile_distribution": {},
            "offensive_high_beta_weight": 0.0,
            "structural_offensive_high_beta_weight": 0.0,
            "core_defensive_weight": 0.0,
            "missing_core_defensive": True,
            "rows": [],
            "research_only": True,
            "execution_allowed": False,
        }
    total_mv = pd.to_numeric(positions.get("market_value"), errors="coerce").fillna(0).sum()
    realized_scores = []
    structural_scores = []
    weighted_realized = 0.0
    weighted_structural = 0.0
    for _, pos in positions.iterrows():
        symbol = _clean_symbol(pos.get("symbol") or pos.get("code"))
        profile = by_symbol.get(symbol, {})
        market_value = _float(pos.get("market_value"), fallback=0.0)
        weight = market_value / total_mv if total_mv else 0.0
        score = _float(profile.get("risk_score"), fallback=np.nan)
        realized_score = _float(profile.get("realized_risk_score"), fallback=score)
        structural_score = _float(profile.get("structural_risk_score"), fallback=np.nan)
        if pd.notna(realized_score):
            realized_scores.append(realized_score)
            weighted_realized += realized_score * weight
        if pd.notna(structural_score):
            structural_scores.append(structural_score)
            weighted_structural += structural_score * weight
        position_rows.append({
            "symbol": symbol,
            "name": pos.get("name") or profile.get("name") or symbol,
            "current_weight": weight,
            "market_value": market_value,
            "risk_score": None if pd.isna(score) else round(float(score), 4),
            "risk_profile": profile.get("risk_profile", "UNKNOWN"),
            "realized_risk_score": None if pd.isna(realized_score) else round(float(realized_score), 4),
            "realized_risk_profile": profile.get("realized_risk_profile", profile.get("risk_profile", "UNKNOWN")),
            "structural_risk_score": None if pd.isna(structural_score) else round(float(structural_score), 4),
            "structural_risk_profile": profile.get("structural_risk_profile", "UNKNOWN"),
            "style_profile": profile.get("style_profile", "UNKNOWN"),
            "volatility_60d": profile.get("volatility_60d"),
            "beta_60d": profile.get("beta_60d"),
            "max_drawdown_120d": profile.get("max_drawdown_120d"),
            "down_capture_60d": profile.get("down_capture_60d"),
            "execution_allowed": False,
        })
    risk_dist = _weighted_counts(position_rows, "risk_profile", "current_weight")
    structural_dist = _weighted_counts(position_rows, "structural_risk_profile", "current_weight")
    style_dist = _weighted_counts(position_rows, "style_profile", "current_weight")
    offensive_weight = sum(row.get("current_weight", 0.0) for row in position_rows if row.get("realized_risk_profile") in {"OFFENSIVE", "HIGH_BETA"})
    structural_offensive_weight = sum(row.get("current_weight", 0.0) for row in position_rows if row.get("structural_risk_profile") in {"OFFENSIVE", "HIGH_BETA"})
    core_def_weight = sum(row.get("current_weight", 0.0) for row in position_rows if row.get("structural_risk_profile") in {"DEFENSIVE", "CORE"})
    return {
        "position_count": len(position_rows),
        "avg_risk_score": round(float(np.mean(realized_scores)), 4) if realized_scores else None,
        "weighted_risk_score": round(float(weighted_realized), 4) if realized_scores else None,
        "avg_realized_risk_score": round(float(np.mean(realized_scores)), 4) if realized_scores else None,
        "weighted_realized_risk_score": round(float(weighted_realized), 4) if realized_scores else None,
        "avg_structural_risk_score": round(float(np.mean(structural_scores)), 4) if structural_scores else None,
        "weighted_structural_risk_score": round(float(weighted_structural), 4) if structural_scores else None,
        "risk_profile_distribution": risk_dist,
        "structural_risk_profile_distribution": structural_dist,
        "style_profile_distribution": style_dist,
        "offensive_high_beta_weight": offensive_weight,
        "structural_offensive_high_beta_weight": structural_offensive_weight,
        "core_defensive_weight": core_def_weight,
        "missing_core_defensive": core_def_weight <= 0.05,
        "is_offensive_tilt": offensive_weight >= 0.50,
        "rows": position_rows,
        "research_only": True,
        "execution_allowed": False,
    }


def _buy_top_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ranking = _read_buy_ranking()
    by_symbol = {str(row.get("symbol")): row for row in rows}
    enriched = []
    for item in ranking[:10]:
        symbol = str(item.get("symbol") or item.get("code") or "")
        profile = by_symbol.get(symbol, {})
        merged = {**item, **{
            "risk_score_profile": profile.get("risk_score"),
            "risk_profile": profile.get("risk_profile"),
            "realized_risk_score": profile.get("realized_risk_score", profile.get("risk_score")),
            "realized_risk_profile": profile.get("realized_risk_profile", profile.get("risk_profile")),
            "structural_risk_score": profile.get("structural_risk_score"),
            "structural_risk_profile": profile.get("structural_risk_profile"),
            "style_profile": profile.get("style_profile"),
            "volatility_60d": profile.get("volatility_60d"),
            "beta_60d": profile.get("beta_60d"),
            "data_quality": profile.get("data_quality"),
            "execution_allowed": False,
        }}
        enriched.append(merged)
    scores = [_float(row.get("risk_score_profile"), fallback=np.nan) for row in enriched]
    scores = [score for score in scores if pd.notna(score)]
    realized_scores = [_float(row.get("realized_risk_score"), fallback=np.nan) for row in enriched]
    realized_scores = [score for score in realized_scores if pd.notna(score)]
    structural_scores = [_float(row.get("structural_risk_score"), fallback=np.nan) for row in enriched]
    structural_scores = [score for score in structural_scores if pd.notna(score)]
    risk_dist = _value_counts(enriched, "risk_profile")
    structural_dist = _value_counts(enriched, "structural_risk_profile")
    style_dist = _value_counts(enriched, "style_profile")
    offensive = sum(1 for row in enriched if row.get("realized_risk_profile") in {"OFFENSIVE", "HIGH_BETA"})
    structural_offensive = sum(1 for row in enriched if row.get("structural_risk_profile") in {"OFFENSIVE", "HIGH_BETA"})
    core = sum(1 for row in enriched if row.get("risk_profile") in {"DEFENSIVE", "CORE"})
    return {
        "top10_count": len(enriched),
        "top10_avg_risk_score": round(float(np.mean(scores)), 4) if scores else None,
        "top10_avg_realized_risk_score": round(float(np.mean(realized_scores)), 4) if realized_scores else None,
        "top10_avg_structural_risk_score": round(float(np.mean(structural_scores)), 4) if structural_scores else None,
        "risk_profile_distribution": risk_dist,
        "realized_risk_profile_distribution": risk_dist,
        "structural_risk_profile_distribution": structural_dist,
        "style_profile_distribution": style_dist,
        "offensive_high_beta_count": offensive,
        "offensive_high_beta_ratio": offensive / len(enriched) if enriched else 0.0,
        "structural_offensive_high_beta_count": structural_offensive,
        "structural_offensive_high_beta_ratio": structural_offensive / len(enriched) if enriched else 0.0,
        "core_defensive_count": core,
        "core_defensive_ratio": core / len(enriched) if enriched else 0.0,
        "is_ranking_offensive_tilt": offensive / len(enriched) >= 0.50 if enriched else False,
        "rows": enriched,
        "research_only": True,
        "execution_allowed": False,
    }


def build_source_audit(profile_df: pd.DataFrame) -> dict[str, Any]:
    watchlist_path_expected = DATA_DIR / "watchlist.csv"
    watchlist_df = _read_csv(WATCHLIST_FILE)
    class_df = _read_csv(CLASSIFICATION_FILE)
    keyword_hits = _keyword_search()
    payload = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expected_data_watchlist_exists": watchlist_path_expected.exists(),
        "actual_watchlist_path": str(WATCHLIST_FILE.relative_to(PROJECT_ROOT)) if WATCHLIST_FILE.exists() else "",
        "watchlist_groups": sorted(watchlist_df.get("group", pd.Series(dtype=str)).astype(str).dropna().unique().tolist()) if not watchlist_df.empty and "group" in watchlist_df else [],
        "watchlist_types": sorted(watchlist_df.get("type", pd.Series(dtype=str)).astype(str).dropna().unique().tolist()) if not watchlist_df.empty and "type" in watchlist_df else [],
        "classification_etf_types": _value_counts(class_df.to_dict(orient="records"), "etf_type") if not class_df.empty else {},
        "classification_risk_profiles": _value_counts(class_df.to_dict(orient="records"), "risk_profile") if not class_df.empty else {},
        "unknown_classification_count": int((class_df.get("etf_type", pd.Series(dtype=str)).astype(str) == "unknown").sum()) if not class_df.empty and "etf_type" in class_df else 0,
        "high_beta_definition": "Existing high_beta watcher flags names/types containing high_beta, 证券, 券商. Risk Profile additionally uses beta_60d>=1.20 or annualized volatility_60d>=35%.",
        "broad_base_definition": "Existing broad_base preview uses curated traditional/quasi broad codes and broad-index names. Risk Profile splits is_broad_base and is_quasi_broad_base with code/name/group rules.",
        "manual_label_fields": ["watchlist.group", "watchlist.role", "classification.etf_type", "classification.risk_profile", "classification.classification_reason"],
        "historical_market_fields": ["return_20d/60d/120d", "volatility_20d/60d/120d", "beta_60d/120d", "max_drawdown_60d/120d", "downside_volatility_60d", "up_capture_60d", "down_capture_60d"],
        "usable_inputs": ["name", "group", "type", "etf_type", "pool", "local daily OHLCV/amount", "existing high_beta/broad_base/portfolio exposure reports"],
        "keyword_hits": keyword_hits,
        "profile_unknown_style_count": int((profile_df.get("style_profile", pd.Series(dtype=str)).astype(str) == "UNKNOWN").sum()) if not profile_df.empty else 0,
        "watchlist_modified": False,
        "research_only": True,
        "execution_allowed": False,
    }
    return payload


def build_buy_ranking_analysis(profile_df: pd.DataFrame) -> dict[str, Any]:
    rows = profile_df.to_dict(orient="records") if not profile_df.empty else []
    return _buy_top_profile(rows)


def build_style_unknown_audit(profile_df: pd.DataFrame) -> dict[str, Any]:
    rows = profile_df.to_dict(orient="records") if not profile_df.empty else []
    unknown = [row for row in rows if row.get("style_profile") == "UNKNOWN"]
    audit_rows = []
    for row in unknown:
        audit_rows.append({
            "symbol": row.get("symbol"),
            "name": row.get("name"),
            "group": row.get("group"),
            "type": row.get("type"),
            "pool": row.get("pool"),
            "data_quality": row.get("data_quality"),
            "classification_reason": row.get("style_classification_reason") or "metadata insufficient",
            "manual_override_candidate": "yes" if str(row.get("name", "")).isdigit() or str(row.get("type", "")) == "unknown" else "review",
        })
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_etf": len(rows),
        "unknown_count": len(audit_rows),
        "unknown_target": 15,
        "target_met": len(audit_rows) <= 15,
        "rows": audit_rows,
        "reason": "UNKNOWN is preserved when metadata/name/group/type cannot identify a reliable style. No guessing.",
        "research_only": True,
        "execution_allowed": False,
    }


PROFILE_ORDER = {"DEFENSIVE": 1, "CORE": 2, "BALANCED": 3, "OFFENSIVE": 4, "HIGH_BETA": 5}


def build_structural_vs_realized_analysis(profile_df: pd.DataFrame) -> dict[str, Any]:
    rows = profile_df.to_dict(orient="records") if not profile_df.empty else []
    analysis_rows = []
    for row in rows:
        structural_score = _float(row.get("structural_risk_score"), fallback=np.nan)
        realized_score = _float(row.get("realized_risk_score"), fallback=_float(row.get("risk_score"), fallback=np.nan))
        structural_profile = str(row.get("structural_risk_profile") or "")
        realized_profile = str(row.get("realized_risk_profile") or row.get("risk_profile") or "")
        score_gap = None if pd.isna(structural_score) or pd.isna(realized_score) else round(structural_score - realized_score, 4)
        profile_gap = PROFILE_ORDER.get(structural_profile, 0) - PROFILE_ORDER.get(realized_profile, 0)
        if score_gap is None:
            direction = "insufficient"
        elif score_gap >= 12 or profile_gap >= 2:
            direction = "structural_gt_realized"
        elif score_gap <= -12 or profile_gap <= -2:
            direction = "realized_gt_structural"
        else:
            direction = "aligned_or_mild_gap"
        analysis_rows.append({
            "symbol": row.get("symbol"),
            "name": row.get("name"),
            "style_profile": row.get("style_profile"),
            "structural_risk_score": None if pd.isna(structural_score) else round(float(structural_score), 4),
            "structural_risk_profile": structural_profile,
            "realized_risk_score": None if pd.isna(realized_score) else round(float(realized_score), 4),
            "realized_risk_profile": realized_profile,
            "score_gap": score_gap,
            "profile_gap": profile_gap,
            "gap_direction": direction,
            "gap_reason": _gap_reason(row, direction),
        })
    focus = {symbol: _row_by_symbol(analysis_rows, symbol) for symbol in FOCUS_SYMBOLS}
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "row_count": len(analysis_rows),
        "gap_distribution": _value_counts(analysis_rows, "gap_direction"),
        "focus_symbols": focus,
        "rows": analysis_rows,
        "research_only": True,
        "execution_allowed": False,
    }


def _gap_reason(row: dict[str, Any], direction: str) -> str:
    style = str(row.get("style_profile") or "")
    if direction == "structural_gt_realized":
        return f"{style} has higher long-term/structural risk character than recent realized market risk; not a trading signal."
    if direction == "realized_gt_structural":
        return f"Recent realized volatility/beta/drawdown is higher than the ETF's structural style baseline; needs observation, not automatic action."
    if direction == "insufficient":
        return "Insufficient metrics for reliable comparison."
    return "Structural and realized risk are broadly aligned or only mildly different."


def build_consistency_audit(profile_df: pd.DataFrame) -> dict[str, Any]:
    rows = profile_df.to_dict(orient="records") if not profile_df.empty else []
    by_symbol = {str(row.get("symbol")): row for row in rows}
    high_beta = _read_json(REPORT_DIR / "high_beta_risk_watch.json")
    broad = _read_json(REPORT_DIR / "broad_base_balance_preview.json")
    portfolio = _read_json(REPORT_DIR / "portfolio_exposure.json")

    hb_rows = high_beta.get("rows", []) if isinstance(high_beta, dict) else []
    hb_match = []
    hb_structural_conflict = []
    hb_realized_gap = []
    for row in hb_rows:
        symbol = str(row.get("symbol", ""))
        profile = by_symbol.get(symbol, {})
        merged = {
            "symbol": symbol,
            "name": row.get("name"),
            "realized_risk_profile": profile.get("realized_risk_profile", profile.get("risk_profile")),
            "realized_risk_score": profile.get("realized_risk_score", profile.get("risk_score")),
            "structural_risk_profile": profile.get("structural_risk_profile"),
            "structural_risk_score": profile.get("structural_risk_score"),
            "risk_profile": profile.get("risk_profile"),
            "risk_score": profile.get("risk_score"),
            "style_profile": profile.get("style_profile"),
        }
        hb_match.append(merged)
        if profile.get("structural_risk_profile") not in {"OFFENSIVE", "HIGH_BETA"}:
            hb_structural_conflict.append({**merged, "conflict_reason": "existing high_beta not structurally OFFENSIVE/HIGH_BETA"})
        if profile.get("realized_risk_profile") not in {"OFFENSIVE", "HIGH_BETA"}:
            hb_realized_gap.append({**merged, "gap_reason": "existing high_beta but recent realized risk is not OFFENSIVE/HIGH_BETA; this can be normal"})

    broad_rows = broad.get("rows", []) if isinstance(broad, dict) else []
    broad_conflict = []
    broad_summary = []
    for row in broad_rows:
        symbol = str(row.get("symbol", ""))
        profile = by_symbol.get(symbol, {})
        item = {
            "symbol": symbol,
            "name": row.get("name"),
            "type": row.get("type"),
            "realized_risk_profile": profile.get("realized_risk_profile", profile.get("risk_profile")),
            "structural_risk_profile": profile.get("structural_risk_profile"),
            "style_profile": profile.get("style_profile"),
            "risk_profile": profile.get("risk_profile"),
            "risk_score": profile.get("risk_score"),
            "structural_risk_score": profile.get("structural_risk_score"),
        }
        broad_summary.append(item)
        if row.get("is_broad_base") and profile.get("structural_risk_profile") == "HIGH_BETA":
            broad_conflict.append({**item, "conflict_reason": "traditional broad base is structurally HIGH_BETA"})

    bond_rows = [row for row in rows if row.get("is_bond")]
    bond_conflict = [row for row in bond_rows if row.get("structural_risk_profile") not in {"DEFENSIVE", "CORE"}]
    portfolio_rows = portfolio.get("positions", []) if isinstance(portfolio, dict) else []
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "high_beta_existing_count": len(hb_rows),
        "high_beta_structural_consistent_count": len(hb_rows) - len(hb_structural_conflict),
        "high_beta_realized_offensive_count": len(hb_rows) - len(hb_realized_gap),
        "high_beta_consistent_count": len(hb_rows) - len(hb_structural_conflict),
        "high_beta_structural_conflicts": hb_structural_conflict,
        "high_beta_realized_gaps": hb_realized_gap,
        "high_beta_conflicts": hb_structural_conflict,
        "broad_base_candidate_count": len(broad_rows),
        "broad_base_conflicts": broad_conflict,
        "bond_count": len(bond_rows),
        "bond_conflicts": [{"symbol": row.get("symbol"), "name": row.get("name"), "structural_risk_profile": row.get("structural_risk_profile"), "structural_risk_score": row.get("structural_risk_score")} for row in bond_conflict],
        "portfolio_position_count": len(portfolio_rows),
        "broad_base_summary": broad_summary[:20],
        "conflict_count": len(hb_structural_conflict) + len(broad_conflict) + len(bond_conflict),
        "realized_gap_count": len(hb_realized_gap),
        "conflict_interpretation": "Structural conflicts are potential taxonomy issues. Realized gaps are not automatically errors; they may reflect recent risk being lower/higher than stable asset character.",
        "research_only": True,
        "execution_allowed": False,
    }


def build_phase_report_payload(profile_payload: dict[str, Any], source_audit: dict[str, Any], buy_analysis: dict[str, Any], consistency: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "phase": "Regime & Risk Allocation Phase 1",
        "target": "ETF Risk Profile Layer",
        "risk_score_method": profile_payload.get("risk_score_method", {}),
        "summary": profile_payload.get("summary", {}),
        "portfolio_risk_profile": profile_payload.get("portfolio_risk_profile", {}),
        "buy_ranking_risk_profile": buy_analysis,
        "source_audit_summary": {
            "watchlist_groups": source_audit.get("watchlist_groups", []),
            "watchlist_types": source_audit.get("watchlist_types", []),
            "unknown_classification_count": source_audit.get("unknown_classification_count", 0),
        },
        "consistency_audit": {
            "conflict_count": consistency.get("conflict_count", 0),
            "high_beta_consistent_count": consistency.get("high_beta_consistent_count", 0),
            "broad_base_conflicts": consistency.get("broad_base_conflicts", []),
        },
        "ready_for_regime_fit": False,
        "ready_for_execution": False,
        "next_phase_requirements": [
            "accumulate risk profile stability history",
            "define regime-asset fit as preview-only",
            "backtest any regime fit before touching execution",
            "keep adjusted preview and shadow separated from paper_trade_engine",
        ],
        "research_only": True,
        "execution_allowed": False,
        "safety": _safety_payload(),
    }


def render_profile_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    portfolio = payload["portfolio_risk_profile"]
    buy = payload["buy_ranking_risk_profile"]
    rows = payload["rows"]
    lines = [
        "# ETF Risk Profile 风险画像报告",
        "",
        "本报告只建立 ETF 自身风险/风格画像，不修改 BUY ranking、不修改模拟仓、不接执行层。",
        "",
        "## 摘要",
        f"- ETF 总数：{summary['total_etf']}",
        f"- 有效画像数量：{summary['valid_profile_count']}",
        f"- 数据不足数量：{summary['insufficient_data_count']}",
        f"- Beta/capture 基准：{payload['benchmark_code']}",
        f"- 基准警告：{summary['benchmark_warning'] or '无'}",
        f"- risk_profile 分布：{summary['risk_profile_distribution']}",
        f"- structural_risk_profile 分布：{summary['structural_risk_profile_distribution']}",
        f"- style_profile 分布：{summary['style_profile_distribution']}",
        f"- UNKNOWN style 数量：{summary['unknown_style_count']}",
        "",
        "## realized risk / compatibility alias",
        "- risk_score / risk_profile 为兼容字段，本轮重新定义为 realized_risk_score / realized_risk_profile。",
        "- realized risk 表示 ETF 最近历史行情中实际表现出来的风险水平。",
        "- 所有数值指标使用全 ETF 截面分位数，不用“科技=80、证券=90”这种人工打分。",
        f"- 权重：{payload['risk_score_method']['weights']}",
        "- 缺失指标不填 0，而是按可用指标重新归一权重，并记录 missing_feature_count。",
        "",
        "## structural risk 方法",
        "- structural risk 表示 ETF 基于资产类别、集中度、风格属性、长期风险特征形成的较稳定风险性格。",
        "- Structural Risk != Realized Risk；Style Profile != Risk Profile。",
        f"- 权重：{payload['structural_risk_method']['weights']}",
        f"- 初始阈值与约束：{payload['structural_risk_method']['profile_thresholds']}",
        "",
        "## realized_risk_score Top 20",
        _rows_table(_top_rows(rows, True, 20), ["symbol", "name", "group", "type", "realized_risk_score", "realized_risk_profile", "structural_risk_profile", "style_profile", "data_quality"]),
        "",
        "## realized_risk_score Bottom 20",
        _rows_table(_top_rows(rows, False, 20), ["symbol", "name", "group", "type", "realized_risk_score", "realized_risk_profile", "structural_risk_profile", "style_profile", "data_quality"]),
        "",
        "## 当前正式模拟仓风险画像",
        f"- 持仓加权 realized_risk_score：{_fmt(portfolio.get('weighted_realized_risk_score'))}",
        f"- 持仓加权 structural_risk_score：{_fmt(portfolio.get('weighted_structural_risk_score'))}",
        f"- realized OFFENSIVE/HIGH_BETA 持仓权重：{_pct(portfolio.get('offensive_high_beta_weight'))}",
        f"- structural OFFENSIVE/HIGH_BETA 持仓权重：{_pct(portfolio.get('structural_offensive_high_beta_weight'))}",
        f"- structural CORE/DEFENSIVE 持仓权重：{_pct(portfolio.get('core_defensive_weight'))}",
        f"- 是否缺少 CORE/DEFENSIVE：{portfolio.get('missing_core_defensive')}",
        _rows_table(portfolio.get("rows", []), ["symbol", "name", "current_weight", "realized_risk_score", "realized_risk_profile", "structural_risk_score", "structural_risk_profile", "style_profile", "volatility_60d", "beta_60d"]),
        "",
        "## BUY Ranking Top 10 风险结构",
        f"- Top 10 平均 realized_risk_score：{_fmt(buy.get('top10_avg_realized_risk_score'))}",
        f"- Top 10 平均 structural_risk_score：{_fmt(buy.get('top10_avg_structural_risk_score'))}",
        f"- realized OFFENSIVE/HIGH_BETA 占比：{_pct(buy.get('offensive_high_beta_ratio'))}",
        f"- structural OFFENSIVE/HIGH_BETA 占比：{_pct(buy.get('structural_offensive_high_beta_ratio'))}",
        f"- CORE/DEFENSIVE 占比：{_pct(buy.get('core_defensive_ratio'))}",
        f"- 是否明显偏进攻：{buy.get('is_ranking_offensive_tilt')}",
        _rows_table(buy.get("rows", []), ["rank", "symbol", "name", "group", "rank_score", "realized_risk_score", "realized_risk_profile", "structural_risk_score", "structural_risk_profile", "style_profile"]),
        "",
        "## 重点 ETF",
        _rows_table([summary["focus_symbols"].get(symbol, {}) for symbol in FOCUS_SYMBOLS], ["symbol", "name", "group", "type", "style_profile", "realized_risk_score", "realized_risk_profile", "structural_risk_score", "structural_risk_profile", "volatility_60d", "beta_60d", "data_quality"]),
        "",
        "## 研究边界",
        "- research_only=true。",
        "- execution_allowed=false。",
        "- 不修改 paper_trade_engine / paper_trades / paper_positions / BUY ranking / market_regime。",
    ]
    return "\n".join(lines)


def render_source_audit(audit: dict[str, Any]) -> str:
    lines = [
        "# ETF Risk Profile 来源审计",
        "",
        "本审计只读取本地文件，不修改 watchlist 或交易规则。",
        "",
        "## 结论",
        f"- 期望 data/watchlist.csv 是否存在：{audit['expected_data_watchlist_exists']}",
        f"- 实际 watchlist：{audit['actual_watchlist_path'] or '未找到'}",
        f"- watchlist group：{audit['watchlist_groups']}",
        f"- watchlist type：{audit['watchlist_types']}",
        f"- etf_type 分布：{audit['classification_etf_types']}",
        f"- risk_profile 分布：{audit['classification_risk_profiles']}",
        f"- unknown 分类数量：{audit['unknown_classification_count']}",
        f"- profile UNKNOWN style 数量：{audit['profile_unknown_style_count']}",
        "",
        "## 现有定义",
        f"- high_beta：{audit['high_beta_definition']}",
        f"- broad_base：{audit['broad_base_definition']}",
        "",
        "## 可用输入",
        f"- 人工标签字段：{audit['manual_label_fields']}",
        f"- 历史行情字段：{audit['historical_market_fields']}",
        f"- 综合可用输入：{audit['usable_inputs']}",
        "",
        "## 关键词代码命中 Top 20",
        _rows_table(audit.get("keyword_hits", [])[:20], ["keyword", "file_count", "hit_count", "example_files"]),
        "",
        "## 安全边界",
        "- watchlist_modified=false。",
        "- execution_allowed=false。",
    ]
    return "\n".join(lines)


def render_style_unknown_audit(audit: dict[str, Any]) -> str:
    lines = [
        "# ETF Style UNKNOWN 审计",
        "",
        "本报告列出仍无法自动判断 style_profile 的 ETF。系统宁可保留 UNKNOWN，也不乱猜。",
        "",
        f"- ETF 总数：{audit.get('total_etf')}",
        f"- UNKNOWN 数量：{audit.get('unknown_count')}",
        f"- 目标 UNKNOWN <= {audit.get('unknown_target')}",
        f"- 是否达标：{audit.get('target_met')}",
        f"- 原因：{audit.get('reason')}",
        "",
        _rows_table(audit.get("rows", []), ["symbol", "name", "group", "type", "pool", "data_quality", "classification_reason", "manual_override_candidate"]),
        "",
        "## 安全边界",
        "- 本审计不修改 BUY ranking、market_regime、模拟仓或交易记录。",
    ]
    return "\n".join(lines)


def render_structural_analysis(payload: dict[str, Any]) -> str:
    focus_rows = [payload.get("focus_symbols", {}).get(symbol, {"symbol": symbol}) for symbol in FOCUS_SYMBOLS]
    large_gap = [
        row for row in payload.get("rows", [])
        if row.get("gap_direction") in {"structural_gt_realized", "realized_gt_structural"}
    ][:40]
    lines = [
        "# Structural vs Realized Risk 差异分析",
        "",
        "本报告解释结构性风险与近期实现风险的差异。它不是交易信号，不修改 ranking 或模拟仓。",
        "",
        f"- 行数：{payload.get('row_count')}",
        f"- 差异方向分布：{payload.get('gap_distribution')}",
        "",
        "## 重点 ETF",
        _rows_table(focus_rows, ["symbol", "name", "style_profile", "structural_risk_score", "structural_risk_profile", "realized_risk_score", "realized_risk_profile", "score_gap", "profile_gap", "gap_direction", "gap_reason"]),
        "",
        "## 显著差异样本 Top 40",
        _rows_table(large_gap, ["symbol", "name", "style_profile", "structural_risk_score", "structural_risk_profile", "realized_risk_score", "realized_risk_profile", "score_gap", "gap_direction", "gap_reason"]),
        "",
        "## 512880 解释",
        "- 512880 证券 ETF 属于金融高 beta 情绪资产，结构性风险可为 HIGH_BETA。",
        "- 如果近期 realized_risk_profile 不是 HIGH_BETA，表示近期行情中的实际波动/回撤/beta 暂时收敛。",
        "- 这不是冲突，也不应为了消除差异反向修改 realized risk。",
        "- high_beta watch 应继续保留，但仍为观察层，不自动减仓或卖出。",
    ]
    return "\n".join(lines)


def build_phase_1_5_payload(profile_payload: dict[str, Any], unknown_audit: dict[str, Any], structural_analysis: dict[str, Any], buy_analysis: dict[str, Any], consistency: dict[str, Any]) -> dict[str, Any]:
    summary = profile_payload.get("summary", {})
    portfolio = profile_payload.get("portfolio_risk_profile", {})
    focus = summary.get("focus_symbols", {})
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "phase": "Regime & Risk Allocation Phase 1.5",
        "target": "ETF Style Profile + Structural vs Realized Risk split",
        "unknown_before": 73,
        "unknown_after": unknown_audit.get("unknown_count"),
        "unknown_target": unknown_audit.get("unknown_target"),
        "unknown_target_met": unknown_audit.get("target_met"),
        "style_profile_distribution": summary.get("style_profile_distribution", {}),
        "realized_risk_definition": "recent market-data realized risk based on volatility/beta/drawdown/downside/capture cross-sectional scoring",
        "structural_risk_definition": "stable asset/style/concentration/long-cycle risk character based on ETF type, style keywords and longer-window risk metrics",
        "structural_risk_method": profile_payload.get("structural_risk_method", {}),
        "realized_risk_profile_distribution": summary.get("realized_risk_profile_distribution", {}),
        "structural_risk_profile_distribution": summary.get("structural_risk_profile_distribution", {}),
        "focus_symbols": {symbol: focus.get(symbol, {}) for symbol in FOCUS_SYMBOLS},
        "structural_vs_realized_focus": structural_analysis.get("focus_symbols", {}),
        "portfolio_weighted_realized_risk_score": portfolio.get("weighted_realized_risk_score"),
        "portfolio_weighted_structural_risk_score": portfolio.get("weighted_structural_risk_score"),
        "buy_top10_avg_realized_risk_score": buy_analysis.get("top10_avg_realized_risk_score"),
        "buy_top10_avg_structural_risk_score": buy_analysis.get("top10_avg_structural_risk_score"),
        "buy_top10_realized_offensive_high_beta_ratio": buy_analysis.get("offensive_high_beta_ratio"),
        "buy_top10_structural_offensive_high_beta_ratio": buy_analysis.get("structural_offensive_high_beta_ratio"),
        "ranking_offensive_tilt": buy_analysis.get("is_ranking_offensive_tilt"),
        "high_beta_structural_consistent_count": consistency.get("high_beta_structural_consistent_count"),
        "high_beta_realized_gap_count": consistency.get("realized_gap_count"),
        "ready_for_regime_audit_phase": bool(unknown_audit.get("target_met")),
        "ready_for_execution": False,
        "research_only": True,
        "safety": _safety_payload(),
    }


def render_phase_1_5_report(payload: dict[str, Any]) -> str:
    focus = payload.get("focus_symbols", {})
    focus_rows = [focus.get(symbol, {"symbol": symbol}) for symbol in FOCUS_SYMBOLS]
    lines = [
        "# Regime & Risk Allocation Phase 1.5 - Style / Structural Profile",
        "",
        "本报告为研究层，不是交易方案。Structural / Realized Risk 均不接执行层。",
        "",
        "## 摘要",
        f"- UNKNOWN 从 {payload.get('unknown_before')} 降至：{payload.get('unknown_after')}",
        f"- UNKNOWN 目标 <= {payload.get('unknown_target')}：{payload.get('unknown_target_met')}",
        f"- style_profile 分布：{payload.get('style_profile_distribution')}",
        f"- realized risk 分布：{payload.get('realized_risk_profile_distribution')}",
        f"- structural risk 分布：{payload.get('structural_risk_profile_distribution')}",
        "",
        "## 定义",
        f"- Realized Risk：{payload.get('realized_risk_definition')}",
        f"- Structural Risk：{payload.get('structural_risk_definition')}",
        "- Structural Risk != Realized Risk。",
        "- Style Profile != Risk Profile。",
        "",
        "## Structural Risk 权重",
        f"- {payload.get('structural_risk_method', {}).get('weights')}",
        f"- 分层：{payload.get('structural_risk_method', {}).get('profile_thresholds')}",
        "",
        "## 当前组合双风险画像",
        f"- 组合加权 realized_risk_score：{_fmt(payload.get('portfolio_weighted_realized_risk_score'))}",
        f"- 组合加权 structural_risk_score：{_fmt(payload.get('portfolio_weighted_structural_risk_score'))}",
        "- 若 515000 权重较大，组合结构性风险会偏成长/进攻。",
        "- 若组合缺少 CORE/DEFENSIVE style，应进入后续 Regime Audit 观察，不自动调仓。",
        "",
        "## BUY Ranking 双风险结构",
        f"- BUY Top10 平均 realized_risk_score：{_fmt(payload.get('buy_top10_avg_realized_risk_score'))}",
        f"- BUY Top10 平均 structural_risk_score：{_fmt(payload.get('buy_top10_avg_structural_risk_score'))}",
        f"- realized OFFENSIVE/HIGH_BETA 占比：{_pct(payload.get('buy_top10_realized_offensive_high_beta_ratio'))}",
        f"- structural OFFENSIVE/HIGH_BETA 占比：{_pct(payload.get('buy_top10_structural_offensive_high_beta_ratio'))}",
        f"- ranking 是否偏进攻：{payload.get('ranking_offensive_tilt')}",
        "",
        "## 重点 ETF 双风险画像",
        _rows_table(focus_rows, ["symbol", "name", "group", "style_profile", "realized_risk_score", "realized_risk_profile", "structural_risk_score", "structural_risk_profile", "data_quality"]),
        "",
        "## 512880 差异解释",
        "- 512880 证券 ETF 的人工 high_beta 来源是券商/证券类 ETF 的长期市场情绪弹性和 beta 属性。",
        "- 本轮 structural_risk_profile 可保持 HIGH_BETA；realized_risk_profile 可根据近期行情为 BALANCED/OFFENSIVE 等。",
        "- 这表示资产结构上高弹性，但近期实际波动风险暂处中等或未完全释放，属于合理差异。",
        "- high_beta watch 应继续保留，仍不自动交易。",
        "",
        "## 是否进入 Regime Audit Phase",
        f"- ready_for_regime_audit_phase：{payload.get('ready_for_regime_audit_phase')}",
        "- 仅表示可以继续做 Regime Audit 研究，不表示接入执行层。",
        "",
        "## 安全边界",
        "- research_only=true。",
        "- ready_for_execution=false。",
        "- 未修改 BUY ranking / market_regime / paper_trade_engine / paper_trades / paper_positions。",
        "- 不接券商 API，不真实下单，不读取真实账户，不暴露 token/密码。",
    ]
    return "\n".join(lines)


def render_buy_analysis(payload: dict[str, Any]) -> str:
    return "\n".join([
        "# BUY Ranking 风险画像分析",
        "",
        "本报告只分析当前 BUY Top 10 的风险结构，不修改 ranking。",
        "",
        f"- Top 10 数量：{payload.get('top10_count')}",
        f"- Top10 avg realized_risk_score：{_fmt(payload.get('top10_avg_realized_risk_score'))}",
        f"- Top10 avg structural_risk_score：{_fmt(payload.get('top10_avg_structural_risk_score'))}",
        f"- realized risk_profile 分布：{payload.get('realized_risk_profile_distribution')}",
        f"- structural risk_profile 分布：{payload.get('structural_risk_profile_distribution')}",
        f"- style_profile 分布：{payload.get('style_profile_distribution')}",
        f"- realized OFFENSIVE/HIGH_BETA 占比：{_pct(payload.get('offensive_high_beta_ratio'))}",
        f"- structural OFFENSIVE/HIGH_BETA 占比：{_pct(payload.get('structural_offensive_high_beta_ratio'))}",
        f"- CORE/DEFENSIVE 占比：{_pct(payload.get('core_defensive_ratio'))}",
        f"- 是否天然偏进攻：{payload.get('is_ranking_offensive_tilt')}",
        "",
        _rows_table(payload.get("rows", []), ["rank", "symbol", "name", "group", "rank_score", "realized_risk_score", "realized_risk_profile", "structural_risk_score", "structural_risk_profile", "style_profile", "data_quality"]),
        "",
        "结论：如果 Top BUY 同时集中在 realized 与 structural OFFENSIVE/HIGH_BETA，说明 ranking 可能存在风险偏好偏置；本报告只提示后续 Regime Audit，不直接改变本期执行层。",
    ])


def render_consistency_audit(payload: dict[str, Any]) -> str:
    return "\n".join([
        "# ETF Risk Profile 一致性审计",
        "",
        "本报告分别对比 Structural Risk 与 Realized Risk，不要求人工 high_beta 必须与近期 realized HIGH_BETA 完全一致。",
        "",
        f"- 现有 high_beta 标的数：{payload.get('high_beta_existing_count')}",
        f"- high_beta structural 一致数量：{payload.get('high_beta_structural_consistent_count')}",
        f"- high_beta realized offensive 数量：{payload.get('high_beta_realized_offensive_count')}",
        f"- high_beta realized gap 数量：{payload.get('realized_gap_count')}",
        f"- broad_base 候选数量：{payload.get('broad_base_candidate_count')}",
        f"- 债券 ETF 数量：{payload.get('bond_count')}",
        f"- structural 冲突数量：{payload.get('conflict_count')}",
        f"- 冲突解释：{payload.get('conflict_interpretation')}",
        "",
        "## high_beta structural 冲突",
        _rows_table(payload.get("high_beta_structural_conflicts", []), ["symbol", "name", "structural_risk_score", "structural_risk_profile", "realized_risk_profile", "style_profile", "conflict_reason"]),
        "",
        "## high_beta realized gap（不自动视为错误）",
        _rows_table(payload.get("high_beta_realized_gaps", []), ["symbol", "name", "structural_risk_profile", "realized_risk_profile", "style_profile", "gap_reason"]),
        "",
        "## broad_base 冲突",
        _rows_table(payload.get("broad_base_conflicts", []), ["symbol", "name", "type", "structural_risk_score", "structural_risk_profile", "realized_risk_profile", "style_profile", "conflict_reason"]),
        "",
        "## bond 冲突",
        _rows_table(payload.get("bond_conflicts", []), ["symbol", "name", "structural_risk_score", "structural_risk_profile"]),
    ])


def render_phase_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    portfolio = payload["portfolio_risk_profile"]
    buy = payload["buy_ranking_risk_profile"]
    return "\n".join([
        "# Regime & Risk Allocation Phase 1 - ETF Risk Profile",
        "",
        "本轮目标：建立 ETF 自身 Risk Profile / Style Profile，为未来 Regime-Asset Fit 做准备。",
        "",
        "## 方法",
        f"- risk_score 输入：{list(payload['risk_score_method']['weights'].keys())}",
        f"- risk_score 权重：{payload['risk_score_method']['weights']}",
        "- risk_profile 分层：按全池 risk_score 分位数切为 DEFENSIVE / CORE / BALANCED / OFFENSIVE / HIGH_BETA。",
        "- style_profile：使用 watchlist group、type、ETF 名称、宽基/主题/债券/QDII 规则生成。",
        "",
        "## 当前结果",
        f"- ETF 总数：{summary.get('total_etf')}",
        f"- 有效画像数量：{summary.get('valid_profile_count')}",
        f"- 数据不足数量：{summary.get('insufficient_data_count')}",
        f"- risk_profile 分布：{summary.get('risk_profile_distribution')}",
        f"- style_profile 分布：{summary.get('style_profile_distribution')}",
        "",
        "## 当前持仓风险画像",
        f"- 加权 risk_score：{_fmt(portfolio.get('weighted_risk_score'))}",
        f"- 平均 risk_score：{_fmt(portfolio.get('avg_risk_score'))}",
        f"- 是否偏进攻：{portfolio.get('is_offensive_tilt')}",
        f"- 是否缺少 CORE/DEFENSIVE：{portfolio.get('missing_core_defensive')}",
        "",
        "## BUY Ranking 风险结构",
        f"- Top 10 平均 risk_score：{_fmt(buy.get('top10_avg_risk_score'))}",
        f"- OFFENSIVE/HIGH_BETA 占比：{_pct(buy.get('offensive_high_beta_ratio'))}",
        f"- 是否偏进攻：{buy.get('is_ranking_offensive_tilt')}",
        "",
        "## 一致性与下一阶段",
        f"- high_beta 一致数量：{payload['consistency_audit'].get('high_beta_consistent_count')}",
        f"- broad_base 冲突：{len(payload['consistency_audit'].get('broad_base_conflicts', []))}",
        f"- 当前是否足以做 Regime Fit：{payload.get('ready_for_regime_fit')}",
        "- 下一阶段需要先观察 risk_profile 稳定性，再做 preview-only 的 Regime Fit。",
        "",
        "## 安全边界",
        "- research_only=true。",
        "- ready_for_execution=false。",
        "- 未修改 BUY ranking / market_regime / paper_trade_engine / paper_trades / paper_positions。",
        "- 不接券商 API，不真实下单，不读取真实账户，不暴露 token/密码。",
    ])


def _window_return(prices: pd.DataFrame, window: int) -> float | None:
    if len(prices) <= window:
        return None
    close = prices["close"].dropna()
    if len(close) <= window:
        return None
    start = close.iloc[-window - 1]
    end = close.iloc[-1]
    if start == 0:
        return None
    return _round(end / start - 1.0)


def _annualized_volatility(returns: pd.Series, window: int) -> float | None:
    sub = returns.dropna().tail(window)
    if len(sub) < max(10, window // 2):
        return None
    return _round(float(sub.std(ddof=1) * math.sqrt(252)))


def _downside_volatility(returns: pd.Series, window: int) -> float | None:
    sub = returns.dropna().tail(window)
    sub = sub[sub < 0]
    if len(sub) < 5:
        return None
    return _round(float(sub.std(ddof=1) * math.sqrt(252)))


def _beta(returns: pd.Series, benchmark: pd.Series, window: int) -> float | None:
    aligned = pd.concat([returns.rename("asset"), benchmark.rename("bench")], axis=1, sort=False).dropna().tail(window)
    if len(aligned) < max(20, window // 2):
        return None
    variance = aligned["bench"].var(ddof=1)
    if variance == 0 or pd.isna(variance):
        return None
    covariance = aligned["asset"].cov(aligned["bench"])
    return _round(float(covariance / variance))


def _max_drawdown(prices: pd.DataFrame, window: int) -> float | None:
    close = prices["close"].dropna().tail(window)
    if len(close) < max(20, window // 2):
        return None
    running_max = close.cummax()
    drawdown = close / running_max - 1.0
    return _round(float(drawdown.min()))


def _capture_ratio(returns: pd.Series, benchmark: pd.Series, window: int, up: bool) -> float | None:
    aligned = pd.concat([returns.rename("asset"), benchmark.rename("bench")], axis=1, sort=False).dropna().tail(window)
    if len(aligned) < max(20, window // 2):
        return None
    mask = aligned["bench"] > 0 if up else aligned["bench"] < 0
    sub = aligned[mask]
    if len(sub) < 5:
        return None
    bench_sum = sub["bench"].sum()
    if bench_sum == 0 or pd.isna(bench_sum):
        return None
    return _round(float(sub["asset"].sum() / bench_sum))


def _daily_returns(prices: pd.DataFrame) -> pd.Series:
    if prices.empty or "date" not in prices or "close" not in prices:
        return pd.Series(dtype=float)
    series = prices.set_index("date")["close"].astype(float).sort_index().pct_change()
    return series.replace([np.inf, -np.inf], np.nan)


def _benchmark_warning(benchmark: pd.DataFrame) -> str:
    if benchmark.empty:
        return "510300 benchmark file missing or unreadable; beta/capture mostly null."
    if len(benchmark) < 120:
        return "510300 benchmark has fewer than 120 rows; beta/capture reliability is limited."
    latest = benchmark["date"].max()
    if pd.isna(latest):
        return "510300 benchmark date parse failed."
    return ""


def _keyword_search() -> list[dict[str, Any]]:
    keywords = ["group", "type", "high_beta", "is_broad_base", "is_quasi_broad_base", "sector", "theme", "growth", "defensive", "bond", "dividend", "low_vol"]
    files = [p for p in list((PROJECT_ROOT / "src").glob("*.py")) + list((PROJECT_ROOT / "dashboard").glob("*.py")) + list((PROJECT_ROOT / "app").glob("**/*.py")) + list((PROJECT_ROOT / "app").glob("**/*.jsx")) if p.is_file()]
    rows = []
    for keyword in keywords:
        hit_files = []
        hit_count = 0
        for path in files:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            count = text.count(keyword)
            if count:
                hit_count += count
                hit_files.append(str(path.relative_to(PROJECT_ROOT)))
        rows.append({"keyword": keyword, "file_count": len(hit_files), "hit_count": hit_count, "example_files": ", ".join(hit_files[:5])})
    return sorted(rows, key=lambda row: row["hit_count"], reverse=True)


def _read_buy_ranking() -> list[dict[str, Any]]:
    path = REPORT_DIR / "buy_signal_ranking.md"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows = []
    in_table = False
    headers: list[str] = []
    for line in lines:
        if line.startswith("| rank |"):
            headers = [part.strip() for part in line.strip("|").split("|")]
            in_table = True
            continue
        if in_table and line.startswith("| ---"):
            continue
        if in_table:
            if not line.startswith("|"):
                break
            values = [part.strip() for part in line.strip("|").split("|")]
            if len(values) != len(headers):
                continue
            raw = dict(zip(headers, values))
            rows.append({
                "rank": _maybe_int(raw.get("rank")),
                "symbol": _clean_symbol(raw.get("code")),
                "name": raw.get("name", ""),
                "group": raw.get("group", ""),
                "rank_score": _maybe_float(raw.get("rank_score")),
                "mid_trend_signal": raw.get("mid", raw.get("mid_trend_signal", "")),
                "short_swing_signal": raw.get("short", raw.get("short_swing_signal", "")),
            })
    return rows


def _row_by_symbol(rows: list[dict[str, Any]], symbol: str) -> dict[str, Any]:
    for row in rows:
        if str(row.get("symbol")) == symbol:
            return row
    return {"symbol": symbol, "missing": True}


def _top_rows(rows: list[dict[str, Any]], descending: bool, limit: int) -> list[dict[str, Any]]:
    valid = [row for row in rows if pd.notna(_float(row.get("risk_score"), fallback=np.nan))]
    return sorted(valid, key=lambda row: _float(row.get("risk_score"), fallback=-1), reverse=descending)[:limit]


def _value_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get(field) or "UNKNOWN")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _weighted_counts(rows: list[dict[str, Any]], field: str, weight_field: str) -> dict[str, float]:
    counts: dict[str, float] = {}
    for row in rows:
        key = str(row.get(field) or "UNKNOWN")
        counts[key] = counts.get(key, 0.0) + _float(row.get(weight_field), fallback=0.0)
    return {key: round(value, 6) for key, value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))}


def _rows_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    if not rows:
        return "\n".join([header, sep, "| " + " | ".join("" for _ in columns) + " |"])
    body = []
    for row in rows:
        body.append("| " + " | ".join(_fmt_cell(row.get(col)) for col in columns) + " |")
    return "\n".join([header, sep, *body])


def _safety_payload() -> dict[str, bool]:
    return {
        "broker_api": False,
        "real_order": False,
        "real_account": False,
        "credentials_read": False,
        "paper_trade_engine_modified": False,
        "paper_trades_modified": False,
        "paper_positions_modified": False,
        "ranking_modified": False,
        "market_regime_modified": False,
        "execution_allowed": False,
    }


def _symbol_from_path(path: Path) -> str:
    match = re.fullmatch(r"(?:sh|sz)_(\d{6})\.csv", path.name)
    return match.group(1) if match else ""


def _clean_symbol(value: object) -> str:
    match = re.search(r"(\d{6})", str(value or ""))
    return match.group(1) if match else ""


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")
    except Exception:
        return pd.DataFrame()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _json_dumps(payload: Any) -> str:
    return json.dumps(_sanitize_json(payload), ensure_ascii=False, indent=2)


def _sanitize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _sanitize_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_json(v) for v in value]
    if isinstance(value, tuple):
        return [_sanitize_json(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.floating, float)):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return None
        return float(value)
    if isinstance(value, pd.Timestamp):
        return _date_str(value)
    if value is pd.NaT:
        return None
    return value


def _round(value: float | None, digits: int = 6) -> float | None:
    if value is None or pd.isna(value) or math.isinf(float(value)):
        return None
    return round(float(value), digits)


def _float(value: object, fallback: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    if math.isnan(number) or math.isinf(number):
        return fallback
    return number


def _maybe_float(value: object) -> float | None:
    try:
        return _round(float(str(value).replace("%", "")))
    except (TypeError, ValueError):
        return None


def _maybe_int(value: object) -> int | None:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "是"}


def _date_str(value: object) -> str:
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def _has(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text.lower() for keyword in keywords)


def _fmt(value: object) -> str:
    number = _float(value, fallback=np.nan)
    if pd.isna(number):
        return "N/A"
    return f"{number:.4f}"


def _pct(value: object) -> str:
    number = _float(value, fallback=np.nan)
    if pd.isna(number):
        return "N/A"
    return f"{number:.2%}"


def _fmt_cell(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return ""
        return f"{float(value):.4f}"
    text = str(value).replace("|", "/").replace("\n", " ")
    return text[:240]


if __name__ == "__main__":
    main()
