"""本地行情数据覆盖检查。

本模块只读取 watchlist.csv 和本地 CSV，不联网，不连接券商，不下单。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import DATA_COVERAGE_REPORT_FILE, DATA_DIR, ETF_DAILY_DIR, LATEST_DATA_COVERAGE_FILE, PROJECT_ROOT, WATCHLIST_FILE
from data_loader import COLUMN_MAP, REQUIRED_PRICE_COLUMNS, find_price_file, read_formal_data_universe


STALE_DAYS = 10


def write_data_coverage_report(watchlist: pd.DataFrame | None = None) -> tuple[Path, dict]:
    """生成数据覆盖报告，并返回摘要供 latest_brief 使用。"""
    if watchlist is None:
        watchlist = read_formal_data_universe(WATCHLIST_FILE, ETF_DAILY_DIR, PROJECT_ROOT / "data" / "etf_pool_expansion_candidates.csv")
    rows = build_coverage_rows(watchlist)
    df = pd.DataFrame(rows)
    summary = summarize_coverage(df)
    lines = _build_report_lines(df, summary)
    DATA_COVERAGE_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    LATEST_DATA_COVERAGE_FILE.write_text(DATA_COVERAGE_REPORT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    return DATA_COVERAGE_REPORT_FILE, summary


def build_coverage_rows(watchlist: pd.DataFrame) -> list[dict]:
    """逐标的检查本地 CSV 覆盖情况。"""
    rows: list[dict] = []
    for _, item in watchlist.iterrows():
        code = str(item.get("code", "")).strip()
        path = find_price_file(DATA_DIR, code)
        row = {
            "code": code,
            "name": item.get("name", code),
            "type": item.get("type", ""),
            "pool": item.get("role", ""),
            "group": item.get("group", ""),
            "file_path": "",
            "rows": 0,
            "start_date": "",
            "end_date": "",
            "latest_date": "",
            "has_required_fields": False,
            "valid_data": False,
            "is_stale": False,
            "message": "缺少本地 CSV",
        }
        if path is None:
            rows.append(row)
            continue

        row["file_path"] = _relative_path(path)
        try:
            df = _read_csv(path)
        except Exception as exc:
            row["message"] = f"CSV 读取失败：{exc}"
            rows.append(row)
            continue

        df = df.rename(columns={col: COLUMN_MAP.get(str(col).strip(), col) for col in df.columns})
        missing = [col for col in REQUIRED_PRICE_COLUMNS if col not in df.columns]
        row["has_required_fields"] = not missing
        row["rows"] = len(df)
        if missing:
            row["message"] = "缺少必要字段：" + ", ".join(missing)
            rows.append(row)
            continue

        dates = pd.to_datetime(df["date"], errors="coerce").dropna()
        if dates.empty:
            row["message"] = "date 字段无法解析"
            rows.append(row)
            continue

        row["start_date"] = dates.min().strftime("%Y-%m-%d")
        row["end_date"] = dates.max().strftime("%Y-%m-%d")
        row["latest_date"] = row["end_date"]
        row["valid_data"] = len(df) > 0
        row["is_stale"] = _is_stale(dates.max())
        row["message"] = "有效" if not row["is_stale"] else "数据最近日期偏旧"
        rows.append(row)
    return rows


def summarize_coverage(df: pd.DataFrame) -> dict:
    """汇总覆盖情况。"""
    if df.empty:
        return {
            "total": 0,
            "valid": 0,
            "missing": 0,
            "stale": 0,
            "etf_total": 0,
            "etf_valid": 0,
            "etf_missing": 0,
            "trade_pool_total": 0,
            "trade_pool_valid": 0,
            "trade_pool_rate": 0.0,
            "observe_pool_total": 0,
            "observe_pool_valid": 0,
            "observe_pool_missing": 0,
            "observe_pool_rate": 0.0,
            "research_only_total": 0,
            "research_only_valid": 0,
            "research_only_missing": 0,
            "research_only_rate": 0.0,
            "stock_observe_total": 0,
            "stock_observe_missing": 0,
        }
    valid = df["valid_data"].astype(bool)
    trade = df["pool"].astype(str) == "trade_pool"
    observe = df["pool"].astype(str) == "observe_pool"
    research = df["pool"].astype(str) == "research_only"
    etf = df["type"].astype(str).str.upper() == "ETF"
    stock_observe = observe & (df["type"].astype(str).str.upper() == "STOCK")
    return {
        "total": int(len(df)),
        "valid": int(valid.sum()),
        "missing": int((~valid).sum()),
        "stale": int((df["is_stale"].astype(bool) & valid).sum()),
        "etf_total": int(etf.sum()),
        "etf_valid": int((etf & valid).sum()),
        "etf_missing": int((etf & ~valid).sum()),
        "trade_pool_total": int(trade.sum()),
        "trade_pool_valid": int((trade & valid).sum()),
        "trade_pool_rate": _rate((trade & valid).sum(), trade.sum()),
        "observe_pool_total": int(observe.sum()),
        "observe_pool_valid": int((observe & valid).sum()),
        "observe_pool_missing": int((observe & ~valid).sum()),
        "observe_pool_rate": _rate((observe & valid).sum(), observe.sum()),
        "research_only_total": int(research.sum()),
        "research_only_valid": int((research & valid).sum()),
        "research_only_missing": int((research & ~valid).sum()),
        "research_only_rate": _rate((research & valid).sum(), research.sum()),
        "stock_observe_total": int(stock_observe.sum()),
        "stock_observe_missing": int((stock_observe & ~valid).sum()),
    }


def _build_report_lines(df: pd.DataFrame, summary: dict) -> list[str]:
    lines = [
        f"# 本地数据覆盖报告 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "本报告只检查本地 CSV 覆盖情况，不联网，不接券商 API，不下单。",
        "",
        "## 摘要",
        f"- ETF/观察池总数：{summary['total']}",
        f"- ETF 总数：{summary.get('etf_total', 0)}",
        f"- ETF 数据缺失数量：{summary.get('etf_missing', 0)}",
        f"- 个股观察缺失数量：{summary.get('stock_observe_missing', 0)}",
        f"- 有效数据数量：{summary['valid']}",
        f"- 缺失或无效数据数量：{summary['missing']}",
        f"- 数据过期数量：{summary['stale']}",
        f"- trade_pool 覆盖率：{summary['trade_pool_valid']}/{summary['trade_pool_total']} = {summary['trade_pool_rate']:.2%}",
        f"- observe_pool 覆盖率：{summary['observe_pool_valid']}/{summary['observe_pool_total']} = {summary['observe_pool_rate']:.2%}",
        f"- research_only 覆盖率：{summary.get('research_only_valid', 0)}/{summary.get('research_only_total', 0)} = {summary.get('research_only_rate', 0):.2%}",
        f"- observe_pool 总缺失数量：{summary.get('observe_pool_missing', 0)}",
        f"- research_only 总缺失数量：{summary.get('research_only_missing', 0)}",
        "",
        "## 明细",
        "| 代码 | 名称 | 类型 | pool | group | 文件 | 行数 | 起始日期 | 结束日期 | 必要字段 | 是否有效 | 是否过期 | 说明 |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- |",
    ]
    if df.empty:
        lines.append("|  |  |  |  |  |  | 0 |  |  | 否 | 否 | 否 | 无观察标的 |")
        return lines
    for row in df.itertuples():
        lines.append(
            f"| {row.code} | {row.name} | {row.type} | {row.pool} | {row.group} | {row.file_path} | "
            f"{row.rows} | {row.start_date} | {row.end_date} | {'是' if row.has_required_fields else '否'} | "
            f"{'是' if row.valid_data else '否'} | {'是' if row.is_stale else '否'} | {str(row.message).replace('|', '/')} |"
        )
    return lines


def _read_csv(path: Path) -> pd.DataFrame:
    for encoding in ["utf-8-sig", "utf-8", "gbk", "gb18030"]:
        try:
            return pd.read_csv(path, dtype={"code": str}, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, dtype={"code": str})


def _is_stale(latest_date: pd.Timestamp) -> bool:
    today = pd.Timestamp.today().normalize()
    return (today - latest_date.normalize()).days > STALE_DAYS


def _rate(numerator: int | float, denominator: int | float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(DATA_DIR.parent))
    except ValueError:
        return str(path)


def main() -> None:
    path, _ = write_data_coverage_report()
    print(f"已生成数据覆盖报告：{path}")
    print("本报告只读取本地 CSV，不包含任何真实交易接口。")


if __name__ == "__main__":
    main()
