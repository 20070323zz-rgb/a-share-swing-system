"""Resolve ETF expansion seed candidates to real JQData ETF symbols.

This script reads local CSV files only. It does not connect to broker APIs,
does not place orders, does not read account credentials, and does not write
to data/etf_daily/.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = PROJECT_ROOT / "data" / "etf_pool_expansion_candidates.csv"
DEFAULT_JQDATA_CANDIDATES = PROJECT_ROOT / "data" / "staging" / "etf_candidates" / "jqdata_etf_candidates.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "staging" / "etf_candidates" / "resolved_etf_expansion_candidates.csv"
WATCHLIST_PATH = PROJECT_ROOT / "watchlist.csv"

MAX_MATCHES_PER_PENDING = 3
MIN_MATCH_SCORE = 8


@dataclass(frozen=True)
class KeywordRule:
    keywords: tuple[str, ...]
    required_any: tuple[str, ...] = ()
    banned: tuple[str, ...] = ()
    max_matches: int = MAX_MATCHES_PER_PENDING


KEYWORD_RULES: dict[str, KeywordRule] = {
    "PENDING_A50_01": KeywordRule(("中证A50", "A50"), ("中证A50", "A50"), ("A500", "中证A500")),
    "PENDING_CSI2000_01": KeywordRule(("中证2000", "2000"), ("中证2000",)),
    "PENDING_KC200_01": KeywordRule(("科创200",), ("科创200",)),
    "PENDING_BJ50_01": KeywordRule(("北证50",), ("北证50",)),
    "PENDING_ROBOT_50_01": KeywordRule(("机器人50", "机器人"), ("机器人",)),
    "PENDING_SEMI_EQUIP_01": KeywordRule(("半导体设备", "芯片设备", "设备"), ("半导体设备", "芯片设备")),
    "PENDING_AI_KCB_01": KeywordRule(("科创人工智能", "人工智能", "AI"), ("人工智能", "AI")),
    "PENDING_COMPUTE_01": KeywordRule(("算力",), ("算力",)),
    "PENDING_DATA_CENTER_01": KeywordRule(("数据中心",), ("数据中心",)),
    "PENDING_TELECOM_EQUIP_01": KeywordRule(("通信设备", "通信"), ("通信设备",)),
    "PENDING_XINCHUANG_01": KeywordRule(("信创",), ("信创",)),
    "PENDING_INFOSAFE_01": KeywordRule(("信息安全", "网络安全"), ("信息安全", "网络安全")),
    "PENDING_MACHINE_TOOL_01": KeywordRule(("工业母机", "机床"), ("工业母机", "机床")),
    "PENDING_HIGH_END_EQUIP_01": KeywordRule(("高端装备", "装备"), ("高端装备",)),
    "PENDING_LOW_ALTITUDE_01": KeywordRule(("低空经济", "低空"), ("低空经济", "低空")),
    "PENDING_SPACE_01": KeywordRule(("商业航天", "航天"), ("商业航天",)),
    "PENDING_HK_BIOTECH_01": KeywordRule(("恒生生物科技", "生物科技", "港股生物"), ("生物科技",)),
    "PENDING_MED_DEVICE_01": KeywordRule(("医疗器械", "器械"), ("医疗器械",)),
    "PENDING_CENTRAL_DIV_01": KeywordRule(("央企红利", "央企", "红利"), ("央企红利", "央企")),
    "PENDING_QUALITY_LOWVOL_01": KeywordRule(("质量低波", "低波", "质量"), ("质量低波", "低波")),
    "PENDING_UTILITY_01": KeywordRule(("公用事业", "公用"), ("公用事业", "公用")),
    "PENDING_POWER_01": KeywordRule(("电力",), ("电力",)),
    "PENDING_A500_DIV_LOWVOL_01": KeywordRule(("A500红利低波", "中证A500红利低波", "A500", "红利低波"), ("A500", "红利低波")),
    "PENDING_COPPER_01": KeywordRule(("铜",), ("铜",)),
    "PENDING_INDUSTRIAL_METAL_01": KeywordRule(("工业金属", "有色金属", "金属"), ("工业金属",)),
    "PENDING_OILGAS_01": KeywordRule(("油气", "石油"), ("油气", "石油")),
    "PENDING_GOLD_STOCK_01": KeywordRule(("黄金股", "黄金股票"), ("黄金股", "黄金股票")),
    "PENDING_STEEL_01": KeywordRule(("钢铁",), ("钢铁",)),
    "PENDING_BUILDING_MATERIAL_01": KeywordRule(("建材", "建筑材料"), ("建材", "建筑材料")),
    "PENDING_NEW_MATERIAL_01": KeywordRule(("新材料",), ("新材料",)),
    "PENDING_INDIA_01": KeywordRule(("印度",), ("印度",)),
    "PENDING_EMERGING_01": KeywordRule(("新兴市场",), ("新兴市场",)),
    "PENDING_SHORT_BOND_01": KeywordRule(("短债", "短融"), ("短债", "短融")),
    "PENDING_CREDIT_BOND_01": KeywordRule(("信用债",), ("信用债",)),
    "PENDING_POLICY_BANK_02": KeywordRule(("政金债", "政策性金融债"), ("政金债", "政策性金融债")),
    "PENDING_CASH_01": KeywordRule(("现金", "货币"), ("现金", "货币")),
    "PENDING_DIV_QUALITY_02": KeywordRule(("红利质量",), ("红利质量",)),
    "PENDING_HK_HIGHDIV_02": KeywordRule(("港股高股息", "恒生高股息", "高股息"), ("高股息",)),
    "PENDING_CONSUME_UP_01": KeywordRule(("消费升级",), ("消费升级",)),
    "PENDING_SILVER_ECONOMY_01": KeywordRule(("银发经济",), ("银发经济",)),
    "PENDING_DIGITAL_ECON_01": KeywordRule(("数字经济",), ("数字经济",)),
    "PENDING_ELECTRONICS_01": KeywordRule(("电子",), ("电子",), ("电子50",)),
    "PENDING_PHOTONICS_01": KeywordRule(("光通信",), ("光通信",)),
    "PENDING_DRONE_01": KeywordRule(("无人机",), ("无人机",)),
    "PENDING_AUTONOMOUS_01": KeywordRule(("智能汽车", "智能车"), ("智能汽车", "智能车")),
    "PENDING_LITHIUM_01": KeywordRule(("锂电材料", "锂电池", "锂电"), ("锂电",)),
    "PENDING_RARE_METAL_01": KeywordRule(("稀有金属", "稀土", "小金属"), ("稀有金属", "小金属")),
    "PENDING_AGRI_SEED_01": KeywordRule(("种业", "农业"), ("种业",)),
    "PENDING_REIT_01": KeywordRule(("REIT", "REITs", "基建REIT"), ("REIT", "REITs")),
    "PENDING_BANK_DIV_01": KeywordRule(("银行红利", "银行"), ("银行红利",)),
    "PENDING_INSURANCE_01": KeywordRule(("保险",), ("保险",)),
    "PENDING_BROKER_LEADER_01": KeywordRule(("证券龙头", "券商龙头", "证券"), ("证券龙头", "券商龙头")),
    "PENDING_DIV_LOWVOL_02": KeywordRule(("红利低波",), ("红利低波",)),
    "PENDING_STATE_OWNED_01": KeywordRule(("国企", "央企"), ("国企", "央企")),
    "PENDING_ESG_01": KeywordRule(("ESG",), ("ESG",)),
    "PENDING_GREEN_POWER_01": KeywordRule(("绿电", "绿色电力"), ("绿电", "绿色电力")),
    "PENDING_HK_CONSUME_01": KeywordRule(("港股消费", "恒生消费"), ("港股消费", "恒生消费")),
    "PENDING_SEA_01": KeywordRule(("东南亚", "东盟"), ("东南亚", "东盟")),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve ETF expansion candidates to JQData ETF codes.")
    parser.add_argument("--candidates", default=str(DEFAULT_CANDIDATES), help="Expansion candidate CSV.")
    parser.add_argument("--jqdata-candidates", default=str(DEFAULT_JQDATA_CANDIDATES), help="JQData ETF candidate CSV.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Resolved output CSV.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    candidates = pd.read_csv(resolve_path(args.candidates), dtype=str).fillna("")
    jqdata = pd.read_csv(resolve_path(args.jqdata_candidates), dtype=str).fillna("")
    watchlist = read_watchlist()
    rows = resolve_candidates(candidates, jqdata, watchlist)

    output = resolve_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output, index=False)
    counts = pd.Series([row["status"] for row in rows]).value_counts().to_dict()
    print(f"resolved candidate rows written: {relative(output)}")
    print(
        "resolution summary: "
        + ", ".join(f"{status} {counts.get(status, 0)}" for status in ["resolved", "unresolved", "duplicate", "existing"])
    )
    print(f"downloadable resolved ETFs: {counts.get('resolved', 0)}")


def resolve_candidates(candidates: pd.DataFrame, jqdata: pd.DataFrame, watchlist: pd.DataFrame) -> list[dict]:
    jqdata = prepare_jqdata(jqdata)
    existing_codes = set(watchlist.get("code", pd.Series(dtype=str)).astype(str))
    seen_resolved: set[str] = set()
    rows: list[dict] = []

    for _, candidate in candidates.iterrows():
        code = str(candidate["code"])
        if is_six_digit_code(code):
            matches = direct_code_match(code, jqdata)
        else:
            matches = keyword_matches(candidate, jqdata)

        if not matches:
            rows.append(build_row(candidate, None, "", 0, "unresolved", unresolved_reason(candidate)))
            continue

        for match_rank, match in enumerate(matches, start=1):
            resolved_code = str(match["jq_code"])
            base_code = resolved_code.split(".")[0]
            if base_code in existing_codes:
                status = "existing"
                reason = "resolved code is already in current watchlist"
            elif resolved_code in seen_resolved:
                status = "duplicate"
                reason = "another expansion candidate already resolved to this JQData ETF"
            elif match_rank > 1 and not code.startswith("PENDING_"):
                status = "duplicate"
                reason = "extra match for a concrete six-digit seed"
            else:
                status = "resolved"
                reason = "resolved by direct code" if is_six_digit_code(code) else "resolved by keyword match"
                seen_resolved.add(resolved_code)
            rows.append(build_row(candidate, match, match["match_keyword"], match["score"], status, reason))
    return rows


def prepare_jqdata(jqdata: pd.DataFrame) -> pd.DataFrame:
    df = jqdata.copy()
    for col in ["code", "display_name", "name", "exchange", "start_date", "source"]:
        if col not in df.columns:
            df[col] = ""
    df["code"] = df["code"].astype(str)
    df["exchange"] = df["exchange"].astype(str)
    df["jq_code"] = df.apply(lambda row: to_jq_code(row["code"], row["exchange"]), axis=1)
    df["search_text"] = (df["display_name"].astype(str) + " " + df["name"].astype(str)).str.upper()
    return df


def direct_code_match(code: str, jqdata: pd.DataFrame) -> list[dict]:
    subset = jqdata[jqdata["code"].astype(str) == code]
    if subset.empty:
        return [
            {
                "code": code,
                "jq_code": to_jq_code(code, ""),
                "display_name": "",
                "name": "",
                "exchange": infer_exchange(code),
                "start_date": "",
                "source": "direct_six_digit_candidate",
                "match_keyword": code,
                "score": 100,
            }
        ]
    return [record_from_row(subset.iloc[0], code, 100)]


def keyword_matches(candidate: pd.Series, jqdata: pd.DataFrame) -> list[dict]:
    rule = KEYWORD_RULES.get(str(candidate["code"]), infer_rule(candidate))
    scored: list[dict] = []
    for _, row in jqdata.iterrows():
        text = str(row["search_text"])
        if any(ban.upper() in text for ban in rule.banned):
            continue
        if rule.required_any and not any(keyword.upper() in text for keyword in rule.required_any):
            continue
        score = 0
        hit_keywords = []
        for keyword in rule.keywords:
            upper = keyword.upper()
            if upper and upper in text:
                hit_keywords.append(keyword)
                score += 10 + min(len(keyword), 8)
                if upper in str(row["display_name"]).upper():
                    score += 4
        if "ETF" in str(row["display_name"]).upper():
            score += 2
        if score >= MIN_MATCH_SCORE and hit_keywords:
            scored.append(record_from_row(row, "/".join(hit_keywords), score))
    scored.sort(key=lambda item: (-item["score"], item["start_date"], item["jq_code"]))
    return scored[: rule.max_matches]


def infer_rule(candidate: pd.Series) -> KeywordRule:
    text = " ".join([str(candidate.get("name", "")), str(candidate.get("group", "")), str(candidate.get("reason", ""))])
    keywords = []
    for keyword in [
        "中证A500",
        "A50",
        "中证2000",
        "科创100",
        "科创200",
        "北证50",
        "机器人",
        "半导体设备",
        "人工智能",
        "算力",
        "数据中心",
        "通信设备",
        "信创",
        "信息安全",
        "工业母机",
        "高端装备",
        "低空经济",
        "商业航天",
        "创新药",
        "港股创新药",
        "生物科技",
        "医疗器械",
        "红利质量",
        "质量低波",
        "自由现金流",
        "公用事业",
        "电力",
        "港股高股息",
        "铜",
        "工业金属",
        "油气",
        "化工",
        "黄金股",
        "钢铁",
        "建材",
        "新材料",
        "港股互联网",
        "港股科技",
        "日经",
        "德国",
        "东南亚",
        "新兴市场",
        "印度",
        "政金债",
        "信用债",
        "可转债",
        "短债",
    ]:
        if keyword in text:
            keywords.append(keyword)
    return KeywordRule(tuple(keywords), tuple(keywords[:1]), max_matches=1) if keywords else KeywordRule(())


def record_from_row(row: pd.Series, match_keyword: str, score: int) -> dict:
    return {
        "code": str(row["code"]),
        "jq_code": str(row["jq_code"]),
        "display_name": str(row.get("display_name", "")),
        "name": str(row.get("name", "")),
        "exchange": str(row.get("exchange", "")),
        "start_date": str(row.get("start_date", "")),
        "source": str(row.get("source", "")),
        "match_keyword": match_keyword,
        "score": score,
    }


def build_row(candidate: pd.Series, match: dict | None, keyword: str, score: int, status: str, reason: str) -> dict:
    return {
        "original_code": str(candidate.get("code", "")),
        "original_name": str(candidate.get("name", "")),
        "resolved_jq_code": "" if match is None else match["jq_code"],
        "resolved_display_name": "" if match is None else match["display_name"],
        "resolved_name": "" if match is None else match["name"],
        "exchange": "" if match is None else match["exchange"],
        "start_date": "" if match is None else match["start_date"],
        "match_keyword": keyword,
        "match_score": score,
        "source": "" if match is None else match["source"],
        "pool": str(candidate.get("pool", "")),
        "group": str(candidate.get("group", "")),
        "strategy": str(candidate.get("strategy", "")),
        "priority": str(candidate.get("priority", "")),
        "status": status,
        "reason": reason,
    }


def unresolved_reason(candidate: pd.Series) -> str:
    code = str(candidate.get("code", ""))
    if is_six_digit_code(code):
        return "six-digit candidate not found in JQData list; keep unresolved for manual check"
    return "no confident keyword match in JQData ETF candidate list"


def read_watchlist() -> pd.DataFrame:
    if not WATCHLIST_PATH.exists():
        return pd.DataFrame(columns=["code"])
    return pd.read_csv(WATCHLIST_PATH, dtype=str).fillna("")


def is_six_digit_code(value: str) -> bool:
    return bool(re.fullmatch(r"\d{6}", str(value)))


def infer_exchange(code: str) -> str:
    if str(code).startswith(("5", "6")):
        return "XSHG"
    if str(code).startswith(("0", "1", "3")):
        return "XSHE"
    return "XSHG"


def to_jq_code(code: str, exchange: str) -> str:
    code = str(code).split(".")[0]
    exchange = str(exchange) if exchange else infer_exchange(code)
    return f"{code}.{exchange}"


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()
