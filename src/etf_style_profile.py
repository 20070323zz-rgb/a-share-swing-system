"""ETF style profile helper.

Research-only classifier for stable ETF style and structural risk attributes.
It does not modify rankings, paper trades, paper positions, strategy rules, or
execution code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config import PROJECT_ROOT


CONFIG_DIR = PROJECT_ROOT / "configs"
STYLE_OVERRIDE_FILE = CONFIG_DIR / "etf_style_override.csv"

STYLE_VALUES = {
    "BOND",
    "DIVIDEND",
    "LOW_VOL",
    "CORE_LARGE_CAP",
    "CORE_MID_CAP",
    "GROWTH_BROAD",
    "GROWTH_THEME",
    "SECTOR_CYCLICAL",
    "SECTOR_DEFENSIVE",
    "HIGH_BETA_THEME",
    "COMMODITY_CYCLICAL",
    "QDII_OBSERVATION",
    "UNKNOWN",
}

PROFILE_ORDER = {"DEFENSIVE": 1, "CORE": 2, "BALANCED": 3, "OFFENSIVE": 4, "HIGH_BETA": 5}
ORDER_PROFILE = {value: key for key, value in PROFILE_ORDER.items()}


def load_style_overrides(path: Path = STYLE_OVERRIDE_FILE) -> dict[str, dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")
    except Exception:
        return {}
    result: dict[str, dict[str, str]] = {}
    for _, row in df.iterrows():
        symbol = _clean_symbol(row.get("symbol"))
        if not symbol:
            continue
        style = str(row.get("style_profile", "")).strip().upper()
        structural = str(row.get("structural_risk_override", "")).strip().upper()
        result[symbol] = {
            "style_profile": style if style in STYLE_VALUES else "",
            "structural_risk_override": structural if structural in PROFILE_ORDER else "",
            "reason": str(row.get("reason", "")).strip(),
        }
    return result


def classify_style_profile(symbol: str, name: str, group: str, etf_type: str, flags: dict[str, bool], override: dict[str, str] | None = None) -> tuple[str, bool, str]:
    override = override or {}
    if override.get("style_profile"):
        return override["style_profile"], True, override.get("reason", "manual style override")

    text = f"{symbol} {name} {group} {etf_type}"
    if flags.get("is_bond"):
        return "BOND", False, "bond/cash asset type"
    if flags.get("is_qdii"):
        return "QDII_OBSERVATION", False, "QDII or cross-border name/group"
    if _has(text, ["红利", "高股息", "央企红利", "红利质量", "股息", "分红"]):
        return "DIVIDEND", False, "dividend keyword"
    if _has(text, ["低波", "低波动", "质量低波"]) and not _has(text, ["创业", "科创", "科技", "芯片", "半导体"]):
        return "LOW_VOL", False, "low-vol keyword"

    if _has(text, ["沪深300", "上证50", "上证180", "中证a50", "a50", "中证a500", "a500", "300esg", "央企etf", "国企etf"]):
        return "CORE_LARGE_CAP", False, "traditional large/core broad keyword"
    if _has(text, ["中证500", "中证1000", "中证2000", "深100"]) or flags.get("is_broad_base"):
        return "CORE_MID_CAP", False, "mid/small broad index keyword"
    if _has(text, ["创业板", "科创50", "科创100", "科创200", "科创创业", "双创", "北证50"]):
        return "GROWTH_BROAD", False, "growth broad index keyword"

    if _has(text, ["证券", "券商", "非银", "保险证券"]):
        return "SECTOR_CYCLICAL", False, "financial beta/cyclical keyword"
    if _has(text, ["煤炭", "有色", "稀土", "黄金股", "钢铁", "能源", "油气", "石油", "化工", "资源", "建材", "新材料", "稀有金属", "工业金属", "铜"]):
        return "COMMODITY_CYCLICAL", False, "resource/commodity cyclical keyword"
    if _has(text, ["银行", "公用事业", "电力", "绿色电力", "绿电"]):
        return "SECTOR_DEFENSIVE", False, "defensive sector keyword"
    if _has(text, ["医药", "医疗", "医疗器械", "消费", "食品", "食品饮料", "家电", "农业", "养殖", "旅游"]):
        return "SECTOR_DEFENSIVE", False, "consumer/healthcare defensive sector keyword"

    high_beta_theme_keywords = ["机器人", "低空", "商业航天", "ai", "人工智能", "算力", "芯片", "半导体", "半导体设备", "信创", "信息安全", "工业母机", "机床", "高端装备", "数字经济", "智能汽车", "新能源", "光伏", "电池", "锂电", "游戏", "传媒", "电子"]
    if _has(text, high_beta_theme_keywords):
        return "HIGH_BETA_THEME" if flags.get("is_high_beta") else "GROWTH_THEME", False, "growth/high-beta theme keyword"
    if _has(text, ["创新药", "生物科技", "生物医药"]):
        return "GROWTH_THEME", False, "innovation drug/biotech growth keyword"
    if flags.get("is_theme"):
        return "GROWTH_THEME" if flags.get("is_growth") else "HIGH_BETA_THEME", False, "theme flag fallback"
    if flags.get("is_sector"):
        return "SECTOR_CYCLICAL", False, "sector flag fallback"
    return "UNKNOWN", False, "insufficient metadata for automatic style classification"


def structural_risk_components(row: dict[str, Any]) -> dict[str, Any]:
    style = str(row.get("style_profile") or "UNKNOWN")
    text = f"{row.get('symbol','')} {row.get('name','')} {row.get('group','')} {row.get('type','')} {style}"
    asset_score = {
        "BOND": 8,
        "LOW_VOL": 20,
        "DIVIDEND": 28,
        "CORE_LARGE_CAP": 35,
        "CORE_MID_CAP": 45,
        "GROWTH_BROAD": 58,
        "SECTOR_DEFENSIVE": 50,
        "SECTOR_CYCLICAL": 66,
        "COMMODITY_CYCLICAL": 72,
        "GROWTH_THEME": 74,
        "HIGH_BETA_THEME": 86,
        "QDII_OBSERVATION": 58,
        "UNKNOWN": 55,
    }.get(style, 55)
    style_score = {
        "BOND": 8,
        "LOW_VOL": 18,
        "DIVIDEND": 30,
        "CORE_LARGE_CAP": 38,
        "CORE_MID_CAP": 46,
        "GROWTH_BROAD": 60,
        "SECTOR_DEFENSIVE": 48,
        "SECTOR_CYCLICAL": 68,
        "COMMODITY_CYCLICAL": 75,
        "GROWTH_THEME": 76,
        "HIGH_BETA_THEME": 90,
        "QDII_OBSERVATION": 60,
        "UNKNOWN": 55,
    }.get(style, 55)
    if _bool(row.get("is_high_beta")):
        style_score = max(style_score, 82)
    if _bool(row.get("is_dividend")) or _bool(row.get("is_low_vol")):
        style_score = min(style_score, 35)

    metric_values = [
        _threshold_score(_float(row.get("volatility_120d")), [(0.08, 10), (0.16, 30), (0.25, 55), (0.35, 75)], 90),
        _threshold_score(_float(row.get("beta_120d")), [(0.40, 15), (0.80, 35), (1.10, 55), (1.40, 75)], 90),
        _threshold_score(abs(_float(row.get("max_drawdown_120d"))), [(0.03, 12), (0.08, 35), (0.15, 58), (0.25, 78)], 92),
        _threshold_score(_float(row.get("down_capture_60d")), [(0.30, 15), (0.70, 35), (1.10, 58), (1.50, 78)], 92),
    ]
    metric_values = [value for value in metric_values if value is not None]
    long_risk_score = sum(metric_values) / len(metric_values) if metric_values else 55.0

    concentration_score = 45
    if _bool(row.get("is_bond")):
        concentration_score = 8
    elif _bool(row.get("is_broad_base")):
        concentration_score = 30
    elif _bool(row.get("is_quasi_broad_base")):
        concentration_score = 48
    elif _bool(row.get("is_theme")):
        concentration_score = 80
    elif _bool(row.get("is_sector")):
        concentration_score = 68
    if style == "UNKNOWN":
        concentration_score = max(concentration_score, 58)
    if _has(text, ["证券", "券商", "非银", "保险证券"]):
        asset_score = max(asset_score, 82)
        style_score = max(style_score, 86)
        concentration_score = max(concentration_score, 82)

    raw_score = 0.30 * asset_score + 0.25 * style_score + 0.35 * long_risk_score + 0.10 * concentration_score
    return {
        "asset_class_score": round(asset_score, 4),
        "style_attribute_score": round(style_score, 4),
        "long_cycle_risk_score": round(long_risk_score, 4),
        "concentration_adjustment_score": round(concentration_score, 4),
        "structural_risk_score": round(max(0.0, min(100.0, raw_score)), 4),
        "structural_risk_reason": (
            f"asset={asset_score:.1f}; style={style_score:.1f}; long_cycle={long_risk_score:.1f}; "
            f"concentration={concentration_score:.1f}; weights=30/25/35/10"
        ),
    }


def structural_profile_from_score(score: float, row: dict[str, Any], override: dict[str, str] | None = None) -> tuple[str, bool, str]:
    override = override or {}
    profile = _profile_from_threshold(score)
    reasons = []
    overridden = False

    if row.get("style_profile") == "BOND" and PROFILE_ORDER[profile] > PROFILE_ORDER["CORE"]:
        profile = "CORE"
        overridden = True
        reasons.append("BOND structural cap to CORE")
    if row.get("style_profile") == "HIGH_BETA_THEME" and PROFILE_ORDER[profile] < PROFILE_ORDER["OFFENSIVE"]:
        profile = "OFFENSIVE"
        overridden = True
        reasons.append("HIGH_BETA_THEME structural floor to OFFENSIVE")
    text = f"{row.get('symbol','')} {row.get('name','')} {row.get('group','')} {row.get('type','')}"
    if _has(text, ["证券", "券商", "非银", "保险证券"]) and PROFILE_ORDER[profile] < PROFILE_ORDER["HIGH_BETA"]:
        profile = "HIGH_BETA"
        overridden = True
        reasons.append("securities ETF structural high-beta floor")
    if row.get("style_profile") in {"CORE_LARGE_CAP", "CORE_MID_CAP"} and PROFILE_ORDER[profile] > PROFILE_ORDER["OFFENSIVE"]:
        profile = "OFFENSIVE"
        overridden = True
        reasons.append("core broad structural cap to OFFENSIVE")
    if override.get("structural_risk_override"):
        profile = override["structural_risk_override"]
        overridden = True
        reasons.append(override.get("reason") or "manual structural risk override")
    return profile, overridden, "; ".join(reasons)


def _profile_from_threshold(score: float) -> str:
    if score < 25:
        return "DEFENSIVE"
    if score < 45:
        return "CORE"
    if score < 60:
        return "BALANCED"
    if score < 80:
        return "OFFENSIVE"
    return "HIGH_BETA"


def _threshold_score(value: float | None, buckets: list[tuple[float, int]], high_score: int) -> float | None:
    if value is None or pd.isna(value):
        return None
    for threshold, score in buckets:
        if value <= threshold:
            return float(score)
    return float(high_score)


def _has(text: str, keywords: list[str]) -> bool:
    lowered = str(text or "").lower()
    return any(str(keyword).lower() in lowered for keyword in keywords)


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "是"}


def _float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number


def _clean_symbol(value: object) -> str:
    import re

    match = re.search(r"(\d{6})", str(value or ""))
    return match.group(1) if match else ""


def main() -> None:
    profile_file = PROJECT_ROOT / "reports" / "etf_risk_profile.csv"
    if not profile_file.exists():
        print("reports/etf_risk_profile.csv not found; run python3 src/etf_risk_profile.py first.")
        return
    df = pd.read_csv(profile_file, dtype=str, keep_default_na=False)
    counts = df.get("style_profile", pd.Series(dtype=str)).value_counts().to_dict()
    print(f"style_profile rows: {len(df)}")
    print(f"style_profile distribution: {counts}")


if __name__ == "__main__":
    main()
