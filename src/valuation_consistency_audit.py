"""Audit paper valuation consistency across reports.

Read-only audit: does not modify paper_positions or paper_trades.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from config import DATA_DIR, PAPER_POSITIONS_FILE, PAPER_TRADES_FILE, REPORT_DIR
from valuation import load_latest_position_valuation


AUDIT_JSON = REPORT_DIR / "valuation_consistency_audit.json"
AUDIT_MD = REPORT_DIR / "valuation_consistency_audit.md"
CHECK_MD = REPORT_DIR / "valuation_consistency_check.md"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_audit()
    AUDIT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    AUDIT_MD.write_text(render_audit(payload), encoding="utf-8")
    CHECK_MD.write_text(render_check(payload), encoding="utf-8")
    print(f"valuation consistency diff: {payload['diff_after_unification']:.2f}")
    print(f"written: {AUDIT_MD}")
    print(f"written: {CHECK_MD}")


def build_audit() -> dict[str, Any]:
    valuation = load_latest_position_valuation()
    valuation_df = valuation["positions"]
    valuation_summary = valuation["summary"]
    paper_perf = _read_json(REPORT_DIR / "paper_performance_summary.json")
    exposure_json = _read_json(REPORT_DIR / "portfolio_exposure.json")
    exposure_csv = _read_csv(REPORT_DIR / "portfolio_exposure.csv")
    positions = _read_csv(PAPER_POSITIONS_FILE)

    position_file_total = _sum_numeric(positions, "market_value")
    unified_total = float(valuation_summary.get("total_market_value", 0.0))
    performance_total = float(paper_perf.get("current_position_value", 0.0) or 0.0)
    exposure_total = 0.0
    if isinstance(exposure_json, dict) and exposure_json.get("summary"):
        exposure_total = float(exposure_json["summary"].get("market_value", 0.0) or 0.0)
    elif not exposure_csv.empty:
        summary = exposure_csv[exposure_csv.get("row_type", "") == "summary"].head(1)
        exposure_total = _sum_numeric(summary, "market_value")

    return {
        "status": "PASS" if abs(performance_total - exposure_total) <= 0.01 and abs(unified_total - performance_total) <= 0.01 else "REVIEW",
        "official_valuation_basis": "data/paper_positions.csv + data/etf_daily/{symbol}.csv latest close",
        "as_of_date": valuation_summary.get("as_of_date", ""),
        "position_count": int(valuation_summary.get("position_count", 0)),
        "position_file_snapshot_market_value": round(position_file_total, 2),
        "unified_latest_close_market_value": round(unified_total, 2),
        "paper_performance_market_value": round(performance_total, 2),
        "portfolio_exposure_market_value": round(exposure_total, 2),
        "diff_before_unification": round(position_file_total - performance_total, 2),
        "diff_after_unification": round(exposure_total - performance_total, 2),
        "price_warning_count": int(valuation_summary.get("price_warning_count", 0)),
        "positions": valuation_df[
            [
                "symbol",
                "name",
                "quantity",
                "cost",
                "latest_close",
                "market_value",
                "unrealized_pnl",
                "as_of_date",
                "price_status",
                "position_file_market_value",
                "market_value_diff_vs_position_file",
            ]
        ].to_dict(orient="records")
        if not valuation_df.empty
        else [],
        "forbidden_file_hashes": {
            "paper_trades_sha256": _sha256(PAPER_TRADES_FILE),
            "paper_positions_sha256": _sha256(PAPER_POSITIONS_FILE),
            "paper_trade_engine_sha256": _sha256(DATA_DIR.parent / "src" / "paper_trade_engine.py"),
        },
        "safety": {
            "broker_api": False,
            "real_order": False,
            "real_account": False,
            "paper_trades_modified": False,
            "paper_positions_modified": False,
        },
    }


def render_audit(payload: dict[str, Any]) -> str:
    lines = [
        "# 模拟仓估值一致性审计",
        "",
        "本报告只读取本地模拟仓和 ETF 日线数据，不接券商 API，不真实下单，不修改 paper_positions / paper_trades。",
        "",
        "## 结论",
        f"- status：{payload['status']}",
        f"- 正式估值口径：{payload['official_valuation_basis']}",
        f"- 估值日期：{payload.get('as_of_date') or 'N/A'}",
        f"- 持仓数量：{payload['position_count']}",
        f"- 统一最新 close 持仓市值：{payload['unified_latest_close_market_value']:.2f}",
        f"- paper_performance 持仓市值：{payload['paper_performance_market_value']:.2f}",
        f"- portfolio_exposure 持仓市值：{payload['portfolio_exposure_market_value']:.2f}",
        f"- 统一后差异：{payload['diff_after_unification']:.2f}",
        f"- 原持仓快照旧市值与绩效差异：{payload['diff_before_unification']:.2f}",
        "",
        "## 持仓估值明细",
        "| symbol | name | quantity | latest_close | market_value | position_file_market_value | diff_vs_position_file | as_of_date | price_status |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload.get("positions", []):
        lines.append(
            f"| {row['symbol']} | {row['name']} | {float(row['quantity']):.0f} | {float(row['latest_close']):.4f} | "
            f"{float(row['market_value']):.2f} | {float(row['position_file_market_value']):.2f} | "
            f"{float(row['market_value_diff_vs_position_file']):+.2f} | {row['as_of_date']} | {row['price_status']} |"
        )
    lines += [
        "",
        "## 差异解释",
        "- paper_positions.csv 内的 market_value 是持仓快照字段，可能滞后于最新 ETF 日线 close。",
        "- paper_performance 使用本地 ETF close 生成权益曲线和当前持仓市值。",
        "- portfolio_exposure 已改为使用统一估值模块，避免继续引用旧快照市值。",
        "",
        "## 安全边界",
        "- 未接券商 API。",
        "- 未真实下单。",
        "- 未读取真实账户。",
        "- 未修改 paper_positions.csv / paper_trades.csv。",
    ]
    return "\n".join(lines)


def render_check(payload: dict[str, Any]) -> str:
    result = "通过" if payload["status"] == "PASS" else "需复核"
    return "\n".join(
        [
            "# 估值一致性检查",
            "",
            f"- 检查结果：{result}",
            f"- paper_performance：{payload['paper_performance_market_value']:.2f}",
            f"- portfolio_exposure：{payload['portfolio_exposure_market_value']:.2f}",
            f"- 差异：{payload['diff_after_unification']:.2f}",
            f"- 估值日期：{payload.get('as_of_date') or 'N/A'}",
            f"- 价格警告数量：{payload['price_warning_count']}",
            "",
            "统一口径：paper_positions 持仓数量/成本 + etf_daily 最新 close。",
        ]
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _sum_numeric(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())


def _sha256(path: Path) -> str:
    import hashlib

    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
