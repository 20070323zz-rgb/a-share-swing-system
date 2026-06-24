"""Shadow tracking for original ranking vs adjusted preview ranking.

This module writes research-only tracking data. It never changes
paper_trade_engine ordering, never writes paper_trades.csv, never changes
paper_positions.csv, and never connects to broker APIs.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

from config import (
    BROKER_API_ENABLED,
    DATA_DIR,
    DEFAULT_SHADOW_INITIAL_CASH,
    ETF_DAILY_DIR,
    PAPER_USE_MARKET_STATE_POSITION,
    REAL_TRADE_ENABLED,
    REPORT_DIR,
)


PREVIEW_FILE = REPORT_DIR / "strategy_enhancement_preview.csv"
TRACKING_DATA_FILE = DATA_DIR / "strategy_preview_tracking.csv"
TRACKING_REPORT_CSV = REPORT_DIR / "strategy_preview_tracking.csv"
TRACKING_REPORT_MD = REPORT_DIR / "strategy_preview_tracking_report.md"
B2_REPORT_MD = REPORT_DIR / "b2_strategy_preview_tracking_report.md"
SHADOW_CSV = REPORT_DIR / "strategy_preview_shadow_portfolio.csv"
SHADOW_MD = REPORT_DIR / "strategy_preview_shadow_portfolio.md"
QUALITY_REVIEW_FILE = REPORT_DIR / "model_research_quality_review.json"

FORWARD_WINDOWS = [1, 3, 5, 10]
SHADOW_INITIAL_CASH = float(DEFAULT_SHADOW_INITIAL_CASH)
SHADOW_MAX_HOLDINGS = 3
SHADOW_SINGLE_POSITION_TARGET = 0.20
SHADOW_TOTAL_TARGET_POSITION = 0.60
SHADOW_MIN_TRADE_VALUE = 3_000.0
TRACKING_COLUMNS = [
    "snapshot_date",
    "symbol",
    "name",
    "etf_type",
    "group",
    "market_state",
    "market_score",
    "portfolio_exposure_status",
    "data_health_status",
    "original_rank",
    "original_rank_score",
    "adjusted_rank_preview",
    "adjusted_rank_score_preview",
    "score_delta",
    "in_original_top3",
    "in_adjusted_top3",
    "in_both_top3",
    "only_in_original_top3",
    "only_in_adjusted_top3",
    "difference_reason",
    "enhancement_reason",
    "penalty_reason",
    "bonus_reason",
    "close_on_snapshot_date",
    "forward_1d_close",
    "forward_3d_close",
    "forward_5d_close",
    "forward_10d_close",
    "forward_1d_return",
    "forward_3d_return",
    "forward_5d_return",
    "forward_10d_return",
    "forward_returns_status",
    "created_at",
    "updated_at",
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    preview = _read_preview()
    existing = _read_tracking()
    snapshot_rows = _snapshot_rows(preview)
    merged, write_stats = _upsert_snapshot(existing, snapshot_rows)
    merged, fill_stats = _fill_forward_returns(merged)
    merged = _normalize_tracking(merged)
    merged.to_csv(TRACKING_DATA_FILE, index=False)
    merged.to_csv(TRACKING_REPORT_CSV, index=False)
    comparison = _comparison_stats(merged)
    shadow = _build_shadow_portfolio(merged)
    shadow.to_csv(SHADOW_CSV, index=False)
    _write_tracking_report(merged, comparison, write_stats, fill_stats)
    _write_shadow_report(shadow, comparison)
    _write_b2_report(merged, comparison, write_stats, fill_stats, shadow)
    print(f"已生成策略预览跟踪账本：{TRACKING_DATA_FILE}")
    print(f"已生成策略预览跟踪报告：{TRACKING_REPORT_MD}")


def _read_preview() -> pd.DataFrame:
    if not PREVIEW_FILE.exists() or PREVIEW_FILE.stat().st_size == 0:
        return pd.DataFrame()
    df = pd.read_csv(PREVIEW_FILE, dtype=str, keep_default_na=False).fillna("")
    for col in ["original_rank", "adjusted_rank_preview", "original_rank_score", "adjusted_rank_score_preview", "score_delta"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _read_tracking() -> pd.DataFrame:
    if not TRACKING_DATA_FILE.exists() or TRACKING_DATA_FILE.stat().st_size == 0:
        return pd.DataFrame(columns=TRACKING_COLUMNS)
    df = pd.read_csv(TRACKING_DATA_FILE, dtype=str, keep_default_na=False).fillna("")
    for col in TRACKING_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[TRACKING_COLUMNS].copy()


def _snapshot_rows(preview: pd.DataFrame) -> list[dict]:
    if preview.empty:
        return []
    snapshot_date = str(preview["date"].dropna().astype(str).max()) if "date" in preview.columns else _latest_data_date()
    original_top10 = set(_top_symbols(preview, "original_rank", 10))
    adjusted_top10 = set(_top_symbols(preview, "adjusted_rank_preview", 10))
    original_top3 = set(_top_symbols(preview, "original_rank", 3))
    adjusted_top3 = set(_top_symbols(preview, "adjusted_rank_preview", 3))
    delta_symbols = set(preview.loc[preview["score_delta"].abs() >= 3, "symbol"].astype(str))
    selected = original_top10 | adjusted_top10 | original_top3 | adjusted_top3 | delta_symbols
    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    rows: list[dict] = []
    for _, item in preview.iterrows():
        symbol = str(item.get("symbol", "")).strip()
        if not symbol or symbol not in selected:
            continue
        in_original = symbol in original_top3
        in_adjusted = symbol in adjusted_top3
        close = _close_at_snapshot(symbol, snapshot_date)
        rows.append(
            {
                "snapshot_date": snapshot_date,
                "symbol": symbol,
                "name": str(item.get("name", symbol)),
                "etf_type": str(item.get("etf_type", "")),
                "group": str(item.get("group", "")),
                "market_state": str(item.get("market_state", "")),
                "market_score": _market_score(),
                "portfolio_exposure_status": str(item.get("portfolio_exposure_status", "")),
                "data_health_status": _data_health_status_from_penalty(item),
                "original_rank": _fmt_num(item.get("original_rank")),
                "original_rank_score": _fmt_num(item.get("original_rank_score")),
                "adjusted_rank_preview": _fmt_num(item.get("adjusted_rank_preview")),
                "adjusted_rank_score_preview": _fmt_num(item.get("adjusted_rank_score_preview")),
                "score_delta": _fmt_num(item.get("score_delta")),
                "in_original_top3": _yn(in_original),
                "in_adjusted_top3": _yn(in_adjusted),
                "in_both_top3": _yn(in_original and in_adjusted),
                "only_in_original_top3": _yn(in_original and not in_adjusted),
                "only_in_adjusted_top3": _yn(in_adjusted and not in_original),
                "difference_reason": _difference_reason(in_original, in_adjusted, item),
                "enhancement_reason": str(item.get("enhancement_reason", "")),
                "penalty_reason": _penalty_reason(item),
                "bonus_reason": _bonus_reason(item),
                "close_on_snapshot_date": _fmt_num(close),
                "forward_1d_close": "",
                "forward_3d_close": "",
                "forward_5d_close": "",
                "forward_10d_close": "",
                "forward_1d_return": "",
                "forward_3d_return": "",
                "forward_5d_return": "",
                "forward_10d_return": "",
                "forward_returns_status": "pending" if close else "missing_data",
                "created_at": now,
                "updated_at": now,
            }
        )
    return rows


def _upsert_snapshot(existing: pd.DataFrame, rows: list[dict]) -> tuple[pd.DataFrame, dict]:
    if not rows:
        return existing.copy(), {"inserted": 0, "updated": 0, "snapshot_date": ""}
    df = existing.copy()
    inserted = 0
    updated = 0
    for row in rows:
        mask = (df["snapshot_date"].astype(str) == row["snapshot_date"]) & (df["symbol"].astype(str) == row["symbol"]) if not df.empty else pd.Series(dtype=bool)
        if not df.empty and bool(mask.any()):
            idx = df[mask].index[0]
            created_at = df.at[idx, "created_at"] or row["created_at"]
            for col, value in row.items():
                if col.startswith("forward_") and str(df.at[idx, col]).strip():
                    continue
                df.at[idx, col] = value
            df.at[idx, "created_at"] = created_at
            df.at[idx, "updated_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            updated += 1
        else:
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            inserted += 1
    return df, {"inserted": inserted, "updated": updated, "snapshot_date": rows[0]["snapshot_date"]}


def _fill_forward_returns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if df.empty:
        return df, {"filled_cells": 0, "completed_rows": 0, "partial_rows": 0, "pending_rows": 0, "missing_rows": 0}
    out = df.copy()
    filled_cells = 0
    for idx, row in out.iterrows():
        symbol = str(row.get("symbol", ""))
        snapshot_date = str(row.get("snapshot_date", ""))
        price_table = _price_table(symbol)
        if price_table.empty or snapshot_date not in set(price_table["date"].astype(str)):
            out.at[idx, "forward_returns_status"] = "missing_data"
            continue
        snap_idx = int(price_table.index[price_table["date"].astype(str) == snapshot_date][0])
        snap_close = _float(row.get("close_on_snapshot_date"))
        if snap_close <= 0:
            snap_close = _float(price_table.at[snap_idx, "close"])
            out.at[idx, "close_on_snapshot_date"] = _fmt_num(snap_close)
        completed = 0
        available = 0
        for window in FORWARD_WINDOWS:
            close_col = f"forward_{window}d_close"
            ret_col = f"forward_{window}d_return"
            target_idx = snap_idx + window
            if target_idx >= len(price_table):
                continue
            available += 1
            forward_close = _float(price_table.at[target_idx, "close"])
            if forward_close <= 0 or snap_close <= 0:
                continue
            old_close = str(out.at[idx, close_col]).strip()
            old_ret = str(out.at[idx, ret_col]).strip()
            out.at[idx, close_col] = _fmt_num(forward_close)
            out.at[idx, ret_col] = _fmt_num(forward_close / snap_close - 1)
            if not old_close or not old_ret:
                filled_cells += 1
            completed += 1
        if completed == len(FORWARD_WINDOWS):
            status = "completed"
        elif completed > 0:
            status = "partial"
        elif available == 0:
            status = "pending"
        else:
            status = "missing_data"
        out.at[idx, "forward_returns_status"] = status
        out.at[idx, "updated_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    counts = out["forward_returns_status"].value_counts().to_dict()
    return out, {
        "filled_cells": filled_cells,
        "completed_rows": int(counts.get("completed", 0)),
        "partial_rows": int(counts.get("partial", 0)),
        "pending_rows": int(counts.get("pending", 0)),
        "missing_rows": int(counts.get("missing_data", 0)),
    }


def _normalize_tracking(df: pd.DataFrame) -> pd.DataFrame:
    for col in TRACKING_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    if not df.empty:
        df = df.sort_values(["snapshot_date", "symbol"]).drop_duplicates(["snapshot_date", "symbol"], keep="last")
    return df[TRACKING_COLUMNS].reset_index(drop=True)


def _comparison_stats(df: pd.DataFrame) -> dict:
    rows = df.to_dict(orient="records") if not df.empty else []
    latest_date = max([str(row.get("snapshot_date", "")) for row in rows], default="")
    latest = [row for row in rows if row.get("snapshot_date") == latest_date]
    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "latest_snapshot_date": latest_date,
        "sample_count": len(rows),
        "completed_count": sum(1 for row in rows if row.get("forward_returns_status") == "completed"),
        "partial_count": sum(1 for row in rows if row.get("forward_returns_status") == "partial"),
        "pending_count": sum(1 for row in rows if row.get("forward_returns_status") == "pending"),
        "missing_count": sum(1 for row in rows if row.get("forward_returns_status") == "missing_data"),
        "original_top3": sorted([row for row in latest if row.get("in_original_top3") == "yes"], key=lambda row: _float(row.get("original_rank"))),
        "adjusted_top3": sorted([row for row in latest if row.get("in_adjusted_top3") == "yes"], key=lambda row: _float(row.get("adjusted_rank_preview"))),
        "top3_changed": _latest_top3_changed(latest),
        "only_original_count": sum(1 for row in latest if row.get("only_in_original_top3") == "yes"),
        "only_adjusted_count": sum(1 for row in latest if row.get("only_in_adjusted_top3") == "yes"),
        "returns": {
            "original_top3": _avg_returns(rows, lambda row: row.get("in_original_top3") == "yes"),
            "adjusted_top3": _avg_returns(rows, lambda row: row.get("in_adjusted_top3") == "yes"),
            "only_original_top3": _avg_returns(rows, lambda row: row.get("only_in_original_top3") == "yes"),
            "only_adjusted_top3": _avg_returns(rows, lambda row: row.get("only_in_adjusted_top3") == "yes"),
            "high_beta_penalty": _avg_returns(rows, lambda row: "high_beta" in str(row.get("penalty_reason", ""))),
            "data_health_penalty": _avg_returns(rows, lambda row: "data_health" in str(row.get("penalty_reason", ""))),
            "concentration_penalty": _avg_returns(rows, lambda row: "same_group" in str(row.get("penalty_reason", "")) or "concentration" in str(row.get("penalty_reason", ""))),
            "broad_index_bonus": _avg_returns(rows, lambda row: "broad_index" in str(row.get("bonus_reason", ""))),
            "defensive_bonus": _avg_returns(rows, lambda row: "defensive" in str(row.get("bonus_reason", ""))),
        },
        "sample_sufficient": sum(1 for row in rows if row.get("forward_returns_status") == "completed") >= 30,
        "conclusion": _conclusion(rows),
        "execution_safety": _execution_safety(),
    }


def _build_shadow_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "snapshot_date",
                "symbol",
                "name",
                "shadow_rank",
                "shadow_weight",
                "shadow_target_value",
                "initial_cash_assumption",
                "research_only",
                *[f"forward_{w}d_return" for w in FORWARD_WINDOWS],
            ]
        )
    rows = []
    for date_value, group in df[df["in_adjusted_top3"].astype(str) == "yes"].groupby("snapshot_date"):
        group = group.sort_values("adjusted_rank_preview", key=lambda s: pd.to_numeric(s, errors="coerce"))
        for _, row in group.iterrows():
            rows.append(
                {
                    "snapshot_date": date_value,
                    "symbol": row["symbol"],
                    "name": row["name"],
                    "shadow_rank": row["adjusted_rank_preview"],
                    "shadow_weight": 1 / 3,
                    "shadow_target_value": round(SHADOW_INITIAL_CASH * SHADOW_TOTAL_TARGET_POSITION / SHADOW_MAX_HOLDINGS, 2),
                    "initial_cash_assumption": SHADOW_INITIAL_CASH,
                    "max_holdings": SHADOW_MAX_HOLDINGS,
                    "single_position_target": SHADOW_SINGLE_POSITION_TARGET,
                    "total_target_position": SHADOW_TOTAL_TARGET_POSITION,
                    "min_trade_value": SHADOW_MIN_TRADE_VALUE,
                    "research_only": "yes",
                    "execution_enabled": "no",
                    "paper_trade_engine_enabled": "no",
                    "real_trade_enabled": "no",
                    "forward_1d_return": row["forward_1d_return"],
                    "forward_3d_return": row["forward_3d_return"],
                    "forward_5d_return": row["forward_5d_return"],
                    "forward_10d_return": row["forward_10d_return"],
                    "forward_returns_status": row["forward_returns_status"],
                }
            )
    return pd.DataFrame(rows)


def _write_tracking_report(df: pd.DataFrame, comparison: dict, write_stats: dict, fill_stats: dict) -> None:
    lines = [
        f"# Strategy Preview Tracking Report {comparison['generated_at']}",
        "",
        "本报告追踪 original BUY ranking 与 adjusted preview ranking 的后续表现，只作研究，不影响 paper_trade_engine。",
        "",
        "## 摘要",
        f"- latest_snapshot_date：{comparison.get('latest_snapshot_date')}",
        f"- tracking rows：{comparison.get('sample_count')}",
        f"- inserted / updated：{write_stats.get('inserted')} / {write_stats.get('updated')}",
        f"- forward filled cells：{fill_stats.get('filled_cells')}",
        f"- completed / partial / pending / missing：{comparison.get('completed_count')} / {comparison.get('partial_count')} / {comparison.get('pending_count')} / {comparison.get('missing_count')}",
        f"- Top 3 是否变化：{'是' if comparison.get('top3_changed') else '否'}",
        f"- 样本是否足够：{'是' if comparison.get('sample_sufficient') else '否'}",
        f"- 结论：{comparison.get('conclusion')}",
        "",
        "## 今日 Original Top 3",
        *_list_rows(comparison.get("original_top3", []), "original_rank", "original_rank_score"),
        "",
        "## 今日 Adjusted Preview Top 3",
        *_list_rows(comparison.get("adjusted_top3", []), "adjusted_rank_preview", "adjusted_rank_score_preview"),
        "",
        "## Forward Return Comparison",
        *_return_table(comparison.get("returns", {})),
        "",
        "## Penalty / Bonus Review",
        *_penalty_bonus_lines(comparison.get("returns", {})),
    ]
    lines += _safety_lines()
    TRACKING_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_shadow_report(shadow: pd.DataFrame, comparison: dict) -> None:
    lines = [
        f"# Strategy Preview Shadow Portfolio {comparison['generated_at']}",
        "",
        "本影子组合只记录 adjusted Top 3 的理论观察收益，不写 paper_trades，不写 paper_positions，不影响真实模拟盘。",
        "",
        f"- rows：{len(shadow)}",
        f"- initial_cash_assumption：{SHADOW_INITIAL_CASH:.2f}",
        f"- max_holdings：{SHADOW_MAX_HOLDINGS}",
        f"- single_position_target：{SHADOW_SINGLE_POSITION_TARGET:.0%}",
        f"- total_target_position：{SHADOW_TOTAL_TARGET_POSITION:.0%}",
        f"- min_trade_value：{SHADOW_MIN_TRADE_VALUE:.2f}",
        "- shadow_model_enabled：true",
        "- shadow_model_execution_enabled：false",
        "- paper_trade_engine_enabled：false",
        "- real_trade_enabled：false",
        "- research_only：true",
        "- 20000 是 shadow/research 观察基准，不代表用户需要真实投入。",
        "",
        "## 最近影子组合",
        "| snapshot_date | rank | symbol | name | weight | target_value | status | fwd1 | fwd3 | fwd5 | fwd10 |",
        "| --- | ---: | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    if shadow.empty:
        lines.append("| N/A |  |  |  |  |  |  |  |  |  |  |")
    else:
        for _, row in shadow.tail(12).iterrows():
            lines.append(
                f"| {row.get('snapshot_date','')} | {row.get('shadow_rank','')} | {row.get('symbol','')} | {row.get('name','')} | "
                f"{_pct(row.get('shadow_weight'))} | {row.get('shadow_target_value','')} | {row.get('forward_returns_status','')} | {_pct(row.get('forward_1d_return'))} | "
                f"{_pct(row.get('forward_3d_return'))} | {_pct(row.get('forward_5d_return'))} | {_pct(row.get('forward_10d_return'))} |"
            )
    lines += _safety_lines()
    SHADOW_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_b2_report(df: pd.DataFrame, comparison: dict, write_stats: dict, fill_stats: dict, shadow: pd.DataFrame) -> None:
    lines = [
        "# B2 Original vs Adjusted Preview Tracking 报告",
        "",
        f"- 生成时间：{comparison['generated_at']}",
        "- 阶段：B2 strategy_preview_tracking_v1。",
        "- 目标：长期跟踪 original ranking 与 adjusted preview ranking 的 forward returns。",
        "",
        "## 今日 Top 3",
        "### Original Top 3",
        *_list_rows(comparison.get("original_top3", []), "original_rank", "original_rank_score"),
        "",
        "### Adjusted Preview Top 3",
        *_list_rows(comparison.get("adjusted_top3", []), "adjusted_rank_preview", "adjusted_rank_score_preview"),
        "",
        f"- Top 3 是否变化：{'是' if comparison.get('top3_changed') else '否'}。",
        "",
        "## Tracking 写入",
        f"- 新增：{write_stats.get('inserted')} 条。",
        f"- 更新：{write_stats.get('updated')} 条。",
        f"- forward return 回填 cell：{fill_stats.get('filled_cells')}。",
        f"- completed / partial / pending / missing：{comparison.get('completed_count')} / {comparison.get('partial_count')} / {comparison.get('pending_count')} / {comparison.get('missing_count')}。",
        "",
        "## 当前样本结论",
        f"- 样本是否足够：{'是' if comparison.get('sample_sufficient') else '否'}。",
        f"- 是否可以证明 adjusted preview 更优：否。{comparison.get('conclusion')}",
        "",
        "## 影子组合",
        f"- shadow rows：{len(shadow)}。",
        f"- initial_cash_assumption：{SHADOW_INITIAL_CASH:.2f}。",
        f"- single_position_target：{SHADOW_SINGLE_POSITION_TARGET:.0%}；total_target_position：{SHADOW_TOTAL_TARGET_POSITION:.0%}；min_trade_value：{SHADOW_MIN_TRADE_VALUE:.2f}。",
        "- shadow_model_enabled：true。",
        "- shadow_model_execution_enabled：false。",
        "- paper_trade_engine_enabled：false。",
        "- real_trade_enabled：false。",
        "- 仅作 research only，不影响真实模拟盘。",
        "",
        "## 是否影响真实模拟交易",
        "- 不影响 paper_trade_engine。",
        "- 不修改 paper_trades.csv。",
        "- 不修改 paper_positions.csv。",
    ]
    lines += _safety_lines()
    B2_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _avg_returns(rows: list[dict], selector) -> dict:
    selected = [row for row in rows if selector(row)]
    out = {"sample_count": len(selected)}
    for window in FORWARD_WINDOWS:
        values = [_float(row.get(f"forward_{window}d_return"), fallback=float("nan")) for row in selected]
        values = [item for item in values if pd.notna(item)]
        out[f"forward_{window}d_mean"] = sum(values) / len(values) if values else ""
        out[f"forward_{window}d_n"] = len(values)
    return out


def _return_table(stats: dict) -> list[str]:
    lines = [
        "| group | sample | 1d mean | 1d n | 3d mean | 3d n | 5d mean | 5d n | 10d mean | 10d n |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, row in stats.items():
        lines.append(
            f"| {key} | {row.get('sample_count', 0)} | {_pct(row.get('forward_1d_mean'))} | {row.get('forward_1d_n', 0)} | "
            f"{_pct(row.get('forward_3d_mean'))} | {row.get('forward_3d_n', 0)} | {_pct(row.get('forward_5d_mean'))} | {row.get('forward_5d_n', 0)} | "
            f"{_pct(row.get('forward_10d_mean'))} | {row.get('forward_10d_n', 0)} |"
        )
    return lines


def _penalty_bonus_lines(stats: dict) -> list[str]:
    return [
        f"- high_beta penalty ETF 后续表现：{_summary_return(stats.get('high_beta_penalty', {}))}",
        f"- data_health penalty ETF 后续表现：{_summary_return(stats.get('data_health_penalty', {}))}",
        f"- concentration penalty ETF 后续表现：{_summary_return(stats.get('concentration_penalty', {}))}",
        f"- broad_index bonus ETF 后续表现：{_summary_return(stats.get('broad_index_bonus', {}))}",
        f"- defensive bonus ETF 后续表现：{_summary_return(stats.get('defensive_bonus', {}))}",
    ]


def _summary_return(row: dict) -> str:
    return f"sample={row.get('sample_count', 0)}, 1d={_pct(row.get('forward_1d_mean'))}, 3d={_pct(row.get('forward_3d_mean'))}, 5d={_pct(row.get('forward_5d_mean'))}, 10d={_pct(row.get('forward_10d_mean'))}"


def _list_rows(rows: list[dict], rank_key: str, score_key: str) -> list[str]:
    if not rows:
        return ["- 暂无。"]
    return [f"{idx}. {row.get('symbol')} {row.get('name')}：rank={row.get(rank_key)}，score={_fmt(row.get(score_key))}" for idx, row in enumerate(rows, start=1)]


def _latest_top3_changed(rows: list[dict]) -> bool:
    original = sorted([row for row in rows if row.get("in_original_top3") == "yes"], key=lambda row: _float(row.get("original_rank")))
    adjusted = sorted([row for row in rows if row.get("in_adjusted_top3") == "yes"], key=lambda row: _float(row.get("adjusted_rank_preview")))
    return [row.get("symbol") for row in original] != [row.get("symbol") for row in adjusted]


def _conclusion(rows: list[dict]) -> str:
    completed = sum(1 for row in rows if row.get("forward_returns_status") == "completed")
    if completed < 30:
        return "当前样本不足，不能证明 adjusted preview 优于 original ranking。"
    return "样本已开始积累，但仍需结合周/月度复盘后再判断是否接入执行层。"


def _difference_reason(in_original: bool, in_adjusted: bool, item: pd.Series) -> str:
    if in_original and in_adjusted:
        return "in_both_top3"
    if in_original:
        return "only_in_original_top3"
    if in_adjusted:
        return "only_in_adjusted_top3"
    if abs(_float(item.get("score_delta"))) >= 3:
        return "score_delta_abs_ge_3"
    return "top10_tracking"


def _penalty_reason(item: pd.Series) -> str:
    reasons = []
    fields = {
        "same_group_concentration_penalty": "same_group_concentration_penalty",
        "high_beta_penalty": "high_beta_penalty",
        "data_health_penalty": "data_health_penalty",
        "qdii_auto_buy_penalty": "qdii_auto_buy_penalty",
        "liquidity_penalty": "liquidity_penalty",
    }
    for field, label in fields.items():
        if _float(item.get(field)) < 0:
            reasons.append(label)
    return "; ".join(reasons)


def _bonus_reason(item: pd.Series) -> str:
    reasons = []
    if _float(item.get("broad_index_balance_bonus")) > 0:
        reasons.append("broad_index_balance_bonus")
    if _float(item.get("defensive_balance_bonus")) > 0:
        reasons.append("defensive_balance_bonus")
    return "; ".join(reasons)


def _data_health_status_from_penalty(item: pd.Series) -> str:
    penalty = _float(item.get("data_health_penalty"))
    if penalty <= -999:
        return "异常"
    if penalty < 0:
        return "提醒"
    return "正常"


def _market_score() -> str:
    market_path = REPORT_DIR / "market_state.csv"
    if not market_path.exists():
        return ""
    df = pd.read_csv(market_path, dtype=str, keep_default_na=False).fillna("")
    if df.empty or "row_type" not in df.columns:
        return ""
    summary = df[df["row_type"].astype(str) == "summary"].head(1)
    return str(summary.iloc[0].get("market_score", "")) if not summary.empty else ""


def _close_at_snapshot(symbol: str, snapshot_date: str) -> float:
    prices = _price_table(symbol)
    if prices.empty:
        return 0.0
    matched = prices[prices["date"].astype(str) == snapshot_date]
    if matched.empty:
        return 0.0
    return _float(matched.iloc[0]["close"])


def _price_table(symbol: str) -> pd.DataFrame:
    prefix = "sh" if str(symbol).startswith(("5", "6")) else "sz"
    path = ETF_DAILY_DIR / f"{prefix}_{symbol}.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, dtype={"date": str})
    except Exception:
        return pd.DataFrame()
    if df.empty or not {"date", "close"}.issubset(df.columns):
        return pd.DataFrame()
    df = df[["date", "close"]].copy()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    return df


def _top_symbols(df: pd.DataFrame, rank_col: str, n: int) -> list[str]:
    if df.empty or rank_col not in df.columns:
        return []
    return df.sort_values(rank_col, ascending=True)["symbol"].astype(str).head(n).tolist()


def _latest_data_date() -> str:
    latest = ""
    for path in ETF_DAILY_DIR.glob("*.csv"):
        try:
            df = pd.read_csv(path, usecols=["date"], dtype=str)
        except Exception:
            continue
        if not df.empty:
            latest = max(latest, str(df["date"].max()))
    return latest or pd.Timestamp.now().strftime("%Y-%m-%d")


def _execution_safety() -> dict:
    return {
        "adjusted_rank_score_preview_enabled": True,
        "adjusted_rank_score_execution_enabled": False,
        "paper_use_market_state_position": bool(PAPER_USE_MARKET_STATE_POSITION),
        "shadow_model_enabled": True,
        "shadow_model_execution_enabled": False,
        "real_trade_enabled": bool(REAL_TRADE_ENABLED),
        "broker_api_enabled": bool(BROKER_API_ENABLED),
    }


def _safety_lines() -> list[str]:
    return [
        "",
        "## 安全边界",
        "- research only / preview only。",
        "- 不改变 paper_trade_engine 执行排序。",
        "- 不启用 adjusted_rank_score 执行。",
        "- 不启用 market_state 仓位控制。",
        "- 不修改 paper_trades.csv。",
        "- 不修改 paper_positions.csv。",
        "- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。",
    ]


def _yn(value: bool) -> str:
    return "yes" if value else "no"


def _fmt_num(value: object) -> str:
    numeric = _float(value, fallback=float("nan"))
    if pd.isna(numeric):
        return ""
    return f"{numeric:.8f}".rstrip("0").rstrip(".")


def _fmt(value: object) -> str:
    numeric = _float(value, fallback=float("nan"))
    if pd.isna(numeric):
        return "N/A"
    return f"{numeric:.4f}".rstrip("0").rstrip(".")


def _pct(value: object) -> str:
    numeric = _float(value, fallback=float("nan"))
    if pd.isna(numeric):
        return "N/A"
    return f"{numeric:.2%}"


def _float(value: object, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    if pd.isna(numeric):
        return fallback
    return numeric


if __name__ == "__main__":
    main()
