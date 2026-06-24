"""Research-only market state snapshot for the ETF paper system."""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from config import DATA_DIR, ETF_DAILY_DIR, REPORT_DIR
from data_loader import load_price_data


CSV_FILE = REPORT_DIR / "market_state.csv"
REPORT_FILE = REPORT_DIR / "market_state_report.md"
BUY_RANKING_FILE = REPORT_DIR / "buy_signal_ranking.md"
DATA_HEALTH_FILE = REPORT_DIR / "latest_data_health.md"

BROAD_CODES = {
    "510300": "沪深300",
    "510500": "中证500",
    "512100": "中证1000",
    "159915": "创业板",
    "588000": "科创50",
    "510050": "上证50",
    "510180": "上证180",
    "159901": "深100",
    "159949": "创业板50",
    "159338": "A500",
}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_market_rows()
    df = pd.DataFrame(rows)
    df.to_csv(CSV_FILE, index=False)
    REPORT_FILE.write_text(render_report(df), encoding="utf-8")
    print(f"market_state rows: {len(df)}")
    print(f"written: {CSV_FILE}")
    print(f"written: {REPORT_FILE}")


def build_market_rows() -> list[dict]:
    component_rows = []
    for code, name in BROAD_CODES.items():
        prices, error = load_price_data(ETF_DAILY_DIR, code)
        if error or prices is None or len(prices) < 80:
            continue
        component_rows.append(_component_row(code, name, prices))
    summary = _summary_row(component_rows)
    return [summary] + component_rows


def _component_row(code: str, name: str, prices: pd.DataFrame) -> dict:
    df = prices.sort_values("date").copy()
    close = pd.to_numeric(df["close"], errors="coerce")
    latest = close.iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1]
    ret20 = latest / close.shift(20).iloc[-1] - 1 if close.shift(20).iloc[-1] else 0.0
    ret60 = latest / close.shift(60).iloc[-1] - 1 if close.shift(60).iloc[-1] else 0.0
    vol20 = close.pct_change().rolling(20).std().iloc[-1]
    drawdown60 = latest / close.rolling(60).max().iloc[-1] - 1 if close.rolling(60).max().iloc[-1] else 0.0
    trend_score = _clip(50 + (latest / ma60 - 1) * 250 + (ma20 / ma60 - 1) * 200, 0, 100)
    momentum_score = _clip(50 + ret20 * 350 + ret60 * 180, 0, 100)
    risk_score = _clip(100 + drawdown60 * 600 - max(vol20 - 0.015, 0) * 800, 0, 100)
    component_score = 0.45 * trend_score + 0.35 * momentum_score + 0.20 * risk_score
    return {
        "row_type": "component",
        "symbol": code,
        "name": name,
        "date": str(pd.to_datetime(df["date"].iloc[-1]).date()),
        "market_state": "",
        "market_score": round(component_score, 2),
        "trend_score": round(trend_score, 2),
        "momentum_score": round(momentum_score, 2),
        "risk_score": round(risk_score, 2),
        "ret20": round(float(ret20), 6),
        "ret60": round(float(ret60), 6),
        "vol20": round(float(vol20), 6),
        "drawdown60": round(float(drawdown60), 6),
        "buy_count": "",
        "risk_alert_count": "",
        "position_ratio": "",
        "suggested_total_position_min": "",
        "suggested_total_position_max": "",
        "evidence_level": "proxy",
        "note": "本地宽基价格代理，不使用未来数据生成当天信号。",
    }


def _summary_row(component_rows: list[dict]) -> dict:
    scores = [float(row["market_score"]) for row in component_rows]
    trend_scores = [float(row["trend_score"]) for row in component_rows]
    momentum_scores = [float(row["momentum_score"]) for row in component_rows]
    risk_scores = [float(row["risk_score"]) for row in component_rows]
    date = max([row["date"] for row in component_rows], default="")
    market_score = sum(scores) / len(scores) if scores else 0.0
    buy_count = _buy_count()
    risk_alert_count = _risk_alert_count()
    position_ratio = _current_position_ratio()
    adjustment = min(buy_count * 1.5, 8.0) - min(risk_alert_count * 5.0, 15.0)
    final_score = _clip(market_score + adjustment, 0, 100)
    state, low, high = _state_and_range(final_score)
    return {
        "row_type": "summary",
        "symbol": "MARKET",
        "name": "A股ETF市场状态",
        "date": date,
        "market_state": state,
        "market_score": round(final_score, 2),
        "trend_score": round(sum(trend_scores) / len(trend_scores), 2) if trend_scores else 0,
        "momentum_score": round(sum(momentum_scores) / len(momentum_scores), 2) if momentum_scores else 0,
        "risk_score": round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else 0,
        "ret20": "",
        "ret60": "",
        "vol20": "",
        "drawdown60": "",
        "buy_count": buy_count,
        "risk_alert_count": risk_alert_count,
        "position_ratio": round(position_ratio, 6),
        "suggested_total_position_min": low,
        "suggested_total_position_max": high,
        "evidence_level": "research_proxy",
        "note": "市场状态仅用于研究和看板，不自动修改仓位规则。",
    }


def render_report(df: pd.DataFrame) -> str:
    summary = df[df["row_type"] == "summary"].head(1)
    if summary.empty:
        state = "unknown"
        score = 0
        low = high = 0
        date = ""
    else:
        row = summary.iloc[0]
        state = row["market_state"]
        score = row["market_score"]
        low = row["suggested_total_position_min"]
        high = row["suggested_total_position_max"]
        date = row["date"]
    lines = [
        "# 市场状态研究报告",
        "",
        "本报告只做模型研究和看板展示，不修改交易规则、不自动买卖、不接券商 API。",
        "",
        "## 摘要",
        f"- 最新数据日：{date}",
        f"- market_state：{state}",
        f"- market_score：{score}",
        f"- 建议总仓位研究区间：{float(low):.0%} - {float(high):.0%}",
        "",
        "## 组成宽基代理",
        "| symbol | name | market_score | trend | momentum | risk | ret20 | ret60 | vol20 | drawdown60 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    components = df[df["row_type"] == "component"].copy()
    if components.empty:
        lines.append("|  | 无可用宽基代理 |  |  |  |  |  |  |  |  |")
    else:
        for _, row in components.sort_values("market_score", ascending=False).iterrows():
            lines.append(
                f"| {row['symbol']} | {row['name']} | {float(row['market_score']):.2f} | {float(row['trend_score']):.2f} | "
                f"{float(row['momentum_score']):.2f} | {float(row['risk_score']):.2f} | {_pct(row['ret20'])} | {_pct(row['ret60'])} | "
                f"{_pct(row['vol20'])} | {_pct(row['drawdown60'])} |"
            )
    lines += [
        "",
        "## 解释边界",
        "- market_strong：研究建议总仓位 40%-60%。",
        "- market_neutral：研究建议总仓位 20%-40%。",
        "- market_weak：研究建议总仓位 0%-20%。",
        "- risk_off：研究建议总仓位 0%-10%。",
        "- 本报告不改变现有 BUY ranking、卖出复核和模拟交易引擎规则。",
    ]
    return "\n".join(lines)


def _buy_count() -> int:
    rows = _read_markdown_table(BUY_RANKING_FILE, "Top BUY Ranking")
    return sum(1 for row in rows if row.get("进入模拟买入候选") == "是" or row.get("candidate_action") == "candidate")


def _risk_alert_count() -> int:
    if not DATA_HEALTH_FILE.exists():
        return 0
    text = DATA_HEALTH_FILE.read_text(encoding="utf-8")
    count = 0
    for key in ["异常", "提醒"]:
        match = re.search(rf"- {key}[：:]\s*(\d+)", text)
        if match:
            count += int(match.group(1))
    return count


def _current_position_ratio() -> float:
    path = DATA_DIR / "paper_positions.csv"
    if not path.exists():
        return 0.0
    try:
        df = pd.read_csv(path, keep_default_na=False)
    except Exception:
        return 0.0
    if "market_value" not in df.columns:
        return 0.0
    return float(pd.to_numeric(df["market_value"], errors="coerce").fillna(0).sum()) / 10000.0


def _state_and_range(score: float) -> tuple[str, float, float]:
    if score >= 70:
        return "market_strong", 0.40, 0.60
    if score >= 45:
        return "market_neutral", 0.20, 0.40
    if score >= 25:
        return "market_weak", 0.00, 0.20
    return "risk_off", 0.00, 0.10


def _read_markdown_table(path: Path, section_title: str) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    table: list[str] = []
    for line in lines:
        if line.strip().startswith("## "):
            in_section = section_title in line
            continue
        if in_section and line.strip().startswith("|"):
            table.append(line)
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


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _pct(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric):
        return ""
    return f"{numeric:.2%}"


if __name__ == "__main__":
    main()
