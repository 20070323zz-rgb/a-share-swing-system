"""Create research-only ETF rotation exit-rule candidate library.

The output is a parameter framework for future backtests. Nothing in this file
is connected to paper_trade_engine or live execution.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "reports"
VOL_PROFILE_CSV = REPORT_DIR / "etf_volatility_profile.csv"

EXIT_RESEARCH_MD = REPORT_DIR / "etf_rotation_exit_rule_research.md"
CANDIDATES_MD = REPORT_DIR / "exit_rule_candidates.md"
CANDIDATES_JSON = REPORT_DIR / "exit_rule_candidates.json"
BY_TYPE_MD = REPORT_DIR / "exit_rule_by_etf_type.md"
BACKTEST_DESIGN_MD = REPORT_DIR / "exit_rule_backtest_design.md"


SOURCE_LINKS = [
    {
        "name": "Quantpedia sector momentum rotational system",
        "url": "https://quantpedia.com/strategies/sector-momentum-rotational-system",
        "note": "行业/ETF 动量轮动的 Top-N + 定期再平衡框架参考。",
    },
    {
        "name": "State Street sector ETF momentum map",
        "url": "https://www.ssga.com/dk/en_gb/intermediary/insights/sector-etf-momentum-map",
        "note": "用相对强弱和动量观察行业 ETF 轮动。",
    },
    {
        "name": "CME Group: ATR",
        "url": "https://www.cmegroup.com/education/courses/technical-analysis/understanding-average-true-range-indicator.html",
        "note": "ATR 是波动率/真实波幅工具，适合做跨品种波动自适应止损研究。",
    },
    {
        "name": "Investopedia trailing stop",
        "url": "https://www.investopedia.com/terms/t/trailingstop.asp",
        "note": "移动止损/移动止盈的基础定义和风险提示。",
    },
    {
        "name": "BlackRock/iShares ETF selection",
        "url": "https://www.blackrock.com/sg/en/ishares/education/choosing-the-right-etf",
        "note": "ETF 选择应考虑流动性、结构、表现和交易质量。",
    },
    {
        "name": "SSE ETF FAQ",
        "url": "https://www.sse.com.cn/assortment/fund/etf/question/",
        "note": "A 股 ETF 交易单位和交易机制约束参考。",
    },
]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    vol_df = read_vol_profile()
    type_summary = build_type_summary(vol_df)
    candidates = build_candidates(type_summary)
    CANDIDATES_JSON.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    CANDIDATES_MD.write_text(render_candidates_report(candidates), encoding="utf-8")
    EXIT_RESEARCH_MD.write_text(render_exit_research_report(), encoding="utf-8")
    BY_TYPE_MD.write_text(render_by_type_report(type_summary, candidates), encoding="utf-8")
    BACKTEST_DESIGN_MD.write_text(render_backtest_design_report(), encoding="utf-8")
    print(f"exit rule families: {len(candidates['rule_families'])}")
    print(f"written: {EXIT_RESEARCH_MD}")
    print(f"written: {CANDIDATES_MD}")
    print(f"written: {CANDIDATES_JSON}")
    print(f"written: {BY_TYPE_MD}")
    print(f"written: {BACKTEST_DESIGN_MD}")


def read_vol_profile() -> pd.DataFrame:
    if not VOL_PROFILE_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(VOL_PROFILE_CSV)


def build_type_summary(df: pd.DataFrame) -> dict[str, dict]:
    if df.empty:
        return {}
    rows: dict[str, dict] = {}
    ok = df[df.get("read_status", "ok") == "ok"].copy()
    for etf_type, sub in ok.groupby("etf_type"):
        rows[str(etf_type)] = {
            "count": int(len(sub)),
            "avg_annualized_volatility": safe_float(sub["annualized_volatility"].mean()),
            "median_annualized_volatility": safe_float(sub["annualized_volatility"].median()),
            "avg_max_drawdown": safe_float(sub["max_drawdown"].mean()),
            "median_atr_14_pct": safe_float(sub["atr_14_pct"].median()),
            "p75_atr_14_pct": safe_float(sub["atr_14_pct"].quantile(0.75)),
            "p90_atr_14_pct": safe_float(sub["atr_14_pct"].quantile(0.90)),
        }
    return rows


def build_candidates(type_summary: dict[str, dict]) -> dict:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    rule_families = [
        {
            "family": "fixed_stop_fixed_take_profit",
            "label": "Fixed Stop / Fixed Take Profit",
            "execution_enabled": False,
            "parameters": {
                "stop_loss_pct": [-0.03, -0.05, -0.08, -0.10],
                "take_profit_pct": [0.05, 0.08, 0.12, 0.15],
            },
            "fit_for_etf_rotation": "baseline only",
            "risk": "固定百分比容易忽略 ETF 类型差异，可能过拟合，也可能过早止盈卖飞。",
            "backtest_note": "作为 baseline，不建议直接作为最终规则。",
        },
        {
            "family": "fixed_stop_trailing_take_profit",
            "label": "Fixed Stop + Trailing Take Profit",
            "execution_enabled": False,
            "parameters": {
                "profit_protection_start_pct": [0.03, 0.05, 0.08],
                "trailing_drawdown_pct": [0.025, 0.03, 0.04, 0.05, 0.06],
            },
            "fit_for_etf_rotation": "good candidate for sector/theme ETF",
            "risk": "趋势强时较适合保护利润，但震荡市容易被洗出。",
            "backtest_note": "重点观察 profit giveback 和 whipsaw count。",
        },
        {
            "family": "atr_stop_atr_trailing",
            "label": "ATR Stop + ATR Trailing",
            "execution_enabled": False,
            "parameters": {
                "atr_window": [14, 20],
                "initial_stop_atr_multiple": [1.5, 2.0, 2.5, 3.0],
                "trailing_stop_atr_multiple": [1.5, 2.0, 2.5, 3.0],
            },
            "fit_for_etf_rotation": "strong candidate",
            "risk": "ATR 参数太多，需防止按历史噪声调参。",
            "backtest_note": "适合作为跨 ETF 类型的波动自适应退出规则。",
        },
        {
            "family": "trend_breakdown_exit",
            "label": "Trend Breakdown Exit",
            "execution_enabled": False,
            "parameters": {"ma_break": ["MA10", "MA20", "MA30"], "confirm_days": [1, 2, 3]},
            "fit_for_etf_rotation": "strong candidate",
            "risk": "MA10 易噪声，MA30 可能退出滞后。",
            "backtest_note": "适合与 ranking exit 组合，而不是单独使用。",
        },
        {
            "family": "ranking_drop_exit",
            "label": "Ranking Drop Exit",
            "execution_enabled": False,
            "parameters": {
                "exit_if_rank_below": [10, 15, 20, 30],
                "score_drop_threshold": [0.10, 0.20, 0.30],
                "consecutive_days": [1, 2, 3],
            },
            "fit_for_etf_rotation": "core candidate",
            "risk": "如果排名日内/日间抖动大，1 日确认会过度换手。",
            "backtest_note": "最符合横截面轮动逻辑，需重点测试换手和成本。",
        },
        {
            "family": "time_stop_capital_efficiency_exit",
            "label": "Time Stop / Capital Efficiency Exit",
            "execution_enabled": False,
            "parameters": {"max_holding_days": [10, 15, 20, 25, 30], "min_return_required": [0.0, 0.01, 0.02, 0.03]},
            "fit_for_etf_rotation": "secondary candidate",
            "risk": "容易把慢趋势卖飞，尤其宽基和红利风格。",
            "backtest_note": "适合检验资金效率，不应单独作为硬退出。",
        },
        {
            "family": "market_state_exit",
            "label": "Market State Exit",
            "execution_enabled": False,
            "parameters": {"if_market_state": ["risk_off", "weak"], "reduce_or_exit": ["review_only"]},
            "fit_for_etf_rotation": "risk overlay only",
            "risk": "市场状态误判会导致系统性踏空。",
            "backtest_note": "第一版只做 review only 或分组统计，不直接强制清仓。",
        },
        {
            "family": "portfolio_exposure_exit",
            "label": "Portfolio Exposure Exit",
            "execution_enabled": False,
            "parameters": {
                "if_same_group_overexposed": ["review_only"],
                "if_high_beta_overexposed": ["review_only"],
                "if_no_broad_based_anchor": ["review_only"],
            },
            "fit_for_etf_rotation": "risk review only",
            "risk": "组合暴露规则应先影响新买入和复核，不宜直接强制卖出。",
            "backtest_note": "观察集中度、回撤贡献和错失收益。",
        },
    ]
    return {
        "version": "exit_rule_candidate_library_v1",
        "generated_at": generated_at,
        "status": "research_only",
        "execution_enabled": False,
        "backtest_required": True,
        "type_summary": type_summary,
        "rule_families": rule_families,
        "etf_type_parameter_framework": build_type_framework(type_summary),
        "sources": SOURCE_LINKS,
        "safety": {
            "broker_api": False,
            "real_order": False,
            "paper_trade_modified": False,
            "paper_position_modified": False,
            "execution_rule_changed": False,
        },
    }


def build_type_framework(type_summary: dict[str, dict]) -> dict[str, dict]:
    base = {
        "broad_index": {
            "role": "core beta / broad market exposure",
            "stop_loss_search": ["5%-8%", "8%-12%", "2.0-4.0x ATR"],
            "take_profit_search": ["8%-15%", "ranking exit primary"],
            "trailing_search": ["profit start 5%-10%", "trail 4%-8% or 2.5-5.0x ATR"],
            "time_stop_search": ["20-60 days", "avoid too-short capital-efficiency exit"],
            "note": "宽基更适合趋势/ranking 出口，止损不宜过紧。",
        },
        "sector": {
            "role": "industry beta / style rotation",
            "stop_loss_search": ["4%-6%", "6%-10%", "1.8-3.5x ATR"],
            "take_profit_search": ["6%-12%", "trailing profit candidate"],
            "trailing_search": ["profit start 4%-8%", "trail 3%-7% or 2.0-4.5x ATR"],
            "time_stop_search": ["10-30 days", "combine with ranking drop"],
            "note": "行业 ETF 对风格切换敏感，ranking 掉队和趋势破坏应重点测试。",
        },
        "theme": {
            "role": "theme/high momentum exposure",
            "stop_loss_search": ["4%-6%", "6%-10%", "1.5-3.5x ATR"],
            "take_profit_search": ["5%-12%", "profit giveback control"],
            "trailing_search": ["profit start 3%-8%", "trail 2.5%-6% or 2.0-4.0x ATR"],
            "time_stop_search": ["5-20 days", "hotspot decay review"],
            "note": "主题 ETF 容易拥挤和退潮，移动止盈与 ranking 连续掉队值得回测。",
        },
        "high_beta": {
            "role": "high beta sentiment sector",
            "stop_loss_search": ["4%-6%", "6%-9%", "1.5-3.0x ATR"],
            "take_profit_search": ["5%-12%", "strict giveback tracking"],
            "trailing_search": ["profit start 3%-8%", "trail 2.5%-6%"],
            "time_stop_search": ["5-20 days", "short_swing weakening review"],
            "note": "高 beta ETF 不适合宽止损无限持有，需更重视短周期衰减。",
        },
        "commodity_resource": {
            "role": "cyclical / resource exposure",
            "stop_loss_search": ["4%-8%", "6%-10%", "1.8-3.5x ATR"],
            "take_profit_search": ["6%-15%", "trend/ranking confirmation"],
            "trailing_search": ["profit start 5%-10%", "trail 4%-8%"],
            "time_stop_search": ["10-45 days", "commodity cycle review"],
            "note": "周期资源可能趋势延续，也可能政策/价格冲击反转，ATR 与趋势破坏应组合测试。",
        },
        "defensive": {
            "role": "defensive / dividend / low volatility",
            "stop_loss_search": ["4%-8%", "2.0-4.0x ATR"],
            "take_profit_search": ["ranking exit primary", "avoid aggressive fixed take-profit"],
            "trailing_search": ["profit start 6%-12%", "trail 4%-8%"],
            "time_stop_search": ["20-60 days", "allow slower trend"],
            "note": "防御/红利 ETF 更偏慢趋势，过紧止盈可能降低防守价值。",
        },
        "bond_cash": {
            "role": "cash/bond sleeve",
            "stop_loss_search": ["0.5%-2.5%", "duration/credit event review"],
            "take_profit_search": ["not primary"],
            "trailing_search": ["not primary"],
            "time_stop_search": ["30-90 days", "liquidity/carry review"],
            "note": "债券/货币 ETF 需单独规则，不套权益 ETF 止盈止损。",
        },
        "qdii": {
            "role": "cross-border exposure",
            "stop_loss_search": ["observe only"],
            "take_profit_search": ["observe only"],
            "trailing_search": ["observe only"],
            "time_stop_search": ["10-45 days after premium/fx checks"],
            "note": "QDII 自动交易前必须补溢价、汇率、海外交易日和申赎状态。",
        },
        "unknown": {
            "role": "manual review",
            "stop_loss_search": ["do not auto trade"],
            "take_profit_search": ["do not auto trade"],
            "trailing_search": ["do not auto trade"],
            "time_stop_search": ["manual classification first"],
            "note": "unknown 分类先不进入自动交易回测池。",
        },
    }
    for etf_type, stats in type_summary.items():
        row = base.setdefault(etf_type, {"role": "unmapped", "note": "needs manual review"})
        row["sample_count"] = stats.get("count", 0)
        row["median_annualized_volatility"] = stats.get("median_annualized_volatility")
        row["median_atr_14_pct"] = stats.get("median_atr_14_pct")
        row["avg_max_drawdown"] = stats.get("avg_max_drawdown")
    return base


def render_exit_research_report() -> str:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    source_lines = "\n".join(f"- [{item['name']}]({item['url']})：{item['note']}" for item in SOURCE_LINKS)
    return f"""# ETF Rotation Exit Rule Research {generated_at}

本报告是 ETF 轮动退出规则调研材料，不是最终交易规则；不接入 paper_trade_engine，不修改模拟持仓。

## 摘要结论

1. ETF 轮动最自然的退出机制不是单一止盈止损，而是 ranking 掉队、趋势破坏、持有期效率和波动自适应止损的组合。
2. 固定止损/固定止盈适合作为 baseline，但容易过拟合，也容易卖飞趋势强的 ETF。
3. ATR/波动率止损更适合跨 ETF 类型比较，因为宽基、主题、高 beta、债券 ETF 的波动结构差异很大。
4. 移动止盈适合行业/主题/高 beta ETF，但要重点观察 whipsaw 和 profit giveback。
5. QDII 暂不进入自动退出规则，需要额外溢价、汇率、海外交易日和申赎状态数据。
6. 债券/货币 ETF 应单独设计，不套普通权益 ETF 的 5%-10% 止损。

## 常见退出机制评估

| 规则 | 适合 ETF 轮动吗 | 优点 | 主要风险 | 是否需回测 |
| --- | --- | --- | --- | --- |
| 固定止损 | baseline 适合 | 简单、可控最大亏损 | 不适配不同 ETF 波动，容易过紧 | 必须 |
| 固定止盈 | 只适合 baseline | 便于观察利润兑现 | 趋势行情容易卖飞 | 必须 |
| 移动止盈 | 行业/主题较适合 | 保护利润，允许趋势延续 | 震荡市被洗出 | 必须 |
| ATR 止损 | 强候选 | 波动自适应 | 参数多，可能过拟合 | 必须 |
| 均线趋势破坏 | 强候选 | 符合趋势策略 | 滞后或噪声 | 必须 |
| ranking 掉队 | 核心候选 | 符合横截面轮动 | 排名抖动导致换手 | 必须 |
| 时间止损 | 辅助候选 | 约束资金效率 | 慢趋势被卖飞 | 必须 |
| 市场状态恶化 | 风险叠加 | 控制系统性风险 | 可能踏空 | 先 review only |
| 组合暴露过高 | 风险叠加 | 控制集中度 | 不宜强制卖出 | 先 review only |

## 对当前项目的适配判断

- 当前系统已有 BUY ranking、sell_signal_review、ETF 分类、组合暴露和 shadow tracking；最适合优先回测 ranking exit + trend breakdown + ATR stop。
- 当前最多持有 3 只、单只 20%、交易成本和 100 份单位约束已经更贴近真实模拟，应在退出规则回测中保留。
- 不建议先上线固定 5% 止损或固定 10% 止盈。它们可以做 benchmark，但不能未经回测直接执行。

## 来源

{source_lines}

## 安全边界

- 不接券商 API。
- 不真实下单。
- 不修改 paper_trades.csv。
- 不修改 paper_positions.csv。
- 不改变当前模拟盘执行逻辑。
"""


def render_candidates_report(candidates: dict) -> str:
    lines = [
        f"# Exit Rule Candidate Library {candidates['generated_at']}",
        "",
        "本候选库只用于后续回测，不接入执行层。",
        "",
        f"- 规则族数量：{len(candidates['rule_families'])}",
        "- execution_enabled: false",
        "- backtest_required: true",
        "",
        "## 规则族",
    ]
    for item in candidates["rule_families"]:
        lines.extend(
            [
                f"### {item['label']}",
                f"- family: `{item['family']}`",
                f"- fit: {item['fit_for_etf_rotation']}",
                f"- risk: {item['risk']}",
                f"- backtest_note: {item['backtest_note']}",
                "```json",
                json.dumps(item["parameters"], ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def render_by_type_report(type_summary: dict[str, dict], candidates: dict) -> str:
    framework = candidates["etf_type_parameter_framework"]
    lines = [
        f"# Exit Rule Parameters by ETF Type {candidates['generated_at']}",
        "",
        "以下为参数搜索范围，不是固定执行规则；所有范围都需要正式回测验证。",
        "",
        "| ETF 类型 | 样本数 | 年化波动中位数 | ATR14 中位数 | 初始止损搜索 | 移动止盈搜索 | 时间止损搜索 | 说明 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for etf_type, row in framework.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    etf_type,
                    str(row.get("sample_count", 0)),
                    pct(row.get("median_annualized_volatility")),
                    pct(row.get("median_atr_14_pct")),
                    list_text(row.get("stop_loss_search")),
                    list_text(row.get("trailing_search")),
                    list_text(row.get("time_stop_search")),
                    str(row.get("note", "")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 特别说明",
            "- 宽基 ETF：更适合 ranking exit + 趋势破坏，止损不宜过紧。",
            "- 行业/周期/主题 ETF：更需要移动止盈和 ranking 连续掉队检测。",
            "- 高 beta ETF：应更关注 short_swing 转弱、profit giveback 和高波动风险。",
            "- 债券/货币 ETF：单独规则，不套权益 ETF 参数。",
            "- QDII ETF：暂不建议进入自动交易规则。",
            "- unknown：必须先人工分类。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_backtest_design_report() -> str:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    combos = [
        ("No explicit profit stop + ranking exit", "只靠 ranking 掉队和基础风险退出", "最贴近轮动本质，避免卖飞", "回撤可能较大", "ranking 阈值", "turnover, drawdown, profit giveback"),
        ("Fixed stop + ranking exit", "固定止损叠加排名掉队", "简单，便于 baseline", "止损可能不适配类型", "固定比例参数", "max drawdown, win rate, cost impact"),
        ("ATR stop + ranking exit", "波动自适应止损叠加排名掉队", "适配不同波动 ETF", "ATR 倍数可能过拟合", "ATR window/multiple", "Calmar, whipsaw count"),
        ("Fixed stop + trailing profit + ranking exit", "固定亏损控制 + 利润回撤保护", "兼顾亏损和盈利回吐", "震荡市被洗出", "profit start / trail pct", "profit giveback, avg win/loss"),
        ("ATR trailing + trend breakdown", "波动自适应移动止盈 + 均线破坏", "适合趋势延续", "趋势破坏滞后", "MA window, ATR multiple", "CAGR, drawdown, holding days"),
        ("Time stop + ranking exit", "持有过久且收益不足时退出", "提高资金效率", "慢趋势被卖飞", "max days / min return", "capital efficiency, turnover"),
        ("ETF type-aware exit", "按 ETF 类型选择不同搜索空间", "更符合波动差异", "类型分类错误会污染结果", "type mapping", "all metrics by type"),
        ("Market state review only", "市场弱时触发复核，不自动退出", "低风险接入", "不能直接降低回撤", "state threshold", "state-conditioned returns"),
    ]
    lines = [
        f"# Exit Rule Backtest Design {generated_at}",
        "",
        "本设计用于 Phase 4A/4B 回测，不修改当前执行规则。",
        "",
        "| 组合 | 逻辑 | 优点 | 缺点 | 可能过拟合点 | 需要观察指标 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in combos:
        lines.append("| " + " | ".join(row) + " |")
    lines.extend(
        [
            "",
            "## 统一评价指标",
            "- CAGR",
            "- max drawdown",
            "- Sharpe",
            "- Calmar",
            "- win rate",
            "- avg win/loss",
            "- turnover",
            "- average holding days",
            "- profit giveback",
            "- whipsaw count",
            "- transaction cost impact",
            "",
            "## 第一版约束",
            "- 只用推荐 trade_pool，不直接用全 183 只。",
            "- 加入佣金、最低佣金、滑点、100 份整数倍。",
            "- QDII、unknown、低流动性、短历史标的不进入自动交易池。",
            "- market_state 和 portfolio_exposure 先作为 review/分组分析，不强制交易。",
        ]
    )
    return "\n".join(lines) + "\n"


def safe_float(value: object) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return round(float(value), 6)
    except Exception:
        return 0.0


def pct(value: object) -> str:
    try:
        return f"{float(value):.2%}"
    except Exception:
        return "N/A"


def list_text(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value or "N/A")


if __name__ == "__main__":
    main()
