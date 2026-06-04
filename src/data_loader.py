"""读取观察名单、交易记录和本地日线行情。"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


WATCHLIST_COLUMNS = ["code", "name", "type", "source", "enabled", "benchmark_code", "group", "role", "preferred_strategy", "note"]
TRADES_COLUMNS = [
    "date",
    "code",
    "name",
    "type",
    "action",
    "price",
    "shares",
    "amount",
    "fee",
    "reason",
    "cash_after",
    "position_after",
    "is_simulated",
    "strategy",
]

COLUMN_MAP = {
    "日期": "date",
    "交易日期": "date",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交量": "volume",
    "成交额": "amount",
    "代码": "code",
    "名称": "name",
}
REQUIRED_PRICE_COLUMNS = ["date", "open", "high", "low", "close", "volume"]


def ensure_watchlist_template(path: Path) -> None:
    """如果观察名单不存在，自动生成示例模板。"""
    if path.exists():
        return
    template = pd.DataFrame(
        [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF", "source": "auto", "enabled": 1, "benchmark_code": "510300", "group": "宽基", "role": "trade_pool", "preferred_strategy": "mid_trend", "note": "核心宽基基准"},
            {"code": "513500", "name": "标普500ETF", "type": "ETF", "source": "auto", "enabled": 0, "benchmark_code": "510300", "group": "QDII观察", "role": "observe_pool", "preferred_strategy": "observe", "note": "长期基金观察"},
            {"code": "159915", "name": "创业板ETF", "type": "ETF", "source": "auto", "enabled": 1, "benchmark_code": "510300", "group": "宽基", "role": "trade_pool", "preferred_strategy": "both", "note": "成长风格"},
        ]
    )
    template.to_csv(path, index=False)


def ensure_trades_template(path: Path) -> None:
    """如果模拟交易记录不存在，自动生成空模板。"""
    if path.exists():
        return
    pd.DataFrame(columns=TRADES_COLUMNS).to_csv(path, index=False)


def read_watchlist(path: Path) -> pd.DataFrame:
    """读取观察名单，按字段名补齐默认值，不依赖字段顺序。"""
    ensure_watchlist_template(path)
    df = pd.read_csv(path, dtype={"code": str, "benchmark_code": str})
    if "note" not in df.columns and "notes" in df.columns:
        df["note"] = df["notes"]
    defaults = {
        "name": "",
        "type": "ETF",
        "source": "auto",
        "enabled": 1,
        "benchmark_code": "510300",
        "group": "未分类",
        "role": "trade_pool",
        "preferred_strategy": "both",
        "note": "",
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    df["code"] = df["code"].astype(str).str.strip()
    df["name"] = df["name"].fillna(df["code"]).astype(str).str.strip()
    df["type"] = df["type"].apply(normalize_security_type)
    df["source"] = df["source"].fillna("auto").astype(str).str.lower().str.strip()
    df["enabled"] = df["enabled"].apply(is_enabled_value)
    df["benchmark_code"] = df["benchmark_code"].fillna("510300").astype(str).str.strip()
    df["group"] = df["group"].fillna("未分类").astype(str).str.strip()
    df["role"] = df["role"].fillna("trade_pool").astype(str).str.lower().str.strip()
    df.loc[~df["role"].isin(["trade_pool", "observe_pool"]), "role"] = "trade_pool"
    df["preferred_strategy"] = df["preferred_strategy"].fillna("both").astype(str).str.lower().str.strip()
    df.loc[~df["preferred_strategy"].isin(["mid_trend", "short_swing", "both", "observe"]), "preferred_strategy"] = "both"
    df["note"] = df["note"].fillna("").astype(str)
    return df[WATCHLIST_COLUMNS].copy()


def is_enabled_value(value: object) -> bool:
    """兼容 1、'1'、1.0、True、'true' 等启用值。"""
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "1.0", "true", "yes", "y", "启用"}


def normalize_security_type(value: object) -> str:
    """把 ETF/STOCK 等类型统一为内部类型。"""
    text = str(value).strip().lower()
    if text in {"etf", "a_share_etf", "ashare_etf", "a-share-etf"}:
        return "ETF"
    if text in {"stock", "a_share_stock", "ashare_stock", "a-share-stock"}:
        return "STOCK"
    return str(value).strip().upper() or "ETF"


def read_trades(path: Path) -> pd.DataFrame:
    """读取手工维护的模拟成交记录。空文件会返回空表。"""
    df, _ = read_trades_with_validation(path)
    return df


def read_trades_with_validation(path: Path) -> tuple[pd.DataFrame, list[str]]:
    """读取并校验 trades.csv，错误会返回为提示文字而不是让程序崩溃。"""
    ensure_trades_template(path)
    if not path.exists() or path.stat().st_size == 0:
        ensure_trades_template(path)
        return _empty_trades(), []

    try:
        df = pd.read_csv(path, dtype={"code": str})
    except Exception as exc:
        return _empty_trades(), [f"trades.csv 读取失败：{exc}"]

    if df.empty:
        return _empty_trades(), []

    warnings = validate_trades(df)
    missing = [col for col in TRADES_COLUMNS if col not in df.columns]
    for col in missing:
        df[col] = "mid_trend" if col == "strategy" else ""

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["price", "shares", "amount", "fee"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["action"] = df["action"].astype(str).str.upper()
    df["strategy"] = df["strategy"].fillna("mid_trend").astype(str).str.lower().str.strip()
    df.loc[~df["strategy"].isin(["mid_trend", "short_swing"]), "strategy"] = "mid_trend"
    df = df.dropna(subset=["date", "code", "action"])
    df = df[(df["price"] > 0) & (df["shares"] > 0)]
    return df.sort_values("date"), warnings


def validate_trades(df: pd.DataFrame) -> list[str]:
    """检查模拟成交记录字段、日期、价格、数量和动作是否合法。"""
    warnings: list[str] = []
    missing = [col for col in TRADES_COLUMNS if col not in df.columns]
    if missing:
        warnings.append(f"trades.csv 缺少字段：{', '.join(missing)}")
        return warnings

    valid_actions = {"BUY", "SELL"}
    for idx, row in df.iterrows():
        line_no = idx + 2
        date_value = pd.to_datetime(row["date"], errors="coerce")
        price = pd.to_numeric(row["price"], errors="coerce")
        shares = pd.to_numeric(row["shares"], errors="coerce")
        action = str(row["action"]).upper()
        if pd.isna(date_value):
            warnings.append(f"trades.csv 第 {line_no} 行日期不合法：{row['date']}")
        if pd.isna(price) or float(price) <= 0:
            warnings.append(f"trades.csv 第 {line_no} 行价格必须大于 0")
        if pd.isna(shares) or float(shares) <= 0:
            warnings.append(f"trades.csv 第 {line_no} 行数量必须大于 0")
        if action not in valid_actions:
            warnings.append(f"trades.csv 第 {line_no} 行 action 只能是 BUY 或 SELL")
    return warnings


def load_price_data(data_dir: Path, code: str) -> tuple[pd.DataFrame | None, str | None]:
    """读取单个标的的日线 CSV。

    兼容 data/etf_daily、data/raw 和 data/ 下的多种文件名格式。
    """
    path = find_price_file(data_dir, code)
    if path is None:
        names = ", ".join(candidate.name for candidate in build_price_file_candidates(data_dir, code)[:4])
        return None, f"缺少行情文件：{names}"

    df = _read_price_csv(path)
    df = df.rename(columns={col: COLUMN_MAP.get(col, col) for col in df.columns})
    missing = [col for col in REQUIRED_PRICE_COLUMNS if col not in df.columns]
    if missing:
        return None, f"{path.name} 缺少字段：{', '.join(missing)}"

    df["date"] = _parse_date(df["date"])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=REQUIRED_PRICE_COLUMNS).sort_values("date").drop_duplicates("date")
    if df.empty:
        return None, f"{path.name} 没有可用行情"

    df["code"] = code
    return df.reset_index(drop=True), None


def find_price_file(data_dir: Path, code: str) -> Path | None:
    """按项目约定寻找本地行情文件。"""
    for path in build_price_file_candidates(data_dir, code):
        if path.exists() and path.is_file():
            return path
    return None


def build_price_file_candidates(data_dir: Path, code: str) -> list[Path]:
    """生成本地行情文件候选路径，越靠前优先级越高。"""
    clean_code = str(code).strip()
    market = market_prefix(clean_code)
    upper_market = market.upper()
    names = [
        f"{market}_{clean_code}.csv",
        f"{market}.{clean_code}.csv",
        f"{clean_code}.{upper_market}.csv",
        f"{clean_code}.csv",
    ]
    dirs = _candidate_data_dirs(data_dir)
    return [directory / name for directory in dirs for name in names]


def market_prefix(code: str) -> str:
    """把 A 股/ETF 代码转换为 sh 或 sz 前缀。"""
    text = str(code).strip()
    if text.startswith(("6", "510", "511", "512", "513", "515", "516", "518", "588")):
        return "sh"
    if text.startswith(("0", "3", "159")):
        return "sz"
    return "sh"


def baostock_code(code: str) -> str:
    """返回 BaoStock 使用的 sh.510300 / sz.159915 格式。"""
    text = str(code).strip()
    return f"{market_prefix(text)}.{text}"


def _parse_date(series: pd.Series) -> pd.Series:
    """兼容 2026-05-29 和 20260529 两种常见日期格式。"""
    text = series.astype(str).str.strip()
    parsed = pd.to_datetime(text, errors="coerce")
    fallback_mask = parsed.isna() & text.str.fullmatch(r"\d{8}")
    parsed.loc[fallback_mask] = pd.to_datetime(text.loc[fallback_mask], format="%Y%m%d", errors="coerce")
    return parsed


def _candidate_data_dirs(data_dir: Path) -> list[Path]:
    data_dir = Path(data_dir)
    names = {data_dir.name.lower()}
    if "etf_daily" in names or "raw" in names:
        return [data_dir]
    return [data_dir / "etf_daily", data_dir / "raw", data_dir]


def _read_price_csv(path: Path) -> pd.DataFrame:
    errors: list[str] = []
    for encoding in ["utf-8-sig", "utf-8", "gbk", "gb18030"]:
        try:
            return pd.read_csv(path, dtype={"code": str}, encoding=encoding)
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")
    if errors:
        raise RuntimeError(f"{path.name} 编码读取失败：{'; '.join(errors)}")
    return pd.read_csv(path, dtype={"code": str})


def _empty_trades() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "date",
            "code",
            "name",
            "type",
            "action",
            "price",
            "shares",
            "amount",
            "fee",
            "reason",
            "cash_after",
            "position_after",
            "is_simulated",
            "strategy",
        ]
    )
