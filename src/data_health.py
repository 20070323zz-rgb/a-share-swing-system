"""本地行情数据健康检查。

本模块只读取本地 CSV，不联网，不连接券商，不下单。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import DATA_DIR, DATA_HEALTH_REPORT_FILE, ETF_DAILY_DIR, LATEST_DATA_HEALTH_FILE, PROJECT_ROOT, WATCHLIST_FILE
from data_loader import COLUMN_MAP, REQUIRED_PRICE_COLUMNS, find_price_file, read_formal_data_universe


STALE_DAYS_STRICT = 10
STALE_DAYS_OBSERVE = 30
RELAXED_GROUPS = {"QDII观察", "债券货币观察", "个股观察"}


def write_data_health_report(watchlist: pd.DataFrame | None = None) -> tuple[Path, dict]:
    """生成数据健康报告，并返回摘要供 latest_brief 使用。"""
    if watchlist is None:
        watchlist = read_formal_data_universe(WATCHLIST_FILE, ETF_DAILY_DIR, PROJECT_ROOT / "data" / "etf_pool_expansion_candidates.csv")
    rows = build_health_rows(watchlist)
    df = pd.DataFrame(rows)
    summary = summarize_health(df)
    lines = _build_report_lines(df, summary)
    DATA_HEALTH_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    LATEST_DATA_HEALTH_FILE.write_text(DATA_HEALTH_REPORT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    return DATA_HEALTH_REPORT_FILE, summary


def build_health_rows(watchlist: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for _, item in watchlist.iterrows():
        code = str(item.get("code", "")).strip()
        group = str(item.get("group", ""))
        role = str(item.get("role", ""))
        relaxed = group in RELAXED_GROUPS or role == "observe_pool"
        path = find_price_file(DATA_DIR, code)
        row = {
            "code": code,
            "name": item.get("name", code),
            "type": item.get("type", ""),
            "pool": role,
            "group": group,
            "file_path": "",
            "rows": 0,
            "latest_date": "",
            "status": "缺失",
            "errors": [],
            "warnings": ["缺少本地 CSV"],
        }
        if path is None:
            rows.append(row)
            continue
        row["file_path"] = _relative_path(path)
        try:
            raw = _read_csv(path)
        except Exception as exc:
            row["status"] = "异常"
            row["errors"] = [f"CSV 读取失败：{exc}"]
            row["warnings"] = []
            rows.append(row)
            continue
        checked = check_price_dataframe(raw, relaxed)
        row.update(checked)
        rows.append(row)
    return rows


def check_price_dataframe(raw: pd.DataFrame, relaxed: bool = False) -> dict:
    """检查单个本地行情 DataFrame。"""
    errors: list[str] = []
    warnings: list[str] = []
    df = raw.rename(columns={col: COLUMN_MAP.get(str(col).strip(), col) for col in raw.columns}).copy()
    row_count = len(df)
    if row_count == 0:
        errors.append("CSV 为空")

    missing = [col for col in REQUIRED_PRICE_COLUMNS if col not in df.columns]
    if missing:
        errors.append("缺少必要字段：" + ", ".join(missing))
        return {
            "rows": row_count,
            "latest_date": "",
            "status": "异常",
            "errors": errors,
            "warnings": warnings,
        }

    dates = pd.to_datetime(df["date"], errors="coerce")
    if dates.isna().any():
        errors.append("存在无法解析的 date")
    valid_dates = dates.dropna()
    latest_date = valid_dates.max().strftime("%Y-%m-%d") if not valid_dates.empty else ""
    if valid_dates.empty:
        errors.append("没有可解析日期")
    else:
        duplicated = dates.duplicated().sum()
        if duplicated:
            warnings.append(f"存在重复日期：{int(duplicated)} 行")
        if not dates.dropna().is_monotonic_increasing:
            warnings.append("日期不是升序")
        stale_days = STALE_DAYS_OBSERVE if relaxed else STALE_DAYS_STRICT
        age = (pd.Timestamp.today().normalize() - valid_dates.max().normalize()).days
        if age > stale_days:
            warnings.append(f"最近交易日偏旧：{latest_date}，距今天 {age} 天")

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[["open", "high", "low", "close"]].isna().any().any():
        errors.append("存在无法解析的价格字段")
    non_positive = (df[["open", "high", "low", "close"]] <= 0).any(axis=1).sum()
    if non_positive:
        errors.append(f"存在 open/high/low/close 小于等于 0：{int(non_positive)} 行")
    high_low_bad = (df["high"] < df["low"]).sum()
    if high_low_bad:
        errors.append(f"存在 high < low：{int(high_low_bad)} 行")

    if row_count:
        zero_volume_ratio = (df["volume"].fillna(0) == 0).mean()
        last20_zero = (df["volume"].tail(20).fillna(0) == 0).all() if row_count >= 20 else False
        if last20_zero or zero_volume_ratio > 0.8:
            text = f"成交量长期为 0 或接近 0：零成交占比 {zero_volume_ratio:.2%}"
            warnings.append(text if relaxed else text)

    close = pd.to_numeric(df["close"], errors="coerce")
    pct = close.pct_change()
    extreme = pct.abs() > 0.25
    if extreme.sum():
        warnings.append(f"存在单日涨跌幅极端异常 abs(pct_change)>0.25：{int(extreme.sum())} 次，仅提示不删除")

    status = "异常" if errors else ("提醒" if warnings else "正常")
    return {
        "rows": row_count,
        "latest_date": latest_date,
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }


def summarize_health(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"total": 0, "normal": 0, "warning": 0, "error": 0, "missing": 0, "issue_symbols": [], "warning_symbols": [], "error_symbols": [], "missing_symbols": []}
    status = df["status"].astype(str)
    issue_df = df[status.isin(["异常", "提醒", "缺失"])].copy()
    return {
        "total": int(len(df)),
        "normal": int((status == "正常").sum()),
        "warning": int((status == "提醒").sum()),
        "error": int((status == "异常").sum()),
        "missing": int((status == "缺失").sum()),
        "issue_symbols": issue_df["code"].astype(str).head(20).tolist(),
        "warning_symbols": df.loc[status == "提醒", "code"].astype(str).tolist(),
        "error_symbols": df.loc[status == "异常", "code"].astype(str).tolist(),
        "missing_symbols": df.loc[status == "缺失", "code"].astype(str).tolist(),
    }


def _build_report_lines(df: pd.DataFrame, summary: dict) -> list[str]:
    lines = [
        f"# 本地数据健康报告 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "本报告只检查本地 CSV，不联网，不接券商 API，不下单。",
        "QDII观察、债券货币观察、个股观察只做提醒，避免用过严规则误判。",
        "",
        "## 摘要",
        f"- 检查标的总数：{summary['total']}",
        f"- 正常：{summary['normal']}",
        f"- 提醒：{summary['warning']}",
        f"- 异常：{summary['error']}",
        f"- 缺失：{summary['missing']}",
        "",
        "## 明细",
        "| 代码 | 名称 | 类型 | pool | group | 文件 | 行数 | 最近日期 | 状态 | 硬问题 | 提醒 |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    if df.empty:
        lines.append("|  |  |  |  |  |  | 0 |  | 缺失 |  | 无观察标的 |")
        return lines
    for row in df.itertuples():
        errors = "；".join(row.errors) if row.errors else ""
        warnings = "；".join(row.warnings) if row.warnings else ""
        lines.append(
            f"| {row.code} | {row.name} | {row.type} | {row.pool} | {row.group} | {row.file_path} | "
            f"{row.rows} | {row.latest_date} | {row.status} | {_escape(errors)} | {_escape(warnings)} |"
        )
    return lines


def _read_csv(path: Path) -> pd.DataFrame:
    for encoding in ["utf-8-sig", "utf-8", "gbk", "gb18030"]:
        try:
            return pd.read_csv(path, dtype={"code": str}, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, dtype={"code": str})


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(DATA_DIR.parent))
    except ValueError:
        return str(path)


def _escape(text: str) -> str:
    return str(text).replace("|", "/")


def main() -> None:
    path, _ = write_data_health_report()
    print(f"已生成数据健康报告：{path}")
    print("本报告只读取本地 CSV，不包含任何真实交易接口。")


if __name__ == "__main__":
    main()
