"""Read-only Streamlit dashboard for the paper ETF system.

The dashboard only reads local CSV/Markdown reports. It does not connect to
broker APIs, place orders, save credentials, or modify trading rules.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = PROJECT_ROOT / "reports"


def main() -> None:
    st.set_page_config(page_title="ETF 模拟盘看板", layout="wide")
    st.title("ETF 模拟盘只读看板")
    st.caption("只读取本地模拟盘与报告文件；不接券商 API，不真实下单，不保存账号密码。")

    positions = _read_csv(DATA_DIR / "paper_positions.csv")
    trades = _read_csv(DATA_DIR / "paper_trades.csv")
    ranking = _read_ranking_report()
    latest_date = _latest_data_date()

    summary = _portfolio_summary(positions, trades)
    cols = st.columns(6)
    cols[0].metric("模拟总资产", _money(summary["total_equity"]))
    cols[1].metric("现金", _money(summary["cash"]))
    cols[2].metric("持仓市值", _money(summary["market_value"]))
    cols[3].metric("累计盈亏", _money(summary["total_pnl"]))
    cols[4].metric("持仓 ETF 数量", str(summary["position_count"]))
    cols[5].metric("最新数据日期", latest_date)

    tab_positions, tab_signals, tab_trades, tab_health, tab_risk = st.tabs(["持仓", "今日信号", "交易记录", "数据健康", "风险提示"])

    with tab_positions:
        st.subheader("当前持仓")
        if positions.empty:
            st.info("当前无模拟持仓。")
        else:
            st.dataframe(_display_positions(positions), use_container_width=True, hide_index=True)

    with tab_signals:
        st.subheader("BUY Ranking")
        if ranking:
            st.markdown(ranking)
        else:
            st.info("暂无 BUY ranking 报告。")

    with tab_trades:
        st.subheader("模拟交易记录")
        if trades.empty:
            st.info("暂无模拟交易记录。")
        else:
            st.dataframe(trades, use_container_width=True, hide_index=True)

    with tab_health:
        st.subheader("数据覆盖 / 数据健康")
        st.markdown(_read_text(REPORT_DIR / "latest_data_coverage.md") or "暂无覆盖报告。")
        st.divider()
        st.markdown(_read_text(REPORT_DIR / "latest_data_health.md") or "暂无健康报告。")

    with tab_risk:
        st.subheader("风险提示")
        st.markdown(_risk_text(positions, summary))
        st.divider()
        st.markdown(_read_text(REPORT_DIR / "first_paper_buy_plan.md") or "暂无首次模拟买入计划。")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str).fillna("")


def _read_text(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return ""
    return path.read_text(encoding="utf-8")


def _read_ranking_report() -> str:
    return _read_text(REPORT_DIR / "buy_signal_ranking.md") or _read_text(REPORT_DIR / "latest_buy_ranking.md")


def _latest_data_date() -> str:
    latest = ""
    for path in (DATA_DIR / "etf_daily").glob("*.csv"):
        try:
            df = pd.read_csv(path, usecols=["date"])
        except Exception:
            continue
        if not df.empty:
            latest = max(latest, str(df["date"].max()))
    return latest or "unknown"


def _portfolio_summary(positions: pd.DataFrame, trades: pd.DataFrame) -> dict:
    market_value = _sum_col(positions, "market_value")
    cost = _sum_col(positions, "cost")
    cash = _latest_trade_value(trades, "simulated_cash", fallback=10000.0 - cost)
    total_equity = _latest_trade_value(trades, "total_equity", fallback=cash + market_value)
    return {
        "cash": cash,
        "market_value": market_value,
        "total_equity": total_equity,
        "total_pnl": total_equity - 10000.0,
        "position_count": len(positions),
    }


def _display_positions(positions: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "symbol",
        "name",
        "cost",
        "entry_price",
        "current_price",
        "market_value",
        "unrealized_pnl",
        "unrealized_pnl_pct",
        "unrealized_return",
        "reason",
        "holding_days",
    ]
    existing = [col for col in cols if col in positions.columns]
    return positions[existing].copy()


def _risk_text(positions: pd.DataFrame, summary: dict) -> str:
    lines = [
        "- 网页为只读展示，不提供真实买入/卖出按钮。",
        f"- 当前仓位比例：{summary['market_value'] / summary['total_equity']:.2%}" if summary["total_equity"] else "- 当前仓位比例：0.00%",
        "- 单 ETF 模拟上限：2000 元。",
    ]
    if positions.empty:
        lines.append("- 当前无持仓超限风险。")
    else:
        values = pd.to_numeric(positions.get("market_value", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
        over = positions.loc[values > 2000, "symbol"].astype(str).tolist() if "symbol" in positions else []
        lines.append(f"- 单 ETF 超限：{', '.join(over) if over else '无'}")
        risk_alerts = positions.get("risk_alert", pd.Series(dtype=str)).fillna("").astype(str)
        lines.append(f"- 持仓风险提醒：{int((risk_alerts.str.len() > 0).sum())}")
    lines.append("- QDII/跨境溢价风险仅做报告提示，未接入实时溢价数据。")
    return "\n".join(lines)


def _latest_trade_value(trades: pd.DataFrame, col: str, fallback: float) -> float:
    if trades.empty or col not in trades.columns:
        return float(fallback)
    values = pd.to_numeric(trades[col], errors="coerce").dropna()
    return float(values.iloc[-1]) if not values.empty else float(fallback)


def _sum_col(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0.0).sum())


def _money(value: float) -> str:
    return f"{value:,.2f}"


if __name__ == "__main__":
    main()
