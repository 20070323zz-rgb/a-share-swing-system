"""Strategy enhancement preview layer.

This module only writes research preview reports. It does not alter the real
paper-trading ranking, does not execute trades, and does not modify
paper_trades.csv or paper_positions.csv.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

import pandas as pd

from config import BROKER_API_ENABLED, DATA_DIR, PAPER_POSITIONS_FILE, PAPER_USE_MARKET_STATE_POSITION, REAL_TRADE_ENABLED, REPORT_DIR


BUY_RANKING_FILE = REPORT_DIR / "buy_signal_ranking.md"
DATA_HEALTH_FILE = REPORT_DIR / "latest_data_health.md"
CLASSIFICATION_FILE = DATA_DIR / "etf_classification.csv"
LEGACY_CLASSIFICATION_FILE = DATA_DIR / "etf_type_classification.csv"
MARKET_STATE_FILE = REPORT_DIR / "market_state.csv"
PORTFOLIO_EXPOSURE_FILE = REPORT_DIR / "portfolio_exposure.csv"
QUALITY_REVIEW_FILE = REPORT_DIR / "model_research_quality_review.json"
PREVIEW_CSV_FILE = REPORT_DIR / "strategy_enhancement_preview.csv"
PREVIEW_MD_FILE = REPORT_DIR / "strategy_enhancement_preview.md"
B1_REPORT_FILE = REPORT_DIR / "b1_strategy_enhancement_preview_report.md"
PAPER_PLAN_CSV_FILE = REPORT_DIR / "paper_trade_plan.csv"
PAPER_PLAN_MD_FILE = REPORT_DIR / "paper_trade_plan.md"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ranking = _read_buy_ranking()
    classification = _read_classification()
    health = _read_data_health()
    positions = _read_csv(PAPER_POSITIONS_FILE)
    market = _read_market_state()
    exposure = _read_portfolio_exposure()
    quality = _read_quality_review()

    rows = _build_preview_rows(ranking, classification, health, positions, market, exposure, quality)
    preview = pd.DataFrame(rows)
    if not preview.empty:
        preview = preview.sort_values(
            ["adjusted_rank_score_preview", "original_rank_score"],
            ascending=[False, False],
        ).reset_index(drop=True)
        preview["adjusted_rank_preview"] = range(1, len(preview) + 1)
        original_top3 = _top_symbols(preview.sort_values("original_rank", ascending=True), "symbol", 3)
        adjusted_top3 = _top_symbols(preview, "symbol", 3)
        preview["would_change_top3"] = preview["symbol"].apply(
            lambda item: "yes" if (item in set(original_top3) or item in set(adjusted_top3)) and original_top3 != adjusted_top3 else "no"
        )
    else:
        original_top3 = []
        adjusted_top3 = []

    preview.to_csv(PREVIEW_CSV_FILE, index=False)
    summary = _summary_payload(preview, original_top3, adjusted_top3, market, exposure)
    _write_preview_report(preview, summary)
    _write_b1_report(preview, summary)
    _update_paper_trade_plan(preview, summary)
    print(f"已生成策略增强预览报告：{PREVIEW_MD_FILE}")
    print(f"已生成策略增强预览 CSV：{PREVIEW_CSV_FILE}")


def _build_preview_rows(
    ranking: list[dict],
    classification: pd.DataFrame,
    health: dict[str, dict],
    positions: pd.DataFrame,
    market: dict,
    exposure: dict,
    quality: dict,
) -> list[dict]:
    held_groups = _held_groups(positions, classification)
    held_types = _held_types(positions, classification)
    portfolio_missing_broad = "broad_index" not in held_types or _has_warning(exposure, "宽基")
    portfolio_missing_defensive = not (held_types & {"bond_cash", "defensive"})
    current_high_beta = "high_beta" in held_types
    market_state = str(market.get("market_state", "N/A"))
    exposure_status = str(exposure.get("overall_status", "N/A"))
    research_confidence = _research_confidence(quality)

    rows: list[dict] = []
    for item in ranking:
        symbol = str(item.get("symbol", "")).strip()
        name = str(item.get("name", symbol)).strip()
        class_row = _classification_for(symbol, name, classification)
        etf_type = _effective_type(str(class_row.get("etf_type") or ""), name)
        group = str(item.get("group") or class_row.get("group") or "")
        health_row = health.get(symbol, {})
        health_status = str(health_row.get("status", ""))
        risk_note = str(item.get("risk_note", ""))
        original_score = _float(item.get("rank_score"))

        broad_bonus = 3.0 if portfolio_missing_broad and etf_type == "broad_index" else 0.0
        defensive_bonus = 1.5 if portfolio_missing_defensive and market_state != "market_strong" and _is_defensive(etf_type, group, name, class_row) else 0.0
        same_group_penalty = -2.0 if group and group in held_groups else 0.0
        high_beta_penalty = -2.0 if current_high_beta and etf_type == "high_beta" else 0.0
        data_health_penalty = _data_health_penalty(health_status)
        qdii_penalty = -999.0 if etf_type == "qdii" else 0.0
        liquidity_penalty = _liquidity_penalty(item, risk_note)
        adjusted = original_score + broad_bonus + defensive_bonus + same_group_penalty + high_beta_penalty + data_health_penalty + qdii_penalty + liquidity_penalty
        reasons = _enhancement_reasons(
            broad_bonus,
            defensive_bonus,
            same_group_penalty,
            high_beta_penalty,
            data_health_penalty,
            qdii_penalty,
            liquidity_penalty,
            etf_type,
            group,
            health_status,
        )
        status = "market_risk_off_preview_only" if market_state == "market_risk_off" else "preview_only_not_executed"
        if data_health_penalty <= -999 or qdii_penalty <= -999:
            status = "preview_blocked_not_executed"
        rows.append(
            {
                "date": _latest_date(),
                "symbol": symbol,
                "name": name,
                "original_rank": int(_float(item.get("rank"), 0)),
                "original_rank_score": round(original_score, 6),
                "adjusted_rank_score_preview": round(adjusted, 6),
                "adjusted_rank_preview": "",
                "score_delta": round(adjusted - original_score, 6),
                "etf_type": etf_type,
                "group": group,
                "market_state": market_state,
                "portfolio_exposure_status": exposure_status,
                "broad_index_balance_bonus": broad_bonus,
                "defensive_balance_bonus": defensive_bonus,
                "same_group_concentration_penalty": same_group_penalty,
                "high_beta_penalty": high_beta_penalty,
                "data_health_penalty": data_health_penalty,
                "qdii_auto_buy_penalty": qdii_penalty,
                "liquidity_penalty": liquidity_penalty,
                "research_confidence": research_confidence,
                "enhancement_reason": "; ".join(reasons) if reasons else "no_preview_adjustment",
                "would_change_top3": "no",
                "execution_status": status,
            }
        )
    return rows


def _summary_payload(preview: pd.DataFrame, original_top3: list[str], adjusted_top3: list[str], market: dict, exposure: dict) -> dict:
    if preview.empty:
        rows = []
    else:
        rows = preview.to_dict(orient="records")
    top3_changed = original_top3 != adjusted_top3
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": _latest_date(),
        "market_state": market.get("market_state", "N/A"),
        "market_score": market.get("market_score", "N/A"),
        "portfolio_exposure_status": exposure.get("overall_status", "N/A"),
        "original_top3": _rows_for_symbols(rows, original_top3),
        "adjusted_top3": rows[:3],
        "top3_changed": top3_changed,
        "score_delta_largest": _largest_abs_delta(rows),
        "broad_index_bonus_hits": [row for row in rows if _float(row.get("broad_index_balance_bonus")) > 0],
        "defensive_bonus_hits": [row for row in rows if _float(row.get("defensive_balance_bonus")) > 0],
        "high_beta_penalty_hits": [row for row in rows if _float(row.get("high_beta_penalty")) < 0],
        "same_group_penalty_hits": [row for row in rows if _float(row.get("same_group_concentration_penalty")) < 0],
        "data_health_penalty_hits": [row for row in rows if _float(row.get("data_health_penalty")) < 0],
        "execution_safety": {
            "adjusted_rank_score_preview_enabled": True,
            "adjusted_rank_score_execution_enabled": False,
            "paper_use_market_state_position": bool(PAPER_USE_MARKET_STATE_POSITION),
            "real_trade_enabled": bool(REAL_TRADE_ENABLED),
            "broker_api_enabled": bool(BROKER_API_ENABLED),
        },
        "execution_note": "Preview only. adjusted_rank_score_preview is not used by paper_trade_engine.",
    }


def _write_preview_report(df: pd.DataFrame, summary: dict) -> None:
    lines = [
        f"# 策略增强预览报告 {summary['generated_at']}",
        "",
        "本报告只计算 adjusted_rank_score_preview，不改变 BUY ranking、不改变 paper_trade_engine 真实排序、不写模拟交易。",
        "",
        "## 摘要",
        f"- market_state：{summary.get('market_state')} / market_score={summary.get('market_score')}",
        f"- portfolio_exposure_status：{summary.get('portfolio_exposure_status')}",
        f"- Top 3 是否变化：{'是' if summary.get('top3_changed') else '否'}",
        "- adjusted_rank_score_execution_enabled：false",
        "- PAPER_USE_MARKET_STATE_POSITION：false",
        "",
        "## Original Top 3",
    ]
    lines.extend(_ordered_list(summary.get("original_top3", []), score_key="original_rank_score", rank_key="original_rank"))
    lines += ["", "## Adjusted Preview Top 3"]
    lines.extend(_ordered_list(summary.get("adjusted_top3", []), score_key="adjusted_rank_score_preview", rank_key="adjusted_rank_preview"))
    lines += [
        "",
        "## Top 3 差异",
        "- 本轮差异：" + ("原始 Top 3 与增强预览 Top 3 不一致。" if summary.get("top3_changed") else "原始 Top 3 与增强预览 Top 3 一致。"),
    ]
    largest = summary.get("score_delta_largest") or {}
    if largest:
        lines.append(f"- 最大分数变化：{largest.get('symbol')} {largest.get('name')}，delta={_fmt(largest.get('score_delta'))}，原因：{largest.get('enhancement_reason')}")
    lines += [
        "",
        "## 组合平衡 bonus 命中",
        *_bullet_rows(summary.get("broad_index_bonus_hits", []), "broad_index_balance_bonus"),
        *_bullet_rows(summary.get("defensive_bonus_hits", []), "defensive_balance_bonus"),
        "",
        "## 降权命中",
        *_bullet_rows(summary.get("same_group_penalty_hits", []), "same_group_concentration_penalty"),
        *_bullet_rows(summary.get("high_beta_penalty_hits", []), "high_beta_penalty"),
        *_bullet_rows(summary.get("data_health_penalty_hits", []), "data_health_penalty"),
        "",
        "## 全部预览明细",
        "| original_rank | adjusted_rank | symbol | name | etf_type | group | original_score | adjusted_score | delta | bonus/penalty reason | execution_status |",
        "| ---: | ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['original_rank']} | {row['adjusted_rank_preview']} | {row['symbol']} | {row['name']} | {row['etf_type']} | {row['group']} | "
            f"{_fmt(row['original_rank_score'])} | {_fmt(row['adjusted_rank_score_preview'])} | {_fmt(row['score_delta'])} | "
            f"{str(row['enhancement_reason']).replace('|', '/')} | {row['execution_status']} |"
        )
    lines += _safety_lines()
    PREVIEW_MD_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_b1_report(df: pd.DataFrame, summary: dict) -> None:
    lines = [
        "# B1 执行层渐进优化第一版报告",
        "",
        f"- 生成时间：{summary['generated_at']}",
        "- 阶段：B1 strategy_enhancement_preview_v1。",
        "- 目标：预览 market_state、ETF 类型、组合暴露、数据健康对 BUY ranking 和 sell review 的影响。",
        "",
        "## 是否新增 adjusted_rank_score_preview",
        "- 已新增，仅写入 `reports/strategy_enhancement_preview.csv` 和 `reports/strategy_enhancement_preview.md`。",
        "- 不修改原始 BUY ranking。",
        "- 不修改 paper_trade_engine 真实买入排序。",
        "",
        "## Top 3 对照",
        "### Original Top 3",
        *_ordered_list(summary.get("original_top3", []), score_key="original_rank_score", rank_key="original_rank"),
        "",
        "### Adjusted Preview Top 3",
        *_ordered_list(summary.get("adjusted_top3", []), score_key="adjusted_rank_score_preview", rank_key="adjusted_rank_preview"),
        "",
        f"- Top 3 是否变化：{'是' if summary.get('top3_changed') else '否'}。",
        "",
        "## 变化原因",
    ]
    if df.empty:
        lines.append("- 暂无 BUY ranking 可预览。")
    else:
        for _, row in df.sort_values("score_delta", key=lambda s: s.abs(), ascending=False).head(8).iterrows():
            lines.append(f"- {row['symbol']} {row['name']}：delta={_fmt(row['score_delta'])}；{row['enhancement_reason']}")
    lines += [
        "",
        "## 当前是否用于真实模拟买入",
        "- 否。`adjusted_rank_score_execution_enabled = false`。",
        "- paper_trade_engine 仍使用原始规则和原始 BUY ranking。",
        "- 本轮只观察增强分对排序的理论影响，避免未经验证的参数直接进入执行层。",
        "",
        "## 当前持仓类型化 REVIEW",
        "- 详见 `reports/sell_signal_review.md` 与 dashboard 的 Type-aware Review 模块。",
        "",
        "## 是否修改模拟盘文件",
        "- 未修改 `data/paper_trades.csv`。",
        "- 未修改 `data/paper_positions.csv`。",
    ]
    lines += _safety_lines()
    B1_REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _update_paper_trade_plan(preview: pd.DataFrame, summary: dict) -> None:
    if PAPER_PLAN_CSV_FILE.exists() and PAPER_PLAN_CSV_FILE.stat().st_size > 0:
        plan = pd.read_csv(PAPER_PLAN_CSV_FILE, dtype=str, keep_default_na=False).fillna("")
        if not plan.empty and "symbol" in plan.columns:
            preview_map = preview.set_index(preview["symbol"].astype(str)).to_dict(orient="index") if not preview.empty else {}
            for col in [
                "adjusted_rank_score_preview",
                "adjusted_rank_preview",
                "score_delta",
                "enhancement_reason",
                "adjusted_rank_score_execution_enabled",
                "strategy_enhancement_preview_note",
            ]:
                if col not in plan.columns:
                    plan[col] = ""
            for idx, row in plan.iterrows():
                symbol = str(row.get("symbol", ""))
                item = preview_map.get(symbol, {})
                if item:
                    plan.at[idx, "adjusted_rank_score_preview"] = str(item.get("adjusted_rank_score_preview", ""))
                    plan.at[idx, "adjusted_rank_preview"] = str(item.get("adjusted_rank_preview", ""))
                    plan.at[idx, "score_delta"] = str(item.get("score_delta", ""))
                    plan.at[idx, "enhancement_reason"] = str(item.get("enhancement_reason", ""))
                plan.at[idx, "adjusted_rank_score_execution_enabled"] = "false"
                plan.at[idx, "strategy_enhancement_preview_note"] = "preview_only_not_used_for_execution"
            plan.to_csv(PAPER_PLAN_CSV_FILE, index=False)

    if PAPER_PLAN_MD_FILE.exists():
        existing = PAPER_PLAN_MD_FILE.read_text(encoding="utf-8")
        marker = "\n## B1 策略增强预览"
        existing = existing.split(marker)[0].rstrip()
    else:
        existing = "# 模拟交易计划\n"
    lines = [
        existing,
        "",
        "## B1 策略增强预览",
        "",
        "- 本节由 `strategy_enhancement_preview.py` 追加，只作预览，不改变真实模拟交易计划。",
        f"- Top 3 是否变化：{'是' if summary.get('top3_changed') else '否'}。",
        "- adjusted_rank_score_execution_enabled：false。",
        "- PAPER_USE_MARKET_STATE_POSITION：false。",
        "",
        "### Adjusted Preview Top 3",
        *_ordered_list(summary.get("adjusted_top3", []), score_key="adjusted_rank_score_preview", rank_key="adjusted_rank_preview"),
    ]
    PAPER_PLAN_MD_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_buy_ranking() -> list[dict]:
    rows = _read_markdown_table(BUY_RANKING_FILE, "全部 BUY 候选得分拆解") or _read_markdown_table(BUY_RANKING_FILE, "Top BUY Ranking")
    result = []
    for row in rows:
        result.append(
            {
                "rank": int(_float(row.get("rank"), 0)),
                "symbol": row.get("code", ""),
                "name": row.get("name", ""),
                "group": row.get("group", ""),
                "mid_trend_signal": row.get("mid", "N/A"),
                "short_swing_signal": row.get("short", "N/A"),
                "rank_score": _float(row.get("rank_score")),
                "mid_trend_score": _float(row.get("mid_trend")),
                "short_momentum_score": _float(row.get("short_momentum")),
                "liquidity_score": _float(row.get("liquidity")),
                "risk_score": _float(row.get("risk")),
                "resonance_score": _float(row.get("resonance")),
                "data_quality_score": _float(row.get("data_quality")),
                "risk_note": row.get("风险提示", ""),
                "candidate_action": row.get("进入模拟买入候选", ""),
            }
        )
    return [row for row in result if row["symbol"]]


def _read_data_health() -> dict[str, dict]:
    return {
        str(row.get("代码", "")): {"status": row.get("状态", ""), "note": row.get("提醒", ""), "hard_issue": row.get("硬问题", "")}
        for row in _read_markdown_table(DATA_HEALTH_FILE, "明细")
        if row.get("代码")
    }


def _read_classification() -> pd.DataFrame:
    df = _read_csv(CLASSIFICATION_FILE)
    if df.empty:
        df = _read_csv(LEGACY_CLASSIFICATION_FILE)
    if not df.empty and "symbol" not in df.columns and "code" in df.columns:
        df["symbol"] = df["code"]
    if not df.empty and "code" not in df.columns and "symbol" in df.columns:
        df["code"] = df["symbol"]
    return df


def _read_market_state() -> dict:
    df = _read_csv(MARKET_STATE_FILE)
    if df.empty or "row_type" not in df.columns:
        return {}
    summary = df[df["row_type"].astype(str) == "summary"].head(1)
    return summary.iloc[0].to_dict() if not summary.empty else {}


def _read_portfolio_exposure() -> dict:
    df = _read_csv(PORTFOLIO_EXPOSURE_FILE)
    if df.empty or "row_type" not in df.columns:
        return {}
    summary = df[df["row_type"].astype(str) == "summary"].head(1)
    row = summary.iloc[0].to_dict() if not summary.empty else {}
    row["warnings"] = _json_list(row.get("warnings_json", "[]"))
    return row


def _read_quality_review() -> dict:
    if not QUALITY_REVIEW_FILE.exists():
        return {}
    try:
        return json.loads(QUALITY_REVIEW_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_markdown_table(path: Path, section_title: str) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    table: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if table and in_section:
                break
            in_section = section_title in stripped
            continue
        if in_section and stripped.startswith("|"):
            table.append(stripped)
        elif in_section and table:
            break
    if len(table) < 3:
        return []
    headers = [cell.strip() for cell in table[0].strip("|").split("|")]
    rows = []
    for line in table[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


def _classification_for(symbol: str, name: str, classification: pd.DataFrame) -> dict:
    if not classification.empty:
        for col in ["symbol", "code"]:
            if col in classification.columns:
                matched = classification[classification[col].astype(str) == symbol]
                if not matched.empty:
                    return matched.iloc[0].to_dict()
    return {"symbol": symbol, "code": symbol, "name": name, "etf_type": _infer_type(name), "group": ""}


def _held_groups(positions: pd.DataFrame, classification: pd.DataFrame) -> set[str]:
    groups: set[str] = set()
    for item in positions.to_dict(orient="records"):
        symbol = str(item.get("symbol", ""))
        class_row = _classification_for(symbol, str(item.get("name", symbol)), classification)
        group = str(item.get("group") or class_row.get("group") or "")
        if group:
            groups.add(group)
    return groups


def _held_types(positions: pd.DataFrame, classification: pd.DataFrame) -> set[str]:
    types: set[str] = set()
    for item in positions.to_dict(orient="records"):
        symbol = str(item.get("symbol", ""))
        class_row = _classification_for(symbol, str(item.get("name", symbol)), classification)
        etf_type = _effective_type(str(item.get("etf_type") or class_row.get("etf_type") or ""), str(item.get("name", "")))
        if etf_type:
            types.add(etf_type)
    return types


def _infer_type(name: str) -> str:
    if any(key in name for key in ["沪深300", "中证500", "中证1000", "创业板", "科创50", "上证50", "A500"]):
        return "broad_index"
    if any(key in name for key in ["纳指", "恒生", "港股", "标普", "日经", "德国"]):
        return "qdii"
    if any(key in name for key in ["货币", "国债", "短债", "政金债", "债"]):
        return "bond_cash"
    if any(key in name for key in ["证券", "券商", "非银"]):
        return "high_beta"
    if any(key in name for key in ["煤炭", "有色", "黄金", "稀土", "能源", "钢铁"]):
        return "commodity_resource"
    if any(key in name for key in ["机器人", "低空", "AI", "人工智能", "芯片", "半导体", "算力"]):
        return "theme"
    return "sector"


def _effective_type(raw_type: str, name: str) -> str:
    text = str(raw_type or "").strip()
    if text and text.lower() not in {"unknown", "manual_review", "nan", "none"}:
        return text
    return _infer_type(name)


def _is_defensive(etf_type: str, group: str, name: str, class_row: dict) -> bool:
    text = f"{etf_type} {group} {name} {class_row.get('risk_profile','')}"
    return etf_type in {"bond_cash", "defensive"} or any(key in text for key in ["红利", "高股息", "低波", "现金", "债", "low_volatility"])


def _data_health_penalty(status: str) -> float:
    if status == "异常":
        return -999.0
    if status == "提醒":
        return -3.0
    return 0.0


def _liquidity_penalty(item: dict, risk_note: str) -> float:
    liquidity = _float(item.get("liquidity_score"), 0.0)
    if liquidity <= 1.0 or any(key in risk_note for key in ["流动性", "成交额", "成交量过低"]):
        return -3.0
    return 0.0


def _enhancement_reasons(*values: object) -> list[str]:
    (
        broad_bonus,
        defensive_bonus,
        same_group_penalty,
        high_beta_penalty,
        data_health_penalty,
        qdii_penalty,
        liquidity_penalty,
        etf_type,
        group,
        health_status,
    ) = values
    reasons = []
    if _float(broad_bonus) > 0:
        reasons.append("组合缺少宽基，broad_index_balance_bonus +3")
    if _float(defensive_bonus) > 0:
        reasons.append("组合缺少防御资产且市场非 strong，defensive_balance_bonus +1.5")
    if _float(same_group_penalty) < 0:
        reasons.append(f"当前持仓已有 {group} 暴露，same_group_concentration_penalty -2")
    if _float(high_beta_penalty) < 0:
        reasons.append("当前已有 high_beta 暴露，high_beta_penalty -2")
    if _float(data_health_penalty) == -3:
        reasons.append(f"data_health={health_status}，data_health_penalty -3")
    if _float(data_health_penalty) <= -999:
        reasons.append("data_health=异常，preview 层标记不可自动买入")
    if _float(qdii_penalty) <= -999:
        reasons.append("QDII 缺少溢价/汇率/海外日历检查，preview 层标记不可自动买入")
    if _float(liquidity_penalty) < 0:
        reasons.append("流动性 proxy 不足，liquidity_penalty -3")
    if not reasons and etf_type:
        reasons.append("未触发 B1 预览加减分")
    return reasons


def _research_confidence(data: dict) -> str:
    if not data:
        return "research_quality_unavailable"
    return "; ".join(
        [
            f"holding_period={data.get('holding_period', {}).get('quality', 'N/A')}",
            f"exit_rule={data.get('exit_rule', {}).get('quality', 'N/A')}",
            f"parameter_sweep={data.get('parameter_sweep', {}).get('quality', 'N/A')}",
            f"market_state={data.get('market_state', {}).get('quality', 'N/A')}",
            "B1=preview_only",
        ]
    )


def _has_warning(exposure: dict, keyword: str) -> bool:
    return any(keyword in str(item) for item in exposure.get("warnings", [])) or keyword in str(exposure.get("exposure_note", ""))


def _largest_abs_delta(rows: list[dict]) -> dict:
    if not rows:
        return {}
    return max(rows, key=lambda item: abs(_float(item.get("score_delta"))))


def _rows_for_symbols(rows: list[dict], symbols: list[str]) -> list[dict]:
    by_symbol = {str(row.get("symbol")): row for row in rows}
    return [by_symbol[symbol] for symbol in symbols if symbol in by_symbol]


def _top_symbols(df: pd.DataFrame, col: str, n: int) -> list[str]:
    if df.empty or col not in df.columns:
        return []
    return [str(item) for item in df[col].head(n).tolist()]


def _ordered_list(rows: list[dict], score_key: str, rank_key: str) -> list[str]:
    if not rows:
        return ["- 暂无。"]
    return [f"{idx}. {row.get('symbol')} {row.get('name')}：rank={row.get(rank_key)}，score={_fmt(row.get(score_key))}" for idx, row in enumerate(rows, start=1)]


def _bullet_rows(rows: list[dict], field: str) -> list[str]:
    if not rows:
        return [f"- {field}：无命中。"]
    return [f"- {row.get('symbol')} {row.get('name')}：{field}={_fmt(row.get(field))}；{row.get('enhancement_reason')}" for row in rows[:8]]


def _safety_lines() -> list[str]:
    return [
        "",
        "## 安全边界",
        "- 本轮只做 preview，不改变真实模拟盘成交结果。",
        "- 不修改 paper_trade_engine 核心执行规则。",
        "- 不启用 market_state 仓位控制。",
        "- 不启用 adjusted_rank_score 作为真实买入排序。",
        "- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。",
    ]


def _latest_date() -> str:
    latest = ""
    for path in (DATA_DIR / "etf_daily").glob("*.csv"):
        try:
            df = pd.read_csv(path, usecols=["date"], dtype=str)
        except Exception:
            continue
        if not df.empty:
            latest = max(latest, str(df["date"].max()))
    return latest or pd.Timestamp.now().strftime("%Y-%m-%d")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")


def _json_list(value: object) -> list[str]:
    try:
        parsed = json.loads(str(value or "[]"))
    except Exception:
        return []
    return parsed if isinstance(parsed, list) else []


def _float(value: object, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    if pd.isna(numeric):
        return fallback
    return numeric


def _fmt(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if pd.isna(numeric):
        return "N/A"
    return f"{numeric:.4f}".rstrip("0").rstrip(".")


if __name__ == "__main__":
    main()
