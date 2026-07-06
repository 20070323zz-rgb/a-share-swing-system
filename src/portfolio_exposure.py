"""Portfolio exposure research report for the local paper account."""

from __future__ import annotations

import json

import pandas as pd

from config import DATA_DIR, REPORT_DIR
from etf_classifier import CLASSIFICATION_FILE, main as build_classification
from valuation import load_latest_position_valuation


CSV_FILE = REPORT_DIR / "portfolio_exposure.csv"
REPORT_FILE = REPORT_DIR / "portfolio_exposure_report.md"
REPORT_ALIAS_FILE = REPORT_DIR / "portfolio_exposure.md"
JSON_FILE = REPORT_DIR / "portfolio_exposure.json"
POSITIONS_FILE = DATA_DIR / "paper_positions.csv"
INITIAL_CASH = 10000.0


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not CLASSIFICATION_FILE.exists():
        build_classification()
    valuation = load_latest_position_valuation()
    positions = valuation["positions"]
    valuation_summary = valuation["summary"]
    classification = _read_classification()
    rows = build_exposure_rows(positions, classification)
    df = pd.DataFrame(rows)
    df.to_csv(CSV_FILE, index=False)
    report_text = render_report(df, valuation_summary)
    REPORT_FILE.write_text(report_text, encoding="utf-8")
    REPORT_ALIAS_FILE.write_text(report_text, encoding="utf-8")
    JSON_FILE.write_text(json.dumps(_json_payload(df, valuation_summary), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"portfolio_exposure rows: {len(df)}")
    print(f"written: {CSV_FILE}")
    print(f"written: {REPORT_FILE}")


def build_exposure_rows(positions: pd.DataFrame, classification: pd.DataFrame) -> list[dict]:
    if positions.empty:
        return [_summary_row([], 0.0, 0.0, "no_positions", [])]
    meta = classification.set_index("symbol").to_dict(orient="index") if not classification.empty and "symbol" in classification.columns else {}
    detail_rows = []
    total_market_value = pd.to_numeric(positions.get("market_value", 0), errors="coerce").fillna(0).sum()
    for _, pos in positions.iterrows():
        symbol = str(pos.get("symbol") or pos.get("code") or "").strip()
        item = meta.get(symbol, {})
        market_value = _float(pos.get("market_value"))
        row = {
            "row_type": "position",
            "symbol": symbol,
            "name": pos.get("name") or item.get("name", symbol),
            "group": item.get("group") or pos.get("group") or _fallback_group(pos.get("name", "")),
            "pool": item.get("pool", ""),
            "etf_type": item.get("etf_type") or pos.get("etf_type") or "unknown",
            "risk_profile": item.get("risk_profile", "manual_review"),
            "market_value": round(market_value, 2),
            "position_ratio": round(market_value / INITIAL_CASH, 6),
            "portfolio_weight": round(market_value / total_market_value, 6) if total_market_value else 0.0,
            "unrealized_pnl": round(_float(pos.get("unrealized_pnl")), 2),
            "unrealized_pnl_pct": round(_float(pos.get("unrealized_pnl_pct", pos.get("unrealized_return"))), 6),
            "latest_close": round(_float(pos.get("latest_close", pos.get("current_price"))), 6),
            "as_of_date": pos.get("as_of_date", ""),
            "price_status": pos.get("price_status", ""),
            "valuation_source": pos.get("valuation_source", ""),
            "market_value_diff_vs_position_file": round(_float(pos.get("market_value_diff_vs_position_file")), 2),
            "data_health_status": pos.get("data_health_status", ""),
            "sell_review_status": pos.get("sell_review_status", ""),
            "exposure_note": _position_note(symbol, item, pos),
        }
        detail_rows.append(row)
    warnings = _warnings(detail_rows, total_market_value)
    rows = [_summary_row(detail_rows, total_market_value, total_market_value / INITIAL_CASH, _overall_status(warnings), warnings)]
    rows.extend(detail_rows)
    rows.extend(_group_rows(detail_rows, "group", total_market_value))
    rows.extend(_group_rows(detail_rows, "etf_type", total_market_value))
    rows.extend(_group_rows(detail_rows, "risk_profile", total_market_value))
    return rows


def render_report(df: pd.DataFrame, valuation_summary: dict | None = None) -> str:
    summary = df[df["row_type"] == "summary"].head(1)
    if summary.empty:
        status = "unknown"
        total_value = 0.0
        position_ratio = 0.0
        warnings = []
    else:
        row = summary.iloc[0]
        status = row["overall_status"]
        total_value = float(row["market_value"])
        position_ratio = float(row["position_ratio"])
        warnings = json.loads(row["warnings_json"] or "[]")
    lines = [
        "# 组合暴露研究报告",
        "",
        "本报告只读取本地模拟持仓，不修改 paper_positions / paper_trades，不生成真实交易。",
        "",
        "## 摘要",
        f"- overall_status：{status}",
        f"- 当前持仓市值：{total_value:.2f}",
        f"- 当前仓位：{position_ratio:.2%}",
        f"- 估值日期：{(valuation_summary or {}).get('as_of_date', '') or 'N/A'}",
        f"- 估值口径：{(valuation_summary or {}).get('valuation_source', 'paper_positions + etf_daily latest close')}",
        f"- 价格警告数量：{(valuation_summary or {}).get('price_warning_count', 0)}",
        f"- 风险提示数量：{len(warnings)}",
    ]
    if warnings:
        lines += ["", "## 风险提示"]
        lines.extend([f"- {item}" for item in warnings])
    lines += [
        "",
        "## 持仓暴露",
        "| symbol | name | group | etf_type | latest_close | as_of_date | market_value | position_ratio | portfolio_weight | data_health | sell_review | price_status | note |",
        "| --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    positions = df[df["row_type"] == "position"].copy()
    if positions.empty:
        lines.append("|  | 当前无持仓 |  |  |  |  |  |  |  |  |  |  |  |")
    else:
        for _, row in positions.iterrows():
            lines.append(
                f"| {row['symbol']} | {row['name']} | {row['group']} | {row['etf_type']} | {float(row['latest_close']):.4f} | {row['as_of_date']} | "
                f"{float(row['market_value']):.2f} | {float(row['position_ratio']):.2%} | {float(row['portfolio_weight']):.2%} | "
                f"{row['data_health_status']} | {row['sell_review_status']} | {row['price_status']} | {row['exposure_note']} |"
            )
    lines += [
        "",
        "## 暴露汇总",
        "| dimension | bucket | market_value | portfolio_weight |",
        "| --- | --- | ---: | ---: |",
    ]
    buckets = df[df["row_type"].isin(["group", "etf_type", "risk_profile"])].copy()
    if buckets.empty:
        lines.append("|  | 无 |  |  |")
    else:
        for _, row in buckets.iterrows():
            lines.append(f"| {row['dimension']} | {row['bucket']} | {float(row['market_value']):.2f} | {float(row['portfolio_weight']):.2%} |")
    lines += [
        "",
        "## 研究边界",
        "- 暴露报告只用于风险观察和看板展示。",
        "- 不自动改变总仓位、不自动加减仓、不改变单 ETF 上限。",
    ]
    return "\n".join(lines)


def _summary_row(details: list[dict], market_value: float, position_ratio: float, overall_status: str, warnings: list[str]) -> dict:
    return {
        "row_type": "summary",
        "dimension": "portfolio",
        "bucket": "total",
        "symbol": "PORTFOLIO",
        "name": "paper_portfolio",
        "group": "",
        "pool": "",
        "etf_type": "",
        "risk_profile": "",
        "market_value": round(market_value, 2),
        "position_ratio": round(position_ratio, 6),
        "portfolio_weight": 1.0 if market_value else 0.0,
        "unrealized_pnl": round(sum(_float(row.get("unrealized_pnl")) for row in details), 2),
        "unrealized_pnl_pct": "",
        "latest_close": "",
        "as_of_date": "",
        "price_status": "",
        "valuation_source": "paper_positions + etf_daily latest close",
        "market_value_diff_vs_position_file": round(sum(_float(row.get("market_value_diff_vs_position_file")) for row in details), 2),
        "data_health_status": "",
        "sell_review_status": "",
        "overall_status": overall_status,
        "warnings_json": json.dumps(warnings, ensure_ascii=False),
        "exposure_note": "; ".join(warnings[:3]) if warnings else "no_major_exposure_warning",
    }


def _group_rows(details: list[dict], field: str, total: float) -> list[dict]:
    values: dict[str, float] = {}
    for row in details:
        key = str(row.get(field) or "unknown")
        values[key] = values.get(key, 0.0) + _float(row.get("market_value"))
    rows = []
    for key, value in sorted(values.items(), key=lambda item: item[1], reverse=True):
        rows.append(
            {
                "row_type": field,
                "dimension": field,
                "bucket": key,
                "symbol": "",
                "name": "",
                "group": "",
                "pool": "",
                "etf_type": "",
                "risk_profile": "",
                "market_value": round(value, 2),
                "position_ratio": round(value / INITIAL_CASH, 6),
                "portfolio_weight": round(value / total, 6) if total else 0.0,
                "unrealized_pnl": "",
                "unrealized_pnl_pct": "",
                "latest_close": "",
                "as_of_date": "",
                "price_status": "",
                "valuation_source": "paper_positions + etf_daily latest close",
                "market_value_diff_vs_position_file": "",
                "data_health_status": "",
                "sell_review_status": "",
                "overall_status": "",
                "warnings_json": "",
                "exposure_note": "",
            }
        )
    return rows


def _warnings(details: list[dict], total: float) -> list[str]:
    warnings = []
    by_group = _sum_by(details, "group")
    by_type = _sum_by(details, "etf_type")
    if total > 0:
        for group, value in by_group.items():
            if value / total >= 0.60:
                warnings.append(f"{group} 占持仓市值 {value / total:.1%}，主题集中度偏高。")
        if by_type.get("high_beta", 0.0) / total >= 0.20:
            warnings.append("high_beta ETF 占比超过 20%，不宜继续同方向加仓。")
        if by_type.get("broad_index", 0.0) == 0:
            warnings.append("组合暂无宽基 ETF，波动可能更依赖行业/主题轮动。")
    for row in details:
        if str(row.get("data_health_status")) in {"提醒", "异常", "caution", "error"}:
            warnings.append(f"{row.get('symbol')} data_health={row.get('data_health_status')}，需保留复核标签。")
        if _float(row.get("position_ratio")) > 0.20:
            warnings.append(f"{row.get('symbol')} 超过单 ETF 20% 上限。")
    return warnings


def _overall_status(warnings: list[str]) -> str:
    if any("超过单 ETF" in item or "异常" in item for item in warnings):
        return "REVIEW"
    if warnings:
        return "CAUTION"
    return "NORMAL"


def _position_note(symbol: str, item: dict, pos: pd.Series) -> str:
    notes = [str(item.get("classification_reason") or "classification proxy")]
    if symbol == "515880":
        notes.append("证券公司ETF按 high_beta 处理，data_health caution 时禁止加仓")
    if str(pos.get("sell_review_status", "")).upper() in {"REVIEW", "REDUCE", "SELL"}:
        notes.append(f"sell_review={pos.get('sell_review_status')}")
    return "; ".join(notes)


def _fallback_group(name: object) -> str:
    text = str(name)
    if any(key in text for key in ["银行", "证券", "券商", "金融"]):
        return "金融地产"
    if any(key in text for key in ["煤炭", "有色", "钢铁", "资源", "能源"]):
        return "周期资源"
    return "其他"


def _sum_by(details: list[dict], field: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for row in details:
        key = str(row.get(field) or "unknown")
        values[key] = values.get(key, 0.0) + _float(row.get("market_value"))
    return values


def _read_positions() -> pd.DataFrame:
    if not POSITIONS_FILE.exists() or POSITIONS_FILE.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(POSITIONS_FILE, dtype=str, keep_default_na=False).fillna("")


def _read_classification() -> pd.DataFrame:
    if not CLASSIFICATION_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(CLASSIFICATION_FILE, dtype=str, keep_default_na=False).fillna("")


def _float(value: object) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if pd.isna(numeric):
        return 0.0
    return numeric


def _json_payload(df: pd.DataFrame, valuation_summary: dict) -> dict:
    clean_df = df.where(pd.notna(df), "")
    summary_df = df[df["row_type"] == "summary"].head(1)
    summary = summary_df.iloc[0].to_dict() if not summary_df.empty else {}
    warnings = []
    raw = summary.get("warnings_json", "")
    if raw:
        try:
            warnings = json.loads(raw)
        except Exception:
            warnings = [str(raw)]
    return {
        "summary": {key: ("" if pd.isna(value) else value) for key, value in summary.items()},
        "positions": clean_df[clean_df["row_type"] == "position"].to_dict(orient="records"),
        "buckets": clean_df[clean_df["row_type"].isin(["group", "etf_type", "risk_profile"])].to_dict(orient="records"),
        "warnings": warnings,
        "valuation": valuation_summary,
        "safety": {
            "broker_api": False,
            "real_order": False,
            "real_account": False,
            "paper_trades_modified": False,
            "paper_positions_modified": False,
        },
    }


if __name__ == "__main__":
    main()
