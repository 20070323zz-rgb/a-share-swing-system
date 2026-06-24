"""ETF classification sidecar for model research.

This module creates research-only classification files. It does not change
watchlist roles, paper positions, paper trades, or strategy rules.
"""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from config import DATA_DIR, ETF_DAILY_DIR, REPORT_DIR, WATCHLIST_FILE
from data_loader import read_formal_data_universe


CANDIDATES_FILE = DATA_DIR / "etf_pool_expansion_candidates.csv"
CLASSIFICATION_FILE = DATA_DIR / "etf_classification.csv"
LEGACY_CLASSIFICATION_FILE = DATA_DIR / "etf_type_classification.csv"
REPORT_FILE = REPORT_DIR / "etf_classification_report.md"
LEGACY_REPORT_FILE = REPORT_DIR / "etf_type_classification_report.md"

EXCLUDED_STATUS = {"failed_validation", "failed_dry_run", "unresolved", "excluded", "quarantined"}

OUTPUT_COLUMNS = [
    "symbol",
    "code",
    "name",
    "pool",
    "group",
    "status",
    "etf_type",
    "risk_profile",
    "holding_profile",
    "default_holding_min_days",
    "default_holding_max_days",
    "max_holding_days",
    "stop_loss_pct",
    "exit_sensitivity",
    "auto_buy_allowed",
    "qdii_check_required",
    "liquidity_check_required",
    "sentiment_check_required",
    "news_required",
    "classification_reason",
    "source_scope",
]

TYPE_PROFILE = {
    "broad_index": {
        "risk_profile": "core_beta",
        "holding_profile": "20-60",
        "min_days": 20,
        "max_days": 60,
        "stop_loss_pct": 0.08,
        "exit_sensitivity": "normal",
        "auto_buy_allowed": 1,
        "qdii": 0,
        "liquidity": 1,
        "sentiment": 0,
        "news_required": "low",
    },
    "sector": {
        "risk_profile": "sector_beta",
        "holding_profile": "10-30",
        "min_days": 10,
        "max_days": 30,
        "stop_loss_pct": 0.06,
        "exit_sensitivity": "medium",
        "auto_buy_allowed": 1,
        "qdii": 0,
        "liquidity": 1,
        "sentiment": 1,
        "news_required": "medium",
    },
    "theme": {
        "risk_profile": "theme_beta",
        "holding_profile": "5-20",
        "min_days": 5,
        "max_days": 20,
        "stop_loss_pct": 0.05,
        "exit_sensitivity": "high",
        "auto_buy_allowed": 0,
        "qdii": 0,
        "liquidity": 1,
        "sentiment": 1,
        "news_required": "high",
    },
    "high_beta": {
        "risk_profile": "high_beta",
        "holding_profile": "5-20",
        "min_days": 5,
        "max_days": 20,
        "stop_loss_pct": 0.05,
        "exit_sensitivity": "high",
        "auto_buy_allowed": 1,
        "qdii": 0,
        "liquidity": 1,
        "sentiment": 1,
        "news_required": "high",
    },
    "commodity_resource": {
        "risk_profile": "commodity_cycle",
        "holding_profile": "10-45",
        "min_days": 10,
        "max_days": 45,
        "stop_loss_pct": 0.06,
        "exit_sensitivity": "medium_high",
        "auto_buy_allowed": 1,
        "qdii": 0,
        "liquidity": 1,
        "sentiment": 1,
        "news_required": "medium_high",
    },
    "bond_cash": {
        "risk_profile": "low_volatility",
        "holding_profile": "30-90",
        "min_days": 30,
        "max_days": 90,
        "stop_loss_pct": 0.02,
        "exit_sensitivity": "low",
        "auto_buy_allowed": 0,
        "qdii": 0,
        "liquidity": 1,
        "sentiment": 0,
        "news_required": "low",
    },
    "qdii": {
        "risk_profile": "cross_border",
        "holding_profile": "10-45",
        "min_days": 10,
        "max_days": 45,
        "stop_loss_pct": 0.07,
        "exit_sensitivity": "medium_high",
        "auto_buy_allowed": 0,
        "qdii": 1,
        "liquidity": 1,
        "sentiment": 1,
        "news_required": "medium",
    },
    "unknown": {
        "risk_profile": "manual_review",
        "holding_profile": "N/A",
        "min_days": 0,
        "max_days": 0,
        "stop_loss_pct": 0.0,
        "exit_sensitivity": "manual_review",
        "auto_buy_allowed": 0,
        "qdii": 0,
        "liquidity": 1,
        "sentiment": 0,
        "news_required": "unknown",
    },
}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = build_classification()
    df.to_csv(CLASSIFICATION_FILE, index=False)
    df.to_csv(LEGACY_CLASSIFICATION_FILE, index=False)
    report = render_report(df)
    REPORT_FILE.write_text(report, encoding="utf-8")
    LEGACY_REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"ETF classification rows: {len(df)}")
    print(f"written: {CLASSIFICATION_FILE}")
    print(f"written: {REPORT_FILE}")


def build_classification() -> pd.DataFrame:
    universe = read_formal_data_universe(WATCHLIST_FILE, ETF_DAILY_DIR, CANDIDATES_FILE)
    candidate_status = _candidate_status_map(CANDIDATES_FILE)
    rows = []
    for item in universe.to_dict(orient="records"):
        code = _clean_code(item.get("code", ""))
        if not code:
            continue
        name = str(item.get("name") or code).strip()
        group = str(item.get("group") or "未分类").strip()
        pool = str(item.get("role") or item.get("pool") or "research_only").strip()
        status = candidate_status.get(code, "active" if str(item.get("source")) != "etf_pool_expansion_candidates" else "imported")
        etf_type, reason = classify_etf(code, name, group, pool, status)
        profile = TYPE_PROFILE.get(etf_type, TYPE_PROFILE["unknown"])
        if status in EXCLUDED_STATUS:
            auto_buy_allowed = 0
        else:
            auto_buy_allowed = profile["auto_buy_allowed"]
        rows.append(
            {
                "symbol": code,
                "code": code,
                "name": name,
                "pool": pool,
                "group": group,
                "status": status,
                "etf_type": etf_type,
                "risk_profile": profile["risk_profile"],
                "holding_profile": profile["holding_profile"],
                "default_holding_min_days": profile["min_days"],
                "default_holding_max_days": profile["max_days"],
                "max_holding_days": profile["max_days"],
                "stop_loss_pct": profile["stop_loss_pct"],
                "exit_sensitivity": profile["exit_sensitivity"],
                "auto_buy_allowed": auto_buy_allowed,
                "qdii_check_required": profile["qdii"],
                "liquidity_check_required": profile["liquidity"],
                "sentiment_check_required": profile["sentiment"],
                "news_required": profile["news_required"],
                "classification_reason": reason,
                "source_scope": str(item.get("source") or "data_universe"),
            }
        )
    if not rows:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    df = pd.DataFrame(rows)
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[OUTPUT_COLUMNS].drop_duplicates("symbol", keep="first").sort_values("symbol").reset_index(drop=True)


def classify_etf(code: str, name: str, group: str, pool: str, status: str) -> tuple[str, str]:
    text = f"{code} {name} {group} {pool}"
    if status in EXCLUDED_STATUS:
        return "unknown", f"excluded status={status}"
    if code in {"515220"} or _has(text, ["煤炭", "有色", "稀土", "能源", "黄金", "铜", "油气", "钢铁", "建材", "化工", "资源"]):
        return "commodity_resource", "商品/周期资源关键词"
    if code in {"512800"}:
        return "sector", "银行金融红利属性，按低敏感行业处理"
    if code in {"515880", "512880", "512070"} or _has(text, ["证券", "券商", "非银"]):
        return "high_beta", "券商/非银高 beta 情绪行业"
    if _has(text, ["QDII", "港股", "恒生", "中概", "纳指", "标普", "日经", "德国", "印度", "新兴市场", "东南亚"]):
        return "qdii", "跨境/QDII关键词"
    if code.startswith("511") or _has(text, ["国债", "政金债", "信用债", "可转债", "短债", "货币", "现金", "添益", "日利", "短融"]):
        return "bond_cash", "债券/货币关键词"
    if _has(text, ["沪深300", "中证500", "中证1000", "中证2000", "中证A500", "A500", "A50", "上证50", "上证180", "深100", "创业板", "科创50", "科创100", "科创200", "北证50", "宽基"]):
        return "broad_index", "宽基指数关键词"
    if _has(text, ["机器人", "低空", "商业航天", "卫星", "人形", "工业母机", "半导体设备", "算力", "数据中心", "AI", "人工智能", "5G", "通信", "光模块", "芯片", "半导体", "软件", "信创", "云计算", "游戏", "传媒", "创新药", "生物科技", "新能源", "光伏", "电池"]):
        return "theme", "主题/科技成长关键词"
    if _has(text, ["银行", "金融", "地产", "医药", "医疗", "消费", "食品", "酒", "家电", "旅游", "汽车", "军工", "红利", "高股息", "养殖", "农业", "公用事业", "电力", "央企", "低波", "质量"]):
        return "sector", "行业/风格关键词"
    if "ETF" in text.upper():
        return "unknown", "ETF但规则无法确定，需人工确认"
    return "unknown", "无法确定为ETF分类"


def render_report(df: pd.DataFrame) -> str:
    type_counts = df["etf_type"].value_counts().to_dict() if not df.empty else {}
    pool_counts = df["pool"].value_counts().to_dict() if not df.empty else {}
    excluded = df[df["status"].isin(EXCLUDED_STATUS)] if not df.empty else pd.DataFrame()
    held = _current_position_symbols()
    held_df = df[df["symbol"].isin(held)] if held and not df.empty else pd.DataFrame(columns=df.columns)
    lines = [
        "# ETF 分类研究报告",
        "",
        "本报告是 phase2_model_research_v1 的研究侧分类文件，不修改交易规则、不修改模拟仓、不生成买卖。",
        "",
        "## 摘要",
        f"- 分类 ETF 数量：{len(df)}",
        f"- 类型分布：{type_counts}",
        f"- pool 分布：{pool_counts}",
        f"- excluded/failed/unresolved 数量：{len(excluded)}",
        "",
        "## 当前持仓分类",
        "| symbol | name | group | pool | etf_type | risk_profile | holding_profile | stop_loss_pct | auto_buy_allowed | reason |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    if held_df.empty:
        lines.append("|  | 当前无持仓或无匹配分类 |  |  |  |  |  |  |  |  |")
    else:
        for _, row in held_df.iterrows():
            lines.append(
                f"| {row['symbol']} | {row['name']} | {row['group']} | {row['pool']} | {row['etf_type']} | "
                f"{row['risk_profile']} | {row['holding_profile']} | {float(row['stop_loss_pct']):.2%} | "
                f"{row['auto_buy_allowed']} | {row['classification_reason']} |"
            )
    lines += [
        "",
        "## 分类规则",
        "- broad_index：宽基指数，适合中期趋势与横截面轮动研究。",
        "- sector：行业/风格 ETF，退出敏感度中等，需要行业新闻作为解释或风险过滤。",
        "- theme/high_beta：主题或高 beta ETF，短周期更敏感，新闻情绪暂不进入 BUY 主分。",
        "- commodity_resource：周期资源 ETF，需要关注商品价格、政策和供需事件。",
        "- bond_cash：债券/货币类，默认不进入进攻型自动买入。",
        "- qdii：跨境类，需要额外溢价、汇率、海外交易日检查。",
        "- unknown：不强行分类，需要人工复核。",
        "",
        "## 安全边界",
        "- 只写入 data/etf_classification.csv 和兼容文件 data/etf_type_classification.csv。",
        "- 不修改 watchlist、不修改 trade_pool、不修改 paper_positions/paper_trades。",
        "- 不接券商 API，不真实下单。",
    ]
    return "\n".join(lines)


def _candidate_status_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")
    except Exception:
        return {}
    if "code" not in df.columns:
        return {}
    result = {}
    for _, row in df.iterrows():
        code = _clean_code(row.get("code", ""))
        if code:
            result[code] = str(row.get("status") or "candidate").strip()
    return result


def _current_position_symbols() -> set[str]:
    path = DATA_DIR / "paper_positions.csv"
    if not path.exists():
        return set()
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")
    except Exception:
        return set()
    col = "symbol" if "symbol" in df.columns else "code" if "code" in df.columns else ""
    if not col:
        return set()
    return {_clean_code(value) for value in df[col].tolist() if _clean_code(value)}


def _clean_code(value: object) -> str:
    match = re.search(r"(\d{6})", str(value or ""))
    return match.group(1) if match else ""


def _has(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


if __name__ == "__main__":
    main()
