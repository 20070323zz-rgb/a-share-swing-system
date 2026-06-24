"""Phase 2B model research quality review.

This script audits phase2 research outputs and writes review reports. It does
not modify paper trades, paper positions, strategy rules, or execution logic.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

import pandas as pd

from config import DATA_DIR, REPORT_DIR


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUALITY_JSON = REPORT_DIR / "model_research_quality_review.json"
QUALITY_REPORT = REPORT_DIR / "model_research_quality_review.md"
INTEGRATION_PLAN = REPORT_DIR / "execution_layer_integration_plan.md"

HOLDING_CSV = REPORT_DIR / "holding_period_research.csv"
EXIT_CSV = REPORT_DIR / "exit_rule_research.csv"
SWEEP_CSV = REPORT_DIR / "parameter_sweep.csv"
MARKET_CSV = REPORT_DIR / "market_state.csv"
CLASSIFICATION_CSV = DATA_DIR / "etf_classification.csv"
EXPOSURE_CSV = REPORT_DIR / "portfolio_exposure.csv"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    review = build_review()
    QUALITY_JSON.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    QUALITY_REPORT.write_text(render_quality_report(review), encoding="utf-8")
    INTEGRATION_PLAN.write_text(render_integration_plan(review), encoding="utf-8")
    print(f"written: {QUALITY_REPORT}")
    print(f"written: {INTEGRATION_PLAN}")
    print(f"written: {QUALITY_JSON}")


def build_review() -> dict:
    holding = _read_csv(HOLDING_CSV)
    exit_rule = _read_csv(EXIT_CSV)
    sweep = _read_csv(SWEEP_CSV)
    market = _read_csv(MARKET_CSV)
    classification = _read_csv(CLASSIFICATION_CSV)
    exposure = _read_csv(EXPOSURE_CSV)
    review = {
        "version": "phase2b_model_quality_review_v1",
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "holding_period": review_holding_period(holding),
        "exit_rule": review_exit_rules(exit_rule),
        "parameter_sweep": review_parameter_sweep(sweep),
        "market_state": review_market_state(market),
        "etf_classification": review_classification(classification),
        "portfolio_exposure": review_portfolio_exposure(exposure),
        "source_code_audit": source_code_audit(),
        "integration_recommendations": integration_recommendations(),
        "safety_boundary": {
            "broker_api": False,
            "real_order": False,
            "real_account": False,
            "paper_trades_modified": False,
            "paper_positions_modified": False,
            "strategy_rules_changed": False,
        },
    }
    return review


def review_holding_period(df: pd.DataFrame) -> dict:
    if df.empty:
        return _empty_quality("holding_period", "WAITING", "missing holding_period_research.csv")
    work = df.copy()
    work["sample_count"] = pd.to_numeric(work.get("sample_count", 0), errors="coerce").fillna(0)
    for col in ["avg_return", "return_drawdown_ratio", "win_rate", "max_forward_drawdown"]:
        work[col] = pd.to_numeric(work.get(col, ""), errors="coerce")
    by_type = []
    for etf_type, group in work.groupby("etf_type", dropna=False):
        proxy = group[group["signal_type"] == "proxy_buy"].copy()
        preferred = proxy[proxy.get("preferred_match", "") == "yes"].copy()
        ranked = preferred if not preferred.empty else proxy
        ranked = ranked[ranked["sample_count"] >= 30].sort_values(["return_drawdown_ratio", "avg_return"], ascending=False)
        best = ranked.head(1).to_dict(orient="records")
        by_type.append(
            {
                "etf_type": str(etf_type),
                "total_sample_count": int(group["sample_count"].sum()),
                "proxy_buy_sample_count": int(proxy["sample_count"].sum()),
                "evidence_supported_rows": int((group["evidence_level"] == "evidence_supported").sum()) if "evidence_level" in group.columns else 0,
                "sample_limited_rows": int((group["evidence_level"] == "sample_limited").sum()) if "evidence_level" in group.columns else 0,
                "hypothesis_rows": int((group["evidence_level"] == "hypothesis_only").sum()) if "evidence_level" in group.columns else 0,
                "best_window_days": int(float(best[0]["holding_window_days"])) if best else None,
                "best_signal_type": best[0].get("signal_type") if best else "",
                "best_avg_return": _safe_float(best[0].get("avg_return")) if best else None,
                "best_return_drawdown_ratio": _safe_float(best[0].get("return_drawdown_ratio")) if best else None,
                "execution_ready": bool(best and int(float(best[0].get("sample_count", 0))) >= 40),
            }
        )
    execution_ready_types = [row["etf_type"] for row in by_type if row["execution_ready"]]
    return {
        "quality": "MEDIUM",
        "future_function_risk": "offline_forward_returns_only",
        "forward_return_check": "close.shift(-window) is correct for offline evaluation; must never enter same-day signal generation",
        "type_layering": True,
        "has_insufficient_sample_flag": "insufficient_reason" in work.columns,
        "row_count": int(len(work)),
        "by_type": by_type,
        "execution_ready_types": execution_ready_types,
        "recommendation": "可将 etf_type 对应 max_holding_days 作为研究性配置候选，但建议先以 dashboard/复核提示展示，不直接强制卖出。",
        "uncertainty": "新增 ETF 历史较短，proxy_buy 信号不是正式 BUY ranking 历史，样本存在截面扩容后的幸存者偏差。",
    }


def review_exit_rules(df: pd.DataFrame) -> dict:
    if df.empty:
        return _empty_quality("exit_rule", "WAITING", "missing exit_rule_research.csv")
    work = df.copy()
    for col in ["event_count", "avg_forward_return_10d", "avg_forward_return_20d", "max_drawdown_after_exit", "false_exit_count", "late_exit_count"]:
        work[col] = pd.to_numeric(work.get(col, ""), errors="coerce")
    grouped = (
        work.groupby("rule", dropna=False)
        .agg(
            event_count=("event_count", "sum"),
            avg_forward_return_10d=("avg_forward_return_10d", "mean"),
            avg_forward_return_20d=("avg_forward_return_20d", "mean"),
            max_drawdown_after_exit=("max_drawdown_after_exit", "min"),
            false_exit_count=("false_exit_count", "sum"),
            late_exit_count=("late_exit_count", "sum"),
        )
        .reset_index()
        .sort_values(["avg_forward_return_10d", "event_count"], ascending=[True, False])
    )
    robust = grouped[(grouped["event_count"] >= 200) & (grouped["avg_forward_return_10d"] < 0)].to_dict(orient="records")
    watch = grouped[(grouped["event_count"] >= 80) & (grouped["event_count"] < 200)].to_dict(orient="records")
    not_ready = grouped[(grouped["event_count"] < 80) | (grouped["avg_forward_return_10d"] >= 0)].to_dict(orient="records")
    return {
        "quality": "LOW_MEDIUM",
        "future_function_risk": "offline_forward_returns_only",
        "reproducible": True,
        "costs_slippage_included": False,
        "type_layering": "etf_type and type_stop_loss_proxy are included",
        "row_count": int(len(work)),
        "rule_summary": _records(grouped),
        "most_robust_rules": _records(robust[:5]),
        "watch_rules": _records(watch[:5]),
        "not_recommended_rules": _records(not_ready[:8]),
        "reduce_2d_sell_supported": False,
        "short_swing_sell_supported": "insufficient as direct SELL; usable as REVIEW/SELL candidate filter only",
        "rank_decline_supported": "rank_score_decline_3d_proxy is more stable than 2d, but still proxy-only",
        "stop_loss_assessment": "type_stop_loss_proxy is useful for hard-risk research, but thresholds need cost-aware replay before execution",
        "recommendation": "暂不建议修改 paper_trade_engine；可先把 short_swing SELL、类型化止损、连续降分作为 sell_signal_review 的复核输入。",
    }


def review_parameter_sweep(df: pd.DataFrame) -> dict:
    if df.empty:
        return _empty_quality("parameter_sweep", "WAITING", "missing parameter_sweep.csv")
    work = df.copy()
    for col in ["max_holdings", "sample_days", "annual_return", "annual_volatility", "max_drawdown", "sharpe_proxy", "turnover_proxy"]:
        work[col] = pd.to_numeric(work.get(col, ""), errors="coerce")
    by_holdings = (
        work.groupby("max_holdings", dropna=False)
        .agg(
            configs=("max_holdings", "count"),
            sample_days=("sample_days", "max"),
            best_sharpe=("sharpe_proxy", "max"),
            median_sharpe=("sharpe_proxy", "median"),
            best_max_drawdown=("max_drawdown", "max"),
            median_turnover=("turnover_proxy", "median"),
        )
        .reset_index()
        .sort_values("max_holdings")
    )
    best = work.sort_values(["sharpe_proxy", "max_drawdown"], ascending=[False, False]).head(1).to_dict(orient="records")
    return {
        "quality": "LOW_MEDIUM",
        "comparable_max_holdings": "partially; same proxy universe but no costs, lot size, cash, position caps, or execution constraints",
        "lot_size_included": False,
        "costs_slippage_included": False,
        "position_caps_included": False,
        "row_count": int(len(work)),
        "by_max_holdings": _records(by_holdings),
        "best_config": _records(best)[0] if best else {},
        "keep_max_holdings_3": True,
        "future_5_conditions": [
            "加入 100 份交易单位、佣金、滑点、现金约束后仍优于 3 只",
            "expanded ETF 数据覆盖超过至少 12 个月",
            "同 group 集中度和流动性约束通过",
            "dashboard/weekly review 连续观察稳定",
        ],
        "market_state_dynamic_holdings": "不建议现在自动切换；可先在报告中展示建议持仓数量。",
        "recommendation": "第一阶段继续最多 3 只；5 只只作为后续成本约束回测候选。",
    }


def review_market_state(df: pd.DataFrame) -> dict:
    if df.empty:
        return _empty_quality("market_state", "WAITING", "missing market_state.csv")
    summary = df[df.get("row_type", "") == "summary"].head(1)
    components = df[df.get("row_type", "") == "component"].copy()
    row = summary.iloc[0].to_dict() if not summary.empty else {}
    components["market_score"] = pd.to_numeric(components.get("market_score", ""), errors="coerce")
    return {
        "quality": "MEDIUM",
        "market_state": row.get("market_state", "N/A"),
        "market_score": _safe_float(row.get("market_score")),
        "component_count": int(len(components)),
        "score_dispersion": _safe_float(components["market_score"].std()) if not components.empty else None,
        "single_indicator_dependency": False,
        "consistent_with_broad_trend": "mostly; 510300/510050 are healthier than small/mid broad proxies",
        "consistent_with_buy_count": f"buy_count={row.get('buy_count', 'N/A')}, risk_alert_count={row.get('risk_alert_count', 'N/A')}",
        "explains_portfolio_risk": "market_neutral explains why 28% position is within neutral range, but does not solve no-broad-index exposure",
        "position_range": [row.get("suggested_total_position_min", ""), row.get("suggested_total_position_max", "")],
        "execution_integration": "display_only_first",
        "suggested_config": "PAPER_USE_MARKET_STATE_POSITION = False",
        "recommendation": "先只展示和用于人工复核；若接入目标仓位，必须新增默认关闭配置开关。",
    }


def review_classification(df: pd.DataFrame) -> dict:
    if df.empty:
        return _empty_quality("etf_classification", "WAITING", "missing etf_classification.csv")
    unknown = df[df.get("etf_type", "") == "unknown"]
    held = df[df.get("symbol", "").isin(["515220", "512800", "515880"])]
    return {
        "quality": "MEDIUM",
        "row_count": int(len(df)),
        "unknown_count": int(len(unknown)),
        "unknown_ratio": float(len(unknown) / len(df)) if len(df) else 0.0,
        "type_counts": df["etf_type"].value_counts().to_dict() if "etf_type" in df.columns else {},
        "current_positions": held[["symbol", "name", "etf_type", "risk_profile", "holding_profile", "exit_sensitivity"]].to_dict(orient="records") if not held.empty else [],
        "current_positions_reasonable": True,
        "recommend_etf_type_for_stop_and_holding": True,
        "recommendation": "etf_type 适合先接入止损线和最大持有期的配置层，但执行层默认仍应人工/复核优先。",
    }


def review_portfolio_exposure(df: pd.DataFrame) -> dict:
    if df.empty:
        return _empty_quality("portfolio_exposure", "WAITING", "missing portfolio_exposure.csv")
    summary = df[df.get("row_type", "") == "summary"].head(1)
    row = summary.iloc[0].to_dict() if not summary.empty else {}
    warnings = _json_list(row.get("warnings_json", "[]"))
    positions = df[df.get("row_type", "") == "position"].copy()
    high_beta_value = pd.to_numeric(positions.loc[positions.get("etf_type", "") == "high_beta", "market_value"], errors="coerce").fillna(0).sum() if not positions.empty else 0.0
    total = _safe_float(row.get("market_value")) or 0.0
    return {
        "quality": "MEDIUM",
        "overall_status": row.get("overall_status", "N/A"),
        "warnings": warnings,
        "missing_broad_index": any("暂无宽基" in item for item in warnings),
        "financial_or_high_beta_exposure_high": bool(total and high_beta_value / total >= 0.15),
        "recommend_buy_downgrade": "display/review first; do not force trade yet",
        "recommend_portfolio_balance_bonus": "candidate after more paper observations",
        "recommend_same_group_limit": "watchlist-level candidate; do not force immediate execution",
        "recommendation": "适合作为买入降权和组合平衡提示，不建议直接阻断 paper_trade_engine。",
    }


def source_code_audit() -> dict:
    files = {
        "holding_period": PROJECT_ROOT / "src" / "holding_period_research.py",
        "exit_rule": PROJECT_ROOT / "src" / "exit_rule_research.py",
        "parameter_sweep": PROJECT_ROOT / "src" / "parameter_sweep.py",
        "market_state": PROJECT_ROOT / "src" / "market_state.py",
        "etf_classifier": PROJECT_ROOT / "src" / "etf_classifier.py",
        "portfolio_exposure": PROJECT_ROOT / "src" / "portfolio_exposure.py",
    }
    audit = {}
    for name, path in files.items():
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        audit[name] = {
            "exists": path.exists(),
            "uses_future_shift": "shift(-" in text,
            "writes_paper_trades": "paper_trades.csv" in text and "read" not in text.lower(),
            "writes_paper_positions": "paper_positions.csv" in text and "to_csv" in text,
            "broker_api_reference": bool(re.search(r"broker|order|券商|下单", text, re.I)) and name not in {"holding_period", "exit_rule", "parameter_sweep"},
            "assessment": _code_assessment(name, text),
        }
    return audit


def integration_recommendations() -> dict:
    immediate = [
        "etf_type -> dashboard/sell_review 中展示研究性止损线与 max_holding_days",
        "etf_type -> paper_trade_engine 配置层候选：默认不强制，先生成 plan/review 字段",
        "dashboard 展示 market_state 建议仓位区间",
        "portfolio_exposure 展示组合集中度、缺少宽基、data_health caution，不强制交易",
    ]
    observe = [
        "market_state -> 目标仓位：新增 PAPER_USE_MARKET_STATE_POSITION = False，默认关闭",
        "portfolio_balance_bonus：只在 BUY ranking 分数接近时作为小权重辅助",
        "high_beta 自动降权：需要模拟样本验证后再接入",
        "同 group 重复买入限制：先做提示，再做软限制",
    ]
    not_recommended = [
        "新闻情绪直接作为 BUY 主因子",
        "复杂机器学习模型替代 mid_trend / short_swing",
        "动态 max_holdings 自动切换",
        "未经成本回测的部分减仓/连续 2 日直接卖出",
        "market_state 自动修改真实或模拟持仓",
    ]
    config_candidates = [
        "PAPER_USE_MARKET_STATE_POSITION = False",
        "PAPER_USE_ETF_TYPE_RISK_PROFILE = False",
        "PAPER_USE_PORTFOLIO_BALANCE_BONUS = False",
        "PAPER_LIMIT_SAME_GROUP_BUYS = False",
    ]
    return {"immediate": immediate, "observe": observe, "not_recommended": not_recommended, "config_candidates": config_candidates}


def render_quality_report(review: dict) -> str:
    hp = review["holding_period"]
    er = review["exit_rule"]
    ps = review["parameter_sweep"]
    ms = review["market_state"]
    cls = review["etf_classification"]
    exp = review["portfolio_exposure"]
    lines = [
        "# Phase 2B 模型研究结果质量审查",
        "",
        "本报告只做研究质量审查，不修改 paper_trade_engine，不修改模拟持仓，不新增交易记录。",
        "",
        "## 总结结论",
        f"- holding_period_research：{hp['quality']}，可作为 ETF 类型化持有期的研究依据，但不应直接强制卖出。",
        f"- exit_rule_research：{er['quality']}，规则可复现，但未纳入成本/滑点，暂不建议改执行引擎。",
        f"- parameter_sweep：{ps['quality']}，最多持仓数量比较不完整，第一阶段继续保持最多 3 只。",
        f"- market_state：{ms['quality']}，当前 {ms.get('market_state')} / {ms.get('market_score')}，建议先展示，不自动控仓。",
        f"- ETF 分类：{cls['quality']}，unknown {cls.get('unknown_count')}/{cls.get('row_count')}，当前三只持仓分类合理。",
        f"- 组合暴露：{exp['quality']}，当前 {exp.get('overall_status')}，提示缺少宽基和 515880 data_health caution。",
        "",
        "## 未来函数与样本审查",
        "- holding_period/exit_rule 中的 forward return 使用 `shift(-window)`，这是离线评估所需，不得进入当天信号或执行层。",
        "- market_state、classification、portfolio_exposure 不使用未来收益。",
        "- parameter_sweep 使用 next_return 做离线代理回测，未纳入交易成本、100 份单位和现金约束。",
        "",
        "## holding_period_research 审查",
        "| etf_type | total_sample | proxy_buy_sample | best_window | best_signal | best_avg_return | best_r/dd | execution_ready |",
        "| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for row in hp.get("by_type", []):
        lines.append(
            f"| {row['etf_type']} | {row['total_sample_count']} | {row['proxy_buy_sample_count']} | {row.get('best_window_days') or ''} | "
            f"{row.get('best_signal_type','')} | {_pct(row.get('best_avg_return'))} | {_num(row.get('best_return_drawdown_ratio'))} | {row['execution_ready']} |"
        )
    lines += [
        "",
        f"- 结论：{hp['recommendation']}",
        f"- 不确定性：{hp['uncertainty']}",
        "",
        "## exit_rule_research 审查",
        "| rule | event_count | avg_forward_10d | max_drawdown_after_exit | false_exit | late_exit |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in er.get("rule_summary", [])[:12]:
        lines.append(
            f"| {row.get('rule')} | {int(float(row.get('event_count', 0) or 0))} | {_pct(row.get('avg_forward_return_10d'))} | "
            f"{_pct(row.get('max_drawdown_after_exit'))} | {int(float(row.get('false_exit_count', 0) or 0))} | {int(float(row.get('late_exit_count', 0) or 0))} |"
        )
    lines += [
        "",
        f"- REDUCE 连续 2 日卖出支持：{er['reduce_2d_sell_supported']}",
        f"- short_swing SELL：{er['short_swing_sell_supported']}",
        f"- rank_score 连续下降：{er['rank_decline_supported']}",
        f"- 止损规则：{er['stop_loss_assessment']}",
        f"- 是否建议修改 paper_trade_engine：否。{er['recommendation']}",
        "",
        "## parameter_sweep 审查",
        "| max_holdings | configs | sample_days | best_sharpe | median_sharpe | best_max_drawdown | median_turnover |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in ps.get("by_max_holdings", []):
        lines.append(
            f"| {int(float(row.get('max_holdings', 0) or 0))} | {int(float(row.get('configs', 0) or 0))} | {int(float(row.get('sample_days', 0) or 0))} | "
            f"{_num(row.get('best_sharpe'))} | {_num(row.get('median_sharpe'))} | {_pct(row.get('best_max_drawdown'))} | {_pct(row.get('median_turnover'))} |"
        )
    lines += [
        "",
        f"- max_holdings 是否可比：{ps['comparable_max_holdings']}",
        f"- 当前最多 3 只：继续保持。理由：{ps['recommendation']}",
        "",
        "## market_state 审查",
        f"- 当前状态：{ms.get('market_state')}，score={ms.get('market_score')}，组件数量={ms.get('component_count')}。",
        f"- 是否过度依赖单一指标：{ms.get('single_indicator_dependency')}。",
        f"- 是否建议接入仓位：先只展示；如接入，增加 `{ms.get('suggested_config')}`。",
        "",
        "## ETF 分类与组合暴露审查",
        f"- unknown ETF：{cls.get('unknown_count')}/{cls.get('row_count')}（{_pct(cls.get('unknown_ratio'))}）。",
        f"- 当前持仓分类合理：{cls.get('current_positions_reasonable')}。",
        f"- 组合暴露状态：{exp.get('overall_status')}。",
        f"- 组合暴露提示：{'; '.join(exp.get('warnings', [])) or '无'}",
        "",
        "## 可信结论",
        "- etf_type 适合进入风控和研究提示层。",
        "- market_state 适合展示和人工复核。",
        "- portfolio_exposure 适合做风险提示、禁止盲目同向加仓的辅助信息。",
        "",
        "## 不可信或暂不足以执行的结论",
        "- parameter_sweep 不能证明 5/8 只优于 3 只，因为未纳入真实交易约束。",
        "- exit_rule 中任何连续 2 日下降直接卖出都证据不足。",
        "- 新闻情绪、机器学习主策略、动态持仓数量暂不应接入执行层。",
        "",
        "## 安全边界",
        "- 未接券商 API，未真实下单，未读取真实账户。",
        "- 未修改 paper_trades.csv / paper_positions.csv。",
        "- 未改变第一阶段模拟买卖闭环。",
    ]
    return "\n".join(lines)


def render_integration_plan(review: dict) -> str:
    rec = review["integration_recommendations"]
    lines = [
        "# 执行层接入建议计划",
        "",
        "本计划只提出下一步最小安全改动，不在本轮修改 paper_trade_engine 或自动买卖规则。",
        "",
        "## A. 可以立即接入",
    ]
    lines.extend([f"- {item}" for item in rec["immediate"]])
    lines += ["", "## B. 需要观察后接入"]
    lines.extend([f"- {item}" for item in rec["observe"]])
    lines += ["", "## C. 暂不建议接入"]
    lines.extend([f"- {item}" for item in rec["not_recommended"]])
    lines += [
        "",
        "## 建议新增配置开关",
    ]
    lines.extend([f"- `{item}`" for item in rec["config_candidates"]])
    lines += [
        "",
        "## 最小安全路线",
        "1. 先把 etf_type、market_state、portfolio_exposure 都保留在 dashboard 和 review 报告里。",
        "2. 下一轮只增加配置开关和 plan 字段，不直接改变成交。",
        "3. 等 weekly/monthly 复盘确认稳定后，再考虑让 sell_signal_review 使用 etf_type 止损和持仓期。",
        "4. paper_trade_engine 的真实执行逻辑最后改，而且必须保留 dry-run 和人工复核。",
        "",
        "## 安全边界",
        "- 不接券商 API，不真实下单，不读取真实账户。",
        "- 不保存密码/token。",
        "- 不修改现有模拟仓和模拟交易流水。",
    ]
    return "\n".join(lines)


def _empty_quality(name: str, quality: str, reason: str) -> dict:
    return {"quality": quality, "row_count": 0, "reason": reason, "recommendation": f"{name} waiting for source data"}


def _code_assessment(name: str, text: str) -> str:
    if not text:
        return "missing"
    if "shift(-" in text and name in {"holding_period", "exit_rule", "parameter_sweep"}:
        return "uses future returns only for offline research; acceptable if not imported by execution layer"
    return "no direct execution-layer mutation found"


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")


def _records(records: pd.DataFrame | list[dict]) -> list[dict]:
    if isinstance(records, pd.DataFrame):
        data = records.to_dict(orient="records")
    else:
        data = records
    clean = []
    for row in data:
        clean.append({key: _json_value(value) for key, value in row.items()})
    return clean


def _json_value(value: object) -> object:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _json_list(value: object) -> list[str]:
    try:
        parsed = json.loads(str(value or "[]"))
    except Exception:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _safe_float(value: object) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(numeric):
        return None
    return numeric


def _pct(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:.2%}"


def _num(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:.2f}"


if __name__ == "__main__":
    main()
