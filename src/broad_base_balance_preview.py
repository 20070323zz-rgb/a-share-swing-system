"""Broad-base balance preview for the paper portfolio.

This module is observation-only. It does not write trades, does not change
positions, and does not connect to any broker or account API.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from config import DATA_DIR, PAPER_POSITIONS_FILE, PROJECT_ROOT, REPORT_DIR, WATCHLIST_FILE
from valuation import load_latest_position_valuation


BUY_RANKING_FILE = REPORT_DIR / "buy_signal_ranking.md"
LATEST_RANKING_FILE = REPORT_DIR / "latest_ranking.md"
SIGNALS_FILE = REPORT_DIR / "signals.csv"
STRATEGY_PREVIEW_FILE = REPORT_DIR / "strategy_enhancement_preview.csv"
PORTFOLIO_EXPOSURE_FILE = REPORT_DIR / "portfolio_exposure.json"
HIGH_BETA_FILE = REPORT_DIR / "high_beta_risk_watch.json"
CSV_FILE = REPORT_DIR / "broad_base_balance_preview.csv"
JSON_FILE = REPORT_DIR / "broad_base_balance_preview.json"
REPORT_FILE = REPORT_DIR / "broad_base_balance_preview.md"

PREVIEW_ADD_AMOUNT = 500.0
BROAD_BASE_TARGET_MIN = 0.20
GROUP_CONCENTRATION_WATCH = 0.50
FINANCE_CONCENTRATION_WATCH = 0.40
HIGH_BETA_WATCH = 0.20

TRADITIONAL_BROAD_CODES = {"510300", "510500", "512100", "510050", "510180"}
QUASI_BROAD_CODES = {"159915", "588000", "588080", "159901", "159949"}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = build_broad_base_balance_preview()
    rows = snapshot["rows"]
    pd.DataFrame(rows).to_csv(CSV_FILE, index=False)
    JSON_FILE.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_FILE.write_text(render_report(snapshot), encoding="utf-8")
    print(f"broad_base candidates: {len(rows)}")
    print(f"written: {REPORT_FILE}")


def build_broad_base_balance_preview() -> dict[str, Any]:
    valuation = load_latest_position_valuation()
    positions = valuation.get("positions", pd.DataFrame())
    watchlist = _read_csv(WATCHLIST_FILE)
    buy_ranking = _read_buy_ranking()
    latest_ranking = _read_latest_ranking()
    latest_signals = _read_latest_signals()
    strategy_preview = _read_csv(STRATEGY_PREVIEW_FILE)
    exposure = _read_json(PORTFOLIO_EXPOSURE_FILE)
    high_beta = _read_json(HIGH_BETA_FILE)

    current = _current_exposure(positions)
    candidate_symbols = _broad_candidate_symbols(watchlist, buy_ranking, strategy_preview, latest_ranking, latest_signals)
    rows = []
    for symbol in candidate_symbols:
        row = _candidate_row(
            symbol=symbol,
            watchlist=watchlist,
            buy_ranking=buy_ranking,
            latest_ranking=latest_ranking,
            latest_signals=latest_signals,
            strategy_preview=strategy_preview,
            current=current,
            positions=positions,
        )
        if row:
            rows.append(row)

    rows = sorted(
        rows,
        key=lambda item: (
            _float(item.get("balance_improvement_score")),
            _float(item.get("adjusted_score")),
            _float(item.get("raw_score")),
        ),
        reverse=True,
    )
    for idx, row in enumerate(rows, start=1):
        row["balance_candidate_rank"] = idx

    summary = _summary_payload(rows, current, exposure, high_beta, valuation.get("summary", {}))
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "observation_only": True,
        "execution_allowed": False,
        "preview_add_amount": PREVIEW_ADD_AMOUNT,
        "summary": summary,
        "rows": rows,
        "top_balance_candidates": rows[:5],
        "safety": {
            "broker_api": False,
            "real_order": False,
            "real_account": False,
            "paper_trade_engine_modified": False,
            "paper_trades_modified": False,
            "paper_positions_modified": False,
            "adjusted_preview_execution_enabled": False,
        },
        "source_files": {
            "buy_ranking": str(BUY_RANKING_FILE.relative_to(PROJECT_ROOT)),
            "latest_ranking": str(LATEST_RANKING_FILE.relative_to(PROJECT_ROOT)),
            "signals": str(SIGNALS_FILE.relative_to(PROJECT_ROOT)),
            "strategy_preview": str(STRATEGY_PREVIEW_FILE.relative_to(PROJECT_ROOT)),
            "portfolio_exposure": str(PORTFOLIO_EXPOSURE_FILE.relative_to(PROJECT_ROOT)),
        },
    }


def _candidate_row(
    symbol: str,
    watchlist: pd.DataFrame,
    buy_ranking: dict[str, dict],
    latest_ranking: dict[str, dict],
    latest_signals: dict[str, dict],
    strategy_preview: pd.DataFrame,
    current: dict[str, Any],
    positions: pd.DataFrame,
) -> dict[str, Any] | None:
    meta = _watchlist_row(symbol, watchlist)
    name = str(meta.get("name") or buy_ranking.get(symbol, {}).get("name") or latest_ranking.get(symbol, {}).get("name") or symbol)
    group = str(meta.get("group") or buy_ranking.get(symbol, {}).get("group") or latest_ranking.get(symbol, {}).get("group") or "")
    if not _is_broad_base(symbol, name, group):
        return None

    buy = buy_ranking.get(symbol, {})
    latest = latest_ranking.get(symbol, {})
    signal = latest_signals.get(symbol, {})
    preview = _preview_row(symbol, strategy_preview)
    held = _held_row(symbol, positions)
    broad_kind = _broad_kind(symbol, name)

    mid = str(buy.get("mid_trend") or latest.get("mid") or latest.get("signal") or signal.get("signal") or "N/A")
    short = str(buy.get("short_swing") or latest.get("short") or "N/A")
    raw_rank = _maybe_int(buy.get("rank")) if buy else ""
    raw_score = _first_number(buy.get("rank_score"), latest.get("composite_score"), latest.get("dual_score"), signal.get("composite_score"))
    adjusted_score = _first_number(preview.get("adjusted_rank_score_preview"), raw_score)
    adjusted_rank = _maybe_int(preview.get("adjusted_rank_preview")) if preview else ""
    current_weight = _float(held.get("market_value")) / current["total_holdings"] if held and current["total_holdings"] else 0.0

    scenario = _preview_scenario(current, PREVIEW_ADD_AMOUNT)
    concentration_reduction = max(0.0, current["max_group_weight"] - scenario["new_max_group_weight"])
    high_beta_offset = max(0.0, current["high_beta_weight"] - scenario["new_high_beta_weight"])
    balance_score = _balance_score(mid, short, raw_rank, raw_score, adjusted_rank, adjusted_score, broad_kind, scenario, concentration_reduction, high_beta_offset, signal)

    reasons = []
    if current["broad_base_weight"] <= 0:
        reasons.append("当前组合缺少宽基，加入后可补齐组合底仓观察层。")
    if broad_kind == "quasi_broad_base":
        reasons.append("成长宽基/准宽基，能补宽基但仍偏成长风格。")
    else:
        reasons.append("传统宽基，更适合降低行业/主题集中度。")
    if mid == "BUY" and short == "BUY":
        reasons.append("当前 BUY/BUY 双周期共振。")
    elif mid == "BUY":
        reasons.append("mid_trend 为 BUY，短周期仍需观察。")
    if _float(preview.get("broad_index_balance_bonus")) > 0:
        reasons.append("B1 adjusted preview 已给宽基平衡加分。")

    return {
        "symbol": symbol,
        "name": name,
        "group": group or "宽基",
        "type": "broad_index" if broad_kind == "traditional_broad_base" else "quasi_broad_base",
        "mid_trend": mid,
        "short_swing": short,
        "raw_rank": raw_rank,
        "raw_score": _round(raw_score),
        "adjusted_rank": adjusted_rank,
        "adjusted_score": _round(adjusted_score),
        "is_broad_base": broad_kind == "traditional_broad_base",
        "is_quasi_broad_base": broad_kind == "quasi_broad_base",
        "current_position": bool(held),
        "current_weight": current_weight,
        "candidate_reason": "；".join(reasons),
        "balance_improvement_score": _round(balance_score),
        "concentration_reduction_score": _round(concentration_reduction),
        "high_beta_offset_score": _round(high_beta_offset),
        "preview_add_amount": PREVIEW_ADD_AMOUNT,
        "new_broad_base_weight": scenario["new_broad_base_weight"],
        "new_finance_real_estate_weight": scenario["new_finance_real_estate_weight"],
        "new_tech_growth_weight": scenario["new_tech_growth_weight"],
        "new_high_beta_weight": scenario["new_high_beta_weight"],
        "concentration_change": concentration_reduction,
        "execution_allowed": False,
        "data_quality": _data_quality(signal, buy, latest),
    }


def _current_exposure(positions: pd.DataFrame) -> dict[str, Any]:
    rows = positions.to_dict(orient="records") if isinstance(positions, pd.DataFrame) and not positions.empty else []
    total_holdings = sum(_float(row.get("market_value")) for row in rows)
    by_group: dict[str, float] = {}
    broad_value = 0.0
    high_beta_value = 0.0
    theme_value = 0.0
    for row in rows:
        symbol = str(row.get("symbol", ""))
        name = str(row.get("name", ""))
        group = str(row.get("group", ""))
        etf_type = str(row.get("etf_type", ""))
        value = _float(row.get("market_value"))
        by_group[group or "unknown"] = by_group.get(group or "unknown", 0.0) + value
        if _is_broad_base(symbol, name, group) or etf_type == "broad_index":
            broad_value += value
        else:
            theme_value += value
        if etf_type == "high_beta" or any(key in name for key in ["证券", "券商"]):
            high_beta_value += value
    finance = by_group.get("金融地产", 0.0)
    tech = by_group.get("科技成长", 0.0)
    weights = {key: value / total_holdings for key, value in by_group.items()} if total_holdings else {}
    return {
        "total_holdings": total_holdings,
        "broad_base_market_value": broad_value,
        "theme_market_value": theme_value,
        "finance_real_estate_market_value": finance,
        "tech_growth_market_value": tech,
        "high_beta_market_value": high_beta_value,
        "broad_base_weight": broad_value / total_holdings if total_holdings else 0.0,
        "theme_weight": theme_value / total_holdings if total_holdings else 0.0,
        "finance_real_estate_weight": finance / total_holdings if total_holdings else 0.0,
        "tech_growth_weight": tech / total_holdings if total_holdings else 0.0,
        "high_beta_weight": high_beta_value / total_holdings if total_holdings else 0.0,
        "group_weights": weights,
        "max_group_weight": max(weights.values(), default=0.0),
    }


def _preview_scenario(current: dict[str, Any], amount: float) -> dict[str, float]:
    new_total = current["total_holdings"] + amount
    if new_total <= 0:
        return {
            "new_broad_base_weight": 0.0,
            "new_finance_real_estate_weight": 0.0,
            "new_tech_growth_weight": 0.0,
            "new_high_beta_weight": 0.0,
            "new_max_group_weight": 0.0,
        }
    new_broad = (current["broad_base_market_value"] + amount) / new_total
    new_finance = current["finance_real_estate_market_value"] / new_total
    new_tech = current["tech_growth_market_value"] / new_total
    new_high_beta = current["high_beta_market_value"] / new_total
    other_weights = []
    for group, weight_value in current.get("group_weights", {}).items():
        market_value = weight_value * current["total_holdings"]
        if group in {"金融地产", "科技成长", "宽基"}:
            continue
        other_weights.append(market_value / new_total)
    new_max = max([new_broad, new_finance, new_tech, new_high_beta, *other_weights], default=0.0)
    return {
        "new_broad_base_weight": new_broad,
        "new_finance_real_estate_weight": new_finance,
        "new_tech_growth_weight": new_tech,
        "new_high_beta_weight": new_high_beta,
        "new_max_group_weight": new_max,
    }


def _summary_payload(rows: list[dict], current: dict[str, Any], exposure: dict, high_beta: dict, valuation_summary: dict) -> dict[str, Any]:
    state_flags = []
    if current["broad_base_weight"] <= 0:
        state_flags.append("BROAD_BASE_MISSING")
    elif current["broad_base_weight"] < BROAD_BASE_TARGET_MIN:
        state_flags.append("BROAD_BASE_LIGHT")
    else:
        state_flags.append("BROAD_BASE_BALANCED")
    if current["max_group_weight"] >= GROUP_CONCENTRATION_WATCH:
        state_flags.append("THEME_CONCENTRATED")
    if current["high_beta_weight"] >= HIGH_BETA_WATCH:
        state_flags.append("HIGH_BETA_CONCENTRATED")
    elif (high_beta.get("summary") or {}).get("high_beta_exposure_state") not in {None, "", "HB_NORMAL"}:
        state_flags.append(str((high_beta.get("summary") or {}).get("high_beta_exposure_state")))

    return {
        "as_of_date": valuation_summary.get("as_of_date", ""),
        "valuation_source": valuation_summary.get("valuation_source", "paper_positions + etf_daily latest close"),
        "total_holdings_market_value": _round(current["total_holdings"]),
        "broad_base_market_value": _round(current["broad_base_market_value"]),
        "broad_base_weight": current["broad_base_weight"],
        "theme_market_value": _round(current["theme_market_value"]),
        "theme_weight": current["theme_weight"],
        "finance_real_estate_market_value": _round(current["finance_real_estate_market_value"]),
        "finance_real_estate_weight": current["finance_real_estate_weight"],
        "tech_growth_market_value": _round(current["tech_growth_market_value"]),
        "tech_growth_weight": current["tech_growth_weight"],
        "high_beta_market_value": _round(current["high_beta_market_value"]),
        "high_beta_weight": current["high_beta_weight"],
        "max_group_weight": current["max_group_weight"],
        "state_flags": state_flags,
        "broad_base_balance_state": state_flags[0],
        "theme_concentration_state": "THEME_CONCENTRATED" if "THEME_CONCENTRATED" in state_flags else "THEME_OK",
        "balance_candidate_count": len(rows),
        "top_balance_candidates": rows[:5],
        "adjusted_preview_execution_enabled": False,
        "execution_allowed": False,
        "preview_add_amount": PREVIEW_ADD_AMOUNT,
        "portfolio_exposure_status": (exposure.get("summary") or {}).get("overall_status", "N/A") if isinstance(exposure, dict) else "N/A",
        "summary_text": _summary_text(state_flags, rows),
    }


def render_report(snapshot: dict[str, Any]) -> str:
    summary = snapshot["summary"]
    rows = snapshot["rows"]
    lines = [
        f"# 宽基平衡 adjusted preview 观察报告 {snapshot['generated_at']}",
        "",
        "本报告只做宽基平衡 preview，不自动买入、不自动调仓、不修改 paper_trades.csv / paper_positions.csv，不接券商 API。",
        "",
        "## 摘要结论",
        f"- 当前宽基占比：{_pct(summary.get('broad_base_weight'))}",
        f"- 当前行业/主题占比：{_pct(summary.get('theme_weight'))}",
        f"- 金融地产组占比：{_pct(summary.get('finance_real_estate_weight'))}",
        f"- 科技成长组占比：{_pct(summary.get('tech_growth_weight'))}",
        f"- high_beta 占比：{_pct(summary.get('high_beta_weight'))}",
        f"- 组合状态：{', '.join(summary.get('state_flags', []))}",
        f"- 候选数量：{summary.get('balance_candidate_count', 0)}",
        f"- preview 假设加入金额：{_money(snapshot.get('preview_add_amount'))}",
        "- adjusted preview 是否接入执行层：false",
        "",
        "## 当前判断",
        f"- {summary.get('summary_text', '')}",
        "- BUY ranking 当前仍偏证券、科技、科创、AI；宽基平衡层只用于观察候选，不替代原始 BUY ranking。",
        "- 若后续要进入正式规则，需要至少经过 shadow tracking、回测和人工确认。",
        "",
        "## 宽基平衡候选",
        "| rank | symbol | name | type | mid | short | raw_rank | raw_score | adjusted_rank | adjusted_score | balance_score | 当前持有 | data_quality | reason |",
        "| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('balance_candidate_rank')} | {row.get('symbol')} | {row.get('name')} | {row.get('type')} | "
            f"{row.get('mid_trend')} | {row.get('short_swing')} | {row.get('raw_rank')} | {_fmt(row.get('raw_score'))} | "
            f"{row.get('adjusted_rank')} | {_fmt(row.get('adjusted_score'))} | {_fmt(row.get('balance_improvement_score'))} | "
            f"{'是' if row.get('current_position') else '否'} | {row.get('data_quality')} | {str(row.get('candidate_reason','')).replace('|','/')} |"
        )
    lines += [
        "",
        "## 500 元假设情景",
        "以下只是假设情景，不修改现金、不修改持仓、不写交易流水、不作为买入信号。",
        "",
        "| symbol | new_broad_base_weight | new_finance_real_estate_weight | new_tech_growth_weight | new_high_beta_weight | concentration_change |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows[:8]:
        lines.append(
            f"| {row.get('symbol')} | {_pct(row.get('new_broad_base_weight'))} | {_pct(row.get('new_finance_real_estate_weight'))} | "
            f"{_pct(row.get('new_tech_growth_weight'))} | {_pct(row.get('new_high_beta_weight'))} | {_pct(row.get('concentration_change'))} |"
        )
    focus = {row["symbol"]: row for row in rows if row.get("symbol") in {"588000", "159915", "510300"}}
    lines += ["", "## 重点观察标的"]
    for symbol in ["588000", "159915", "510300"]:
        row = focus.get(symbol)
        if not row:
            lines.append(f"- {symbol}：当前未进入宽基平衡候选或数据不足。")
            continue
        lines.append(
            f"- {symbol} {row.get('name')}：mid={row.get('mid_trend')}，short={row.get('short_swing')}，"
            f"raw_score={_fmt(row.get('raw_score'))}，adjusted_score={_fmt(row.get('adjusted_score'))}，"
            f"balance_rank={row.get('balance_candidate_rank')}。"
        )
    lines += [
        "",
        "## 为什么不能自动执行",
        "- 本模块是 adjusted preview / observation，不是正式买入规则。",
        "- 宽基平衡是否有效，需要后续 shadow tracking 和回测验证。",
        "- 当前组合仍有 REVIEW、HB_WATCH 等观察状态，不能绕过人工复核。",
        "- 任何正式规则变化都需要单独回到规则层确认。",
        "",
        "## 安全边界",
        "- 不接券商 API。",
        "- 不真实下单。",
        "- 不读取真实账户。",
        "- 不修改 paper_trade_engine.py。",
        "- 不修改 paper_trades.csv / paper_positions.csv。",
        "- adjusted preview 未接入执行层。",
    ]
    return "\n".join(lines) + "\n"


def _balance_score(
    mid: str,
    short: str,
    raw_rank: object,
    raw_score: float,
    adjusted_rank: object,
    adjusted_score: float,
    broad_kind: str,
    scenario: dict[str, float],
    concentration_reduction: float,
    high_beta_offset: float,
    signal: dict,
) -> float:
    score = 0.0
    score += 20.0 if mid == "BUY" else 10.0 if mid == "WATCH" else 0.0
    score += 15.0 if short == "BUY" else 6.0 if short == "WATCH" else 0.0
    score += max(0.0, min(_float(raw_score), 100.0)) * 0.15
    score += max(0.0, min(_float(adjusted_score), 100.0)) * 0.15
    score += 8.0 if _float(raw_rank, 999) <= 5 else 4.0 if _float(raw_rank, 999) <= 15 else 0.0
    score += 8.0 if _float(adjusted_rank, 999) <= 5 else 4.0 if _float(adjusted_rank, 999) <= 15 else 0.0
    score += 8.0 if broad_kind == "traditional_broad_base" else 5.0
    score += min(14.0, scenario["new_broad_base_weight"] * 40)
    score += min(10.0, concentration_reduction * 100)
    score += min(8.0, high_beta_offset * 100)
    score += 5.0 if _data_quality(signal, {}, {}) == "ok" else 2.0
    return score


def _broad_candidate_symbols(
    watchlist: pd.DataFrame,
    buy_ranking: dict[str, dict],
    strategy_preview: pd.DataFrame,
    latest_ranking: dict[str, dict],
    latest_signals: dict[str, dict],
) -> list[str]:
    symbols: list[str] = []
    for source in [
        list(buy_ranking),
        strategy_preview["symbol"].astype(str).tolist() if not strategy_preview.empty and "symbol" in strategy_preview.columns else [],
        list(latest_ranking),
        list(latest_signals),
        watchlist["code"].astype(str).tolist() if not watchlist.empty and "code" in watchlist.columns else [],
    ]:
        for symbol in source:
            symbol = str(symbol).zfill(6) if str(symbol).isdigit() else str(symbol)
            meta = _watchlist_row(symbol, watchlist)
            probe = buy_ranking.get(symbol) or latest_ranking.get(symbol) or latest_signals.get(symbol) or meta
            name = str(probe.get("name") or "")
            group = str(probe.get("group") or meta.get("group") or "")
            if _is_broad_base(symbol, name, group) and symbol not in symbols:
                symbols.append(symbol)
    return symbols


def _read_buy_ranking() -> dict[str, dict]:
    rows = _markdown_rows(BUY_RANKING_FILE, required={"rank", "code", "rank_score"})
    result = {}
    for row in rows:
        symbol = str(row.get("code", "")).strip()
        if not symbol or symbol in result:
            continue
        result[symbol] = {
            "symbol": symbol,
            "rank": row.get("rank"),
            "name": row.get("name", symbol),
            "group": row.get("group", ""),
            "mid_trend": row.get("mid", ""),
            "short_swing": row.get("short", ""),
            "rank_score": row.get("rank_score"),
            "risk_note": row.get("风险提示", ""),
        }
    return result


def _read_latest_ranking() -> dict[str, dict]:
    rows = _markdown_rows(LATEST_RANKING_FILE, required={"代码", "名称"})
    result: dict[str, dict] = {}
    for row in rows:
        symbol = str(row.get("代码", "")).strip()
        if not symbol:
            continue
        existing = result.get(symbol, {})
        merged = {**existing}
        for key, value in row.items():
            if value not in {"", "无"}:
                merged[key] = value
        result[symbol] = {
            "symbol": symbol,
            "name": merged.get("名称", symbol),
            "group": merged.get("group", ""),
            "signal": merged.get("signal", ""),
            "mid": merged.get("mid", ""),
            "short": merged.get("short", ""),
            "composite_score": merged.get("composite_score", ""),
            "dual_score": merged.get("dual_score", ""),
            "block_reasons": merged.get("block_reasons", ""),
        }
    return result


def _read_latest_signals() -> dict[str, dict]:
    df = _read_csv(SIGNALS_FILE)
    if df.empty or "date" not in df.columns:
        return {}
    latest_date = str(df["date"].max())
    df = df[df["date"].astype(str) == latest_date].copy()
    result = {}
    for _, row in df.iterrows():
        symbol = str(row.get("code", "")).strip()
        if symbol:
            result[symbol] = row.to_dict()
    return result


def _markdown_rows(path: Path, required: set[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            header = None
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
            continue
        if not required.issubset(set(header)):
            continue
        if len(cells) != len(header):
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _watchlist_row(symbol: str, watchlist: pd.DataFrame) -> dict:
    if watchlist.empty or "code" not in watchlist.columns:
        return {}
    match = watchlist[watchlist["code"].astype(str).str.zfill(6) == str(symbol).zfill(6)]
    return match.iloc[0].to_dict() if not match.empty else {}


def _preview_row(symbol: str, preview: pd.DataFrame) -> dict:
    if preview.empty or "symbol" not in preview.columns:
        return {}
    match = preview[preview["symbol"].astype(str).str.zfill(6) == str(symbol).zfill(6)]
    return match.iloc[0].to_dict() if not match.empty else {}


def _held_row(symbol: str, positions: pd.DataFrame) -> dict:
    if positions.empty or "symbol" not in positions.columns:
        return {}
    match = positions[positions["symbol"].astype(str).str.zfill(6) == str(symbol).zfill(6)]
    return match.iloc[0].to_dict() if not match.empty else {}


def _is_broad_base(symbol: str, name: str, group: str) -> bool:
    text = f"{symbol} {name} {group}"
    if symbol in TRADITIONAL_BROAD_CODES | QUASI_BROAD_CODES:
        return True
    if "宽基" in text:
        return True
    broad_keys = ["沪深300", "中证500", "中证1000", "上证50", "上证180", "创业板", "科创50", "科创创业", "深100"]
    return any(key in text for key in broad_keys) and not any(key in text for key in ["证券", "银行", "芯片", "半导体", "AI", "人工智能", "医药", "消费"])


def _broad_kind(symbol: str, name: str) -> str:
    if symbol in QUASI_BROAD_CODES or any(key in name for key in ["创业", "科创"]):
        return "quasi_broad_base"
    return "traditional_broad_base"


def _data_quality(signal: dict, buy: dict, latest: dict) -> str:
    text = " ".join(str(item or "") for item in [signal.get("block_reasons"), buy.get("risk_note"), latest.get("block_reasons")])
    if not text or text in {"无", "nan"}:
        return "ok"
    if any(key in text for key in ["缺少", "异常", "提醒", "过远", "追高"]):
        return "caution"
    return "ok"


def _summary_text(flags: list[str], rows: list[dict]) -> str:
    parts = []
    if "BROAD_BASE_MISSING" in flags:
        parts.append("当前正式模拟仓宽基占比为 0，缺少宽基平衡层。")
    elif "BROAD_BASE_LIGHT" in flags:
        parts.append("当前宽基占比偏低。")
    if "THEME_CONCENTRATED" in flags:
        parts.append("当前持仓主要集中在科技成长与金融地产，主题集中度偏高。")
    if rows:
        top = "、".join(f"{row['symbol']} {row['name']}" for row in rows[:3])
        parts.append(f"当前优先观察候选：{top}。")
    return "".join(parts) or "当前组合宽基平衡状态正常。"


def _first_number(*values: object) -> float:
    for value in values:
        number = _float(value, None)
        if number is not None:
            return number
    return 0.0


def _maybe_int(value: object) -> int | str:
    number = _float(value, None)
    return int(number) if number is not None and number == int(number) else ""


def _float(value: object, default: float | None = 0.0) -> float:
    try:
        if value is None or value == "":
            raise ValueError
        number = float(value)
        if pd.isna(number):
            raise ValueError
        return number
    except Exception:
        if default is None:
            return None  # type: ignore[return-value]
        return default


def _round(value: object, digits: int = 6) -> float:
    return round(_float(value), digits)


def _fmt(value: object) -> str:
    number = _float(value, None)
    if number is None:
        return "N/A"
    return f"{number:.4f}".rstrip("0").rstrip(".")


def _pct(value: object) -> str:
    number = _float(value)
    return f"{number:.2%}"


def _money(value: object) -> str:
    return f"{_float(value):.2f}"


if __name__ == "__main__":
    main()
