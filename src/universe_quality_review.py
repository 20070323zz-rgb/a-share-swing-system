"""Review ETF universe quality before building the formal backtest engine.

This script is read-only over market data and classification files. It writes
research/review reports only. It never touches broker APIs, paper trades, or
paper positions.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ETF_DAILY_DIR = DATA_DIR / "etf_daily"
REPORT_DIR = PROJECT_ROOT / "reports"
CLASSIFICATION_FILE = DATA_DIR / "etf_classification.csv"
WATCHLIST_FILE = PROJECT_ROOT / "watchlist.csv"
CANDIDATES_FILE = DATA_DIR / "etf_pool_expansion_candidates.csv"

OUTPUT_CSV = REPORT_DIR / "universe_quality_review.csv"
OUTPUT_MD = REPORT_DIR / "universe_quality_review.md"
STRATEGY_RESEARCH_MD = REPORT_DIR / "etf_rotation_strategy_research.md"
READINESS_MD = REPORT_DIR / "backtest_readiness_report.md"

MIN_BACKTEST_DAYS = 120
LOW_AMOUNT_THRESHOLD = 20_000_000.0
WATCH_AMOUNT_THRESHOLD = 50_000_000.0
ULTRA_LOW_AMOUNT_THRESHOLD = 5_000_000.0
HIGH_VOL_THRESHOLD = 0.45
EXTREME_VOL_THRESHOLD = 0.65


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    meta = load_metadata()
    rows, latest_data_date = build_quality_rows(meta)
    df = pd.DataFrame(rows).sort_values(["recommended_pool", "group", "symbol"]).reset_index(drop=True)
    df.to_csv(OUTPUT_CSV, index=False)
    summary = build_summary(df, latest_data_date)
    OUTPUT_MD.write_text(render_quality_report(df, summary), encoding="utf-8")
    STRATEGY_RESEARCH_MD.write_text(render_strategy_research_report(summary), encoding="utf-8")
    READINESS_MD.write_text(render_readiness_report(df, summary), encoding="utf-8")
    print(f"universe quality rows: {len(df)}")
    print(f"written: {OUTPUT_CSV}")
    print(f"written: {OUTPUT_MD}")
    print(f"written: {STRATEGY_RESEARCH_MD}")
    print(f"written: {READINESS_MD}")


def load_metadata() -> dict[str, dict]:
    meta: dict[str, dict] = {}
    for path, code_col, pool_col in [
        (CLASSIFICATION_FILE, "symbol", "pool"),
        (WATCHLIST_FILE, "code", "role"),
        (CANDIDATES_FILE, "code", "pool"),
    ]:
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path, dtype=str).fillna("")
        except Exception:
            continue
        for _, row in df.iterrows():
            code = extract_code(row.get(code_col, ""))
            if not code:
                continue
            item = meta.setdefault(code, {})
            for field in [
                "name",
                "group",
                "etf_type",
                "risk_profile",
                "holding_profile",
                "status",
                "classification_reason",
                "auto_buy_allowed",
                "qdii_check_required",
                "source_scope",
            ]:
                value = str(row.get(field, "") or "").strip()
                if value and not item.get(field):
                    item[field] = value
            pool = str(row.get(pool_col, "") or "").strip()
            if pool and not item.get("pool_current"):
                item["pool_current"] = pool
    return meta


def build_quality_rows(meta: dict[str, dict]) -> tuple[list[dict], str]:
    date_sets: dict[str, set[str]] = {}
    raw: dict[str, dict] = {}
    latest = ""
    for path in sorted(ETF_DAILY_DIR.glob("*.csv")):
        symbol = extract_code(path.stem)
        if not symbol:
            continue
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            raw[symbol] = {"symbol": symbol, "file": str(path), "read_error": str(exc)}
            continue
        if df.empty or "date" not in df.columns:
            raw[symbol] = {"symbol": symbol, "file": str(path), "read_error": "empty or missing date"}
            continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
        dates = set(df["date"].dt.strftime("%Y-%m-%d"))
        if dates:
            latest = max(latest, max(dates))
        raw[symbol] = {"symbol": symbol, "file": str(path), "df": df}
        date_sets[symbol] = dates

    master_dates = sorted(set().union(*date_sets.values())) if date_sets else []
    rows = []
    exposure_counter: Counter[str] = Counter()
    exposure_liquidity: dict[str, list[tuple[str, float]]] = {}
    first_pass: dict[str, dict] = {}

    for symbol, payload in raw.items():
        row = review_one(symbol, payload, meta.get(symbol, {}), master_dates, latest)
        first_pass[symbol] = row
        key = row["duplicate_exposure_group"]
        exposure_counter[key] += 1
        exposure_liquidity.setdefault(key, []).append((symbol, float(row["avg_amount_20d"] or 0)))

    exposure_rank: dict[str, dict[str, int]] = {}
    for key, values in exposure_liquidity.items():
        ranked = sorted(values, key=lambda item: item[1], reverse=True)
        exposure_rank[key] = {symbol: idx + 1 for idx, (symbol, _) in enumerate(ranked)}

    for symbol, row in first_pass.items():
        key = row["duplicate_exposure_group"]
        row["duplicate_count"] = exposure_counter[key]
        row["duplicate_liquidity_rank"] = exposure_rank.get(key, {}).get(symbol, 1)
        row["recommended_pool"], row["recommended_action"], row["review_reason"] = recommend_pool(row)
        rows.append(row)
    return rows, latest


def review_one(symbol: str, payload: dict, meta: dict, master_dates: list[str], latest_data_date: str) -> dict:
    read_error = payload.get("read_error", "")
    df = payload.get("df")
    name = meta.get("name") or symbol
    group = meta.get("group") or "unknown"
    etf_type = meta.get("etf_type") or "unknown"
    pool_current = normalize_pool(meta.get("pool_current") or "data_update")
    if read_error or df is None or df.empty:
        return base_row(symbol, name, etf_type, group, pool_current, latest_data_date, read_error or "invalid data")

    start_date = df["date"].min().strftime("%Y-%m-%d")
    end_date = df["date"].max().strftime("%Y-%m-%d")
    trading_days = int(len(df))
    date_values = set(df["date"].dt.strftime("%Y-%m-%d"))
    expected = [d for d in master_dates if start_date <= d <= end_date]
    missing_days = len([d for d in expected if d not in date_values])
    amount_col = "amount" if "amount" in df.columns else "money" if "money" in df.columns else ""
    volume_col = "volume" if "volume" in df.columns else ""
    close = pd.to_numeric(df.get("close"), errors="coerce")
    amount = pd.to_numeric(df[amount_col], errors="coerce") if amount_col else pd.Series(dtype=float)
    volume = pd.to_numeric(df[volume_col], errors="coerce") if volume_col else pd.Series(dtype=float)
    returns = close.pct_change(fill_method=None)
    vol_60 = float(returns.tail(60).std(skipna=True) * (252 ** 0.5)) if len(returns.dropna()) else 0.0
    avg_amount_20 = float(amount.tail(20).mean()) if not amount.empty else 0.0
    avg_amount_60 = float(amount.tail(60).mean()) if not amount.empty else 0.0
    avg_volume_20 = float(volume.tail(20).mean()) if not volume.empty else 0.0
    qdii = is_qdii(etf_type, group, name)
    classification_status = "unknown" if etf_type == "unknown" or group == "unknown" else "classified"
    data_length_status = "too_short" if trading_days < 60 else "short_history" if trading_days < MIN_BACKTEST_DAYS else "ok"
    liquidity_status = (
        "unknown"
        if avg_amount_20 <= 0
        else "ultra_low"
        if avg_amount_20 < ULTRA_LOW_AMOUNT_THRESHOLD
        else "low"
        if avg_amount_20 < LOW_AMOUNT_THRESHOLD
        else "watch"
        if avg_amount_20 < WATCH_AMOUNT_THRESHOLD
        else "ok"
    )
    volatility_status = "extreme_volatility" if vol_60 >= EXTREME_VOL_THRESHOLD else "high_volatility" if vol_60 >= HIGH_VOL_THRESHOLD else "normal"
    exposure_key = f"{etf_type}:{group}"
    return {
        "symbol": symbol,
        "name": name,
        "etf_type": etf_type,
        "group": group,
        "pool_current": pool_current,
        "recommended_pool": "",
        "start_date": start_date,
        "end_date": end_date,
        "trading_days": trading_days,
        "missing_days": missing_days,
        "latest_data_date": latest_data_date,
        "is_latest_to_unified_date": end_date == latest_data_date,
        "avg_amount_20d": round(avg_amount_20, 2),
        "avg_amount_60d": round(avg_amount_60, 2),
        "avg_volume_20d": round(avg_volume_20, 2),
        "data_length_status": data_length_status,
        "liquidity_status": liquidity_status,
        "classification_status": classification_status,
        "qdii_flag": bool(qdii),
        "volatility_60d_annualized": round(vol_60, 6),
        "volatility_status": volatility_status,
        "duplicate_exposure_group": exposure_key,
        "duplicate_count": 0,
        "duplicate_liquidity_rank": 0,
        "recommended_action": "",
        "review_reason": "",
    }


def base_row(symbol: str, name: str, etf_type: str, group: str, pool_current: str, latest_data_date: str, reason: str) -> dict:
    return {
        "symbol": symbol,
        "name": name,
        "etf_type": etf_type,
        "group": group,
        "pool_current": pool_current,
        "recommended_pool": "exclude_pool",
        "start_date": "",
        "end_date": "",
        "trading_days": 0,
        "missing_days": 0,
        "latest_data_date": latest_data_date,
        "is_latest_to_unified_date": False,
        "avg_amount_20d": 0.0,
        "avg_amount_60d": 0.0,
        "avg_volume_20d": 0.0,
        "data_length_status": "invalid",
        "liquidity_status": "unknown",
        "classification_status": "unknown" if etf_type == "unknown" else "classified",
        "qdii_flag": is_qdii(etf_type, group, name),
        "volatility_60d_annualized": 0.0,
        "volatility_status": "unknown",
        "duplicate_exposure_group": f"{etf_type}:{group}",
        "duplicate_count": 0,
        "duplicate_liquidity_rank": 0,
        "recommended_action": "exclude_until_fixed",
        "review_reason": reason,
    }


def recommend_pool(row: dict) -> tuple[str, str, str]:
    reasons: list[str] = []
    if not row["is_latest_to_unified_date"]:
        reasons.append("not_latest_to_unified_date")
    if row["data_length_status"] in {"invalid", "too_short"}:
        reasons.append(row["data_length_status"])
    if row["data_length_status"] == "short_history":
        reasons.append("history_lt_120d")
    if row["liquidity_status"] in {"unknown", "ultra_low"}:
        reasons.append(f"liquidity_{row['liquidity_status']}")
    elif row["liquidity_status"] == "low":
        reasons.append("liquidity_low")
    if row["classification_status"] == "unknown":
        reasons.append("classification_unknown")
    if row["qdii_flag"]:
        reasons.append("qdii_needs_premium_fx_calendar_check")
    if row["volatility_status"] == "extreme_volatility":
        reasons.append("extreme_volatility")
    elif row["volatility_status"] == "high_volatility":
        reasons.append("high_volatility")
    if row.get("duplicate_count", 0) >= 6 and row.get("duplicate_liquidity_rank", 99) > 3:
        reasons.append("duplicate_exposure_lower_liquidity")

    hard_exclude = {
        "invalid",
        "too_short",
        "liquidity_unknown",
        "liquidity_ultra_low",
        "not_latest_to_unified_date",
    }
    if any(reason in hard_exclude for reason in reasons):
        return "exclude_pool", "exclude_before_backtest", "; ".join(reasons)
    if row["data_length_status"] == "short_history" or row["qdii_flag"] or row["classification_status"] == "unknown":
        return "observe_pool", "observe_only_before_backtest", "; ".join(reasons)
    if row["liquidity_status"] == "low" or row["volatility_status"] in {"high_volatility", "extreme_volatility"}:
        return "observe_pool", "observe_or_small_weight_only", "; ".join(reasons)
    if "duplicate_exposure_lower_liquidity" in reasons:
        return "observe_pool", "keep_best_liquidity_peer_in_trade_pool", "; ".join(reasons)
    return "trade_pool", "eligible_for_phase4a_backtest", "; ".join(reasons) or "history/liquidity/classification pass"


def build_summary(df: pd.DataFrame, latest_data_date: str) -> dict:
    pool_counts = df["recommended_pool"].value_counts().to_dict()
    type_counts = df["etf_type"].value_counts().to_dict()
    group_counts = df["group"].value_counts().to_dict()
    summary = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_etf": int(len(df)),
        "latest_data_date": latest_data_date,
        "recommended_trade_pool": int(pool_counts.get("trade_pool", 0)),
        "recommended_observe_pool": int(pool_counts.get("observe_pool", 0)),
        "recommended_exclude_pool": int(pool_counts.get("exclude_pool", 0)),
        "low_liquidity_count": int(df["liquidity_status"].isin(["low", "ultra_low", "unknown"]).sum()),
        "short_history_count": int(df["data_length_status"].isin(["too_short", "short_history"]).sum()),
        "qdii_count": int(df["qdii_flag"].sum()),
        "unknown_classification_count": int((df["classification_status"] == "unknown").sum()),
        "not_latest_count": int((~df["is_latest_to_unified_date"]).sum()),
        "high_volatility_count": int(df["volatility_status"].isin(["high_volatility", "extreme_volatility"]).sum()),
        "type_distribution": type_counts,
        "group_distribution": group_counts,
    }
    summary["backtest_ready"] = summary["recommended_trade_pool"] >= 30 and summary["not_latest_count"] == 0
    summary["readiness_summary"] = (
        f"183 ETF data pool can support a Phase 4A first-pass ETF rotation backtest if the engine uses the "
        f"recommended trade_pool only ({summary['recommended_trade_pool']} ETFs) and excludes/observes short-history, "
        f"unknown-classification, QDII and low-liquidity ETFs. Use latest available close date {latest_data_date}; "
        "do not force 2026-06-18 before the data source publishes it."
    )
    return summary


def render_quality_report(df: pd.DataFrame, summary: dict) -> str:
    lines = [
        f"# ETF Universe Quality Review {summary['generated_at']}",
        "",
        "本报告只读取本地 ETF CSV、watchlist 和分类文件；不接券商 API，不下单，不修改模拟持仓。",
        "",
        "## 摘要",
        f"- ETF 文件数量：{summary['total_etf']}",
        f"- 最新统一数据日：{summary['latest_data_date']}",
        f"- 推荐 trade_pool：{summary['recommended_trade_pool']}",
        f"- 推荐 observe_pool：{summary['recommended_observe_pool']}",
        f"- 推荐 exclude_pool：{summary['recommended_exclude_pool']}",
        f"- 低流动性/未知流动性数量：{summary['low_liquidity_count']}",
        f"- 历史不足数量：{summary['short_history_count']}",
        f"- QDII 数量：{summary['qdii_count']}",
        f"- unknown 分类数量：{summary['unknown_classification_count']}",
        f"- 高波动数量：{summary['high_volatility_count']}",
        f"- 是否支持 Phase 4A 第一版回测：{'是' if summary['backtest_ready'] else '谨慎，需先按推荐池过滤'}",
        "",
        "## 类型分布",
        *[f"- {k}: {v}" for k, v in sorted(summary["type_distribution"].items(), key=lambda item: (-item[1], item[0]))],
        "",
        "## Group 分布",
        *[f"- {k}: {v}" for k, v in sorted(summary["group_distribution"].items(), key=lambda item: (-item[1], item[0]))],
        "",
        "## 需要人工复核的 ETF 样例",
    ]
    review_cols = ["symbol", "name", "etf_type", "group", "pool_current", "recommended_pool", "avg_amount_20d", "trading_days", "review_reason"]
    review_rows = df[df["recommended_pool"].isin(["observe_pool", "exclude_pool"])].head(60)
    lines.extend(markdown_table(review_rows[review_cols]))
    lines.extend([
        "",
        "## 推荐 trade_pool 样例",
    ])
    trade_cols = ["symbol", "name", "etf_type", "group", "avg_amount_20d", "trading_days", "duplicate_exposure_group", "duplicate_liquidity_rank"]
    trade_rows = df[df["recommended_pool"] == "trade_pool"].sort_values("avg_amount_20d", ascending=False).head(60)
    lines.extend(markdown_table(trade_rows[trade_cols]))
    lines.extend([
        "",
        "## 判断规则",
        f"- 数据少于 {MIN_BACKTEST_DAYS} 个交易日：不进入第一版自动交易回测池。",
        f"- 近 20 日平均成交额低于 {LOW_AMOUNT_THRESHOLD:,.0f} 元：不进入 trade_pool。",
        "- QDII：先进入 observe_pool，等待溢价、汇率、海外交易日检查。",
        "- unknown 分类：先进入 observe_pool，等待人工分类。",
        "- 高度重复暴露：优先保留同暴露中流动性靠前的 ETF。",
        "- 极端波动或数据非最新：进入 observe/exclude，避免污染第一版回测。",
    ])
    return "\n".join(lines) + "\n"


def render_strategy_research_report(summary: dict) -> str:
    return f"""# ETF Rotation Strategy Research

Generated at: {summary['generated_at']}

本报告是回测前研究材料，不是最终交易规则；不修改 BUY ranking、仓位规则或模拟持仓。

## 主流 ETF 轮动框架

1. **动量/相对强弱轮动**：常见做法是在 ETF 池中选择过去一段时间表现更强的少数 ETF，并定期再平衡。Quantpedia 的 sector momentum 示例使用行业 ETF，选择 12 个月动量最强的 3 只并月度调仓，说明“Top N + 定期再平衡”是经典框架之一。来源：https://quantpedia.com/strategies/sector-momentum-rotational-system

2. **趋势 + 相对强弱二维观察**：State Street 的 Sector ETF Momentum Map 用相对强弱趋势和动量两个维度观察行业轮动，支持“横截面对比 + 趋势过滤”的思路。来源：https://www.ssga.com/dk/en_gb/intermediary/insights/sector-etf-momentum-map

3. **经济周期/行业轮动**：Investopedia 对 sector rotation 的说明强调用行业 ETF 承接经济周期、日历效应或地域机会，但也提示时点判断和交易成本会影响有效性。来源：https://www.investopedia.com/articles/exchangetradedfunds/08/sector-rotation.asp

4. **流动性和交易质量过滤**：BlackRock/iShares ETF 尽调框架把 exposure、structure、performance、liquidity 等作为 ETF 选择要素，说明 ETF 池构建不能只看收益。来源：https://www.blackrock.com/sg/en/ishares/education/choosing-the-right-etf

5. **A 股交易单位约束**：上交所 ETF FAQ 明确 ETF 买卖最低 1 手，即 100 份，最小价格变动单位 0.001 元；A 股股票 ETF 通常 T+1，债券/黄金/跨境/货币等部分品种支持 T+0。来源：https://www.sse.com.cn/assortment/fund/etf/question/

6. **QDII 溢价风险**：证券时报报道 2026 年多只 QDII 基金密集提示二级市场溢价风险，说明跨境 ETF 不能只用日线价格动量自动买入。来源：https://www.stcn.com/article/detail/3650684.html

## 回测前常见风险

- 幸存者偏差：当前 183 只多来自现存正式数据文件，不能代表历史任意时点可交易 ETF 池。
- 新基金样本不足：少于 120 个交易日的 ETF 不应进入第一版交易回测。
- 低流动性：成交额过低会放大冲击成本、滑点和成交不确定性。
- 交易成本：当前项目已有佣金、最低佣金、滑点、100 份整数倍，应进入回测。
- QDII 溢价：QDII 需额外加入 IOPV/溢价、汇率、海外交易日和申赎状态检查。
- 重复暴露：同一指数/主题多个 ETF 会让横截面排名看似分散，实际是同一风险源。
- 数据源差异：JQData/BaoStock 的复权、成交额口径需保持一致。

## 当前策略适合的回测方式

- 日频，收盘后生成信号。
- 第一版只做 ETF，不做个股。
- 最多持有 3 只。
- 单只不超过模拟本金 20%。
- 交易成本包含佣金 0.00012、最低佣金 5 元、滑点 0.0003、100 份整数倍。
- QDII 暂不自动买入。
- market_state 先展示，不直接改变仓位。
- 比较 original ranking 与 adjusted preview，但 adjusted preview 暂不进入真实模拟交易规则。

## 当前策略不适合做什么

- 不适合高频或日内。
- 不适合全市场个股 alpha。
- 不适合复杂机器学习主策略直接上线。
- 不适合对 QDII 做无溢价检查的自动交易。
- 不适合用全 183 只不加过滤直接回测。
"""


def render_readiness_report(df: pd.DataFrame, summary: dict) -> str:
    trade = df[df["recommended_pool"] == "trade_pool"]
    observe = df[df["recommended_pool"] == "observe_pool"]
    exclude = df[df["recommended_pool"] == "exclude_pool"]
    lines = [
        f"# Backtest Readiness Report {summary['generated_at']}",
        "",
        "本报告用于决定是否进入 Phase 4A 回测引擎开发；不修改交易规则，不修改模拟持仓。",
        "",
        "## 结论",
        f"- 当前 183 只 ETF 是否够第一版回测：{'够，但必须过滤' if len(trade) >= 30 else '不足，需要先补数据/筛池'}",
        f"- 推荐 trade_pool 数量：{len(trade)}",
        f"- 推荐 observe_pool 数量：{len(observe)}",
        f"- 推荐 exclude_pool 数量：{len(exclude)}",
        f"- 最新可用数据日：{summary['latest_data_date']}",
        f"- 是否可以进入 Phase 4A：{'可以，前提是使用推荐 trade_pool 并保留风险过滤' if summary['backtest_ready'] else '暂缓，先处理数据或池质量问题'}",
        "",
        "## 回测前必须处理的风险",
        f"1. 幸存者偏差：当前池来自现有 ETF 文件，第一版可做策略验证，但报告必须标注 survivorship bias。",
        f"2. QDII：{summary['qdii_count']} 只应先剔出自动交易池，等待溢价/汇率/海外交易日检查。",
        f"3. unknown 分类：{summary['unknown_classification_count']} 只需人工分类，否则只观察。",
        f"4. 低流动性：{summary['low_liquidity_count']} 只低流动性/未知流动性 ETF 不适合第一版交易池。",
        f"5. 历史不足：{summary['short_history_count']} 只历史不足 ETF 不应用于估计稳定参数。",
        "6. 重复暴露：同主题多个 ETF 要优先保留流动性更好的标的。",
        "",
        "## 第一版回测建议",
        "- 使用推荐 trade_pool，不直接使用全 183 只。",
        "- 交易口径：日线收盘后生成信号，下一交易日 close proxy 或 next open proxy 二选一；第一版建议先用 next close/close proxy 并明确偏差。",
        "- 加入佣金、最低佣金、滑点、100 份整数倍。",
        "- 最大持仓 3 只，单只不超过 20%。",
        "- QDII、unknown、短历史、低流动性标的不进入自动买入池。",
        "- 比较策略：original ranking、adjusted preview、沪深300 ETF buy-and-hold、现金基准。",
        "- market_state 先作为报告分组维度，不直接控制仓位。",
        "",
        "## 推荐 trade_pool 列表",
    ]
    lines.extend(markdown_table(trade[["symbol", "name", "etf_type", "group", "avg_amount_20d", "trading_days", "review_reason"]].head(120)))
    lines.extend(["", "## 推荐 observe_pool 样例"])
    lines.extend(markdown_table(observe[["symbol", "name", "etf_type", "group", "avg_amount_20d", "trading_days", "review_reason"]].head(120)))
    lines.extend(["", "## 推荐 exclude_pool 样例"])
    lines.extend(markdown_table(exclude[["symbol", "name", "etf_type", "group", "avg_amount_20d", "trading_days", "review_reason"]].head(120)))
    return "\n".join(lines) + "\n"


def markdown_table(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["- 无"]
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        values = [format_cell(row.get(col, "")) for col in cols]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def format_cell(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value).replace("|", "/").replace("\n", " ")


def normalize_pool(value: str) -> str:
    text = str(value or "").strip()
    if text in {"trade_pool", "observe_pool", "research_only", "exclude_pool"}:
        return text
    if text == "data_update":
        return "data_update"
    return text or "unknown"


def is_qdii(etf_type: str, group: str, name: str) -> bool:
    text = f"{etf_type} {group} {name}".lower()
    keywords = ["qdii", "跨境", "港股", "恒生", "纳指", "标普", "日经", "德国", "印度", "中概"]
    return any(keyword.lower() in text for keyword in keywords)


def extract_code(value: object) -> str:
    match = re.search(r"(\d{6})", str(value))
    return match.group(1) if match else ""


if __name__ == "__main__":
    main()
