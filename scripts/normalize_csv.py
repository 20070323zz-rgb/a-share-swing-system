"""把手动下载的日线 CSV 标准化为系统格式。

本脚本只读取本地 CSV 并写入 data/<code>.csv，不连接券商，不下单，
不读取账号、密码、验证码或 token。
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_COLUMNS = ["date", "open", "high", "low", "close", "volume"]

COLUMN_MAP = {
    "日期": "date",
    "交易日期": "date",
    "时间": "date",
    "开盘": "open",
    "开盘价": "open",
    "最高": "high",
    "最高价": "high",
    "最低": "low",
    "最低价": "low",
    "收盘": "close",
    "收盘价": "close",
    "成交量": "volume",
    "date": "date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="标准化手动下载的 ETF/股票日线 CSV")
    parser.add_argument("--input", required=True, help="原始 CSV 路径，例如 raw/512880.csv")
    parser.add_argument("--code", required=True, help="证券代码，例如 512880")
    parser.add_argument("--output-dir", default=str(DATA_DIR), help="输出目录，默认 data/")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    df = read_csv(input_path)
    normalized = normalize_daily_csv(df)
    output_path = output_dir / f"{args.code}.csv"
    normalized.to_csv(output_path, index=False)
    print(f"已生成 {output_path}")
    print(f"字段：{','.join(OUTPUT_COLUMNS)}")
    print(f"行数：{len(normalized)}")


def read_csv(path: Path) -> pd.DataFrame:
    """读取 CSV，兼容常见 UTF-8 和 GBK 编码。"""
    if not path.exists():
        raise FileNotFoundError(f"找不到输入文件：{path}")
    errors = []
    for encoding in ["utf-8-sig", "utf-8", "gbk", "gb18030"]:
        try:
            return pd.read_csv(path, encoding=encoding)
        except Exception as exc:
            errors.append(f"{encoding}: {exc}")
    raise RuntimeError("CSV 读取失败；尝试过的编码：" + "；".join(errors))


def normalize_daily_csv(raw: pd.DataFrame) -> pd.DataFrame:
    """把中文或英文日线字段统一成 date,open,high,low,close,volume。"""
    rename_map = {}
    for col in raw.columns:
        key = str(col).strip()
        if key in COLUMN_MAP:
            rename_map[col] = COLUMN_MAP[key]
        elif key.lower() in COLUMN_MAP:
            rename_map[col] = COLUMN_MAP[key.lower()]

    df = raw.rename(columns=rename_map).copy()
    missing = [col for col in OUTPUT_COLUMNS if col not in df.columns]
    if missing:
        original_columns = ", ".join(str(col) for col in raw.columns)
        raise ValueError(f"字段缺失：{', '.join(missing)}。原始字段：{original_columns}")

    df = df[OUTPUT_COLUMNS].copy()
    df["date"] = parse_date(df["date"])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=OUTPUT_COLUMNS)
    df = df.drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date").reset_index(drop=True)
    if df.empty:
        raise ValueError("标准化后没有可用行情行，请检查日期、价格和成交量字段。")
    return df


def parse_date(series: pd.Series) -> pd.Series:
    """兼容 2026-05-29 和 20260529 两种常见日期。"""
    text = series.astype(str).str.strip()
    parsed = pd.to_datetime(text, errors="coerce")
    fallback_mask = parsed.isna() & text.str.fullmatch(r"\d{8}")
    parsed.loc[fallback_mask] = pd.to_datetime(text.loc[fallback_mask], format="%Y%m%d", errors="coerce")
    return parsed.dt.strftime("%Y-%m-%d")


if __name__ == "__main__":
    main()
