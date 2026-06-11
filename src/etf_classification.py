"""ETF type classification for offline research.

This module creates a sidecar classification file and report. It does not
change trading rules, paper positions, or paper trades.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from config import DATA_DIR, REPORT_DIR, WATCHLIST_FILE


CLASSIFICATION_FILE = DATA_DIR / "etf_type_classification.csv"
REPORT_FILE = REPORT_DIR / "etf_type_classification_report.md"
CANDIDATES_FILE = DATA_DIR / "etf_pool_expansion_candidates.csv"

FIELDS = [
    "code",
    "name",
    "source_scope",
    "pool",
    "group",
    "etf_type",
    "holding_profile",
    "default_holding_min_days",
    "default_holding_max_days",
    "exit_sensitivity",
    "news_required",
    "sentiment_filter_required",
    "qdii_check_required",
    "liquidity_check_required",
    "status",
    "classification_reason",
]


PROFILE = {
    "broad_index": ("20-60", 20, 60, "normal", "low", False, False, True),
    "sector": ("10-30", 10, 30, "medium", "medium", True, False, True),
    "theme": ("5-20", 5, 20, "high", "high", True, False, True),
    "hot_theme": ("3-10", 3, 10, "very_high", "high", True, False, True),
    "bond_cash": ("30-90", 30, 90, "low", "low", False, False, True),
    "qdii": ("10-45", 10, 45, "medium", "medium", True, True, True),
    "commodity_resource": ("10-45", 10, 45, "medium_high", "medium_high", True, False, True),
    "unknown": ("N/A", 0, 0, "unknown", "unknown", False, False, True),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ETF 类型分层研究分类")
    return parser.parse_args()


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_classification()
    df = pd.DataFrame(rows, columns=FIELDS).drop_duplicates(subset=["code"], keep="first")
    df.to_csv(CLASSIFICATION_FILE, index=False)
    write_report(df)
    print(f"已生成 ETF 类型分层文件：{CLASSIFICATION_FILE}")
    print(f"已生成 ETF 类型分层报告：{REPORT_FILE}")


def build_classification() -> list[dict]:
    inputs = []
    if WATCHLIST_FILE.exists():
        watchlist = pd.read_csv(WATCHLIST_FILE, dtype=str).fillna("")
        watchlist["source_scope"] = "watchlist"
        watchlist["pool"] = watchlist.get("role", "")
        inputs.append(watchlist)
    if CANDIDATES_FILE.exists():
        candidates = pd.read_csv(CANDIDATES_FILE, dtype=str).fillna("")
        candidates["source_scope"] = "expansion_candidates"
        inputs.append(candidates)
    if not inputs:
        return []
    combined = pd.concat(inputs, ignore_index=True, sort=False).fillna("")
    rows = []
    for item in combined.to_dict(orient="records"):
        code = str(item.get("code", "")).strip()
        if not code or not code.isdigit():
            continue
        name = str(item.get("name", code)).strip()
        group = str(item.get("group", "")).strip()
        pool = str(item.get("pool", item.get("role", ""))).strip()
        status = str(item.get("status", "active" if item.get("source_scope") == "watchlist" else "")).strip()
        etf_type, reason = classify(name, group, pool, status)
        rows.append(_row(item, code, name, group, pool, etf_type, reason))
    return rows


def classify(name: str, group: str, pool: str, status: str) -> tuple[str, str]:
    text = f"{name} {group} {pool}".lower()
    raw = f"{name} {group} {pool}"
    if status in {"failed_validation", "failed_dry_run", "unresolved", "excluded"}:
        return "unknown", f"excluded status={status}"
    if any(key in raw for key in ["QDII", "纳指", "恒生", "港股", "中概", "日经", "德国", "印度", "标普"]):
        return "qdii", "跨境/QDII关键词"
    if any(key in raw for key in ["国债", "政金债", "信用债", "可转债", "短债", "货币", "银华日利", "华宝添益", "短融"]):
        return "bond_cash", "债券/货币关键词"
    if any(key in raw for key in ["黄金", "煤炭", "有色", "能源", "油气", "铜", "稀土", "钢铁", "资源"]):
        return "commodity_resource", "商品/周期资源关键词"
    if any(key in raw for key in ["沪深300", "中证500", "中证1000", "创业板50", "创业板ETF", "科创50", "科创创业", "上证50", "上证180", "深100", "中证A500", "A500", "A50", "中证2000", "北证50"]):
        return "broad_index", "宽基指数关键词"
    if any(key in raw for key in ["机器人", "低空", "商业航天", "卫星", "人形", "工业母机", "半导体设备", "算力", "数据中心"]):
        return "hot_theme", "强事件/高热主题关键词"
    if any(key in raw for key in ["AI", "人工智能", "5G", "通信", "光模块", "芯片", "半导体", "软件", "信创", "云计算", "游戏", "传媒", "创新药", "生物科技"]):
        return "theme", "主题/科技成长关键词"
    if any(key in raw for key in ["银行", "证券", "券商", "金融", "房地产", "医药", "医疗", "消费", "食品", "酒", "家电", "旅游", "汽车", "军工", "新能源", "电池", "光伏", "红利", "高股息", "养殖", "农业", "公用事业", "电力"]):
        return "sector", "行业ETF关键词"
    if "ETF" in raw.upper():
        return "unknown", "ETF但规则无法确定"
    return "unknown", "非ETF或无法确定"


def _row(source: dict, code: str, name: str, group: str, pool: str, etf_type: str, reason: str) -> dict:
    profile, min_days, max_days, exit_sensitivity, news_required, sentiment_required, qdii_required, liquidity_required = PROFILE[etf_type]
    return {
        "code": code,
        "name": name,
        "source_scope": source.get("source_scope", ""),
        "pool": pool,
        "group": group,
        "etf_type": etf_type,
        "holding_profile": profile,
        "default_holding_min_days": min_days,
        "default_holding_max_days": max_days,
        "exit_sensitivity": exit_sensitivity,
        "news_required": news_required,
        "sentiment_filter_required": int(bool(sentiment_required)),
        "qdii_check_required": int(bool(qdii_required)),
        "liquidity_check_required": int(bool(liquidity_required)),
        "status": source.get("status", "active"),
        "classification_reason": reason,
    }


def write_report(df: pd.DataFrame) -> None:
    positions = _read_positions()
    unknown = df[df["etf_type"] == "unknown"].copy()
    type_counts = df["etf_type"].value_counts().to_dict() if not df.empty else {}
    pool_counts = df["pool"].value_counts().to_dict() if "pool" in df.columns else {}
    held = df[df["code"].isin(positions["symbol"].astype(str).tolist())] if not positions.empty else pd.DataFrame(columns=df.columns)
    excluded = df[df["status"].isin(["failed_validation", "failed_dry_run", "unresolved", "excluded"])] if "status" in df.columns else pd.DataFrame()
    lines = [
        "# ETF 类型分层报告",
        "",
        "本报告只用于研究分层，不修改交易规则、不改模拟持仓、不生成买卖指令。",
        "",
        "## 摘要",
        f"- 分类总数：{len(df)}",
        f"- 各类型数量：{type_counts}",
        f"- pool 分布：{pool_counts}",
        f"- unknown 数量：{len(unknown)}",
        f"- failed/quarantine/unresolved/excluded 排除类数量：{len(excluded)}",
        "",
        "## 当前持仓所属类型",
        "| code | name | group | etf_type | holding_profile | exit_sensitivity | news_required | classification_reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    if held.empty:
        lines.append("|  | 当前无匹配持仓 |  |  |  |  |  |  |")
    else:
        for _, row in held.iterrows():
            lines.append(
                f"| {row['code']} | {row['name']} | {row['group']} | {row['etf_type']} | {row['holding_profile']} | "
                f"{row['exit_sensitivity']} | {row['news_required']} | {row['classification_reason']} |"
            )
    lines += [
        "",
        "## 分类规则说明",
        "- broad_index：宽基指数关键词，如沪深300、中证500、中证1000、创业板50、科创50、中证A500。",
        "- sector：银行、证券、医药、消费、军工、新能源、红利等行业/风格 ETF。",
        "- theme：AI、5G、芯片、半导体、创新药等主题 ETF。",
        "- hot_theme：机器人、低空经济、商业航天、半导体设备、算力等强事件主题。",
        "- bond_cash：国债、短债、货币、现金管理类 ETF。",
        "- qdii：港股、美股、日经、印度等跨境 ETF。",
        "- commodity_resource：黄金、煤炭、有色、铜、油气、稀土等商品/资源相关 ETF。",
        "- unknown：规则无法确定，需人工确认，不强行分类。",
        "",
        "## 需要人工确认的 ETF",
        "| code | name | group | pool | status | reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    if unknown.empty:
        lines.append("|  | 无 |  |  |  |  |")
    else:
        for _, row in unknown.head(80).iterrows():
            lines.append(f"| {row['code']} | {row['name']} | {row['group']} | {row['pool']} | {row['status']} | {row['classification_reason']} |")
    lines += [
        "",
        "## 安全边界",
        "- 本轮只生成研究分类 sidecar 文件 data/etf_type_classification.csv。",
        "- 不修改 mid_trend / short_swing 核心策略。",
        "- 不修改 paper_positions.csv 或 paper_trades.csv。",
        "- 不接券商 API，不真实下单。",
    ]
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def _read_positions() -> pd.DataFrame:
    path = DATA_DIR / "paper_positions.csv"
    if not path.exists():
        return pd.DataFrame(columns=["symbol"])
    return pd.read_csv(path, dtype=str).fillna("")


if __name__ == "__main__":
    main()
