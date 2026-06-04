"""公开行情数据下载和数据质量检查。

本模块只获取公开历史行情，并保存到本地 CSV。它不连接券商，不读取账号，
也不包含任何真实下单、融资或杠杆相关功能。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import time

import pandas as pd

from config import (
    DATA_DIR,
    DATA_QUALITY_REPORT_FILE,
    DATA_UPDATE_LOG_FILE,
    REPORT_DIR,
    WATCHLIST_HEALTH_REPORT_FILE,
)


OUTPUT_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
MAX_ATTEMPTS_PER_SYMBOL = 4

AKSHARE_COLUMN_MAP = {
    "日期": "date",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交量": "volume",
    "date": "date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
}


@dataclass
class FetchRunConfig:
    batch_size: int = 5
    sleep_seconds: float = 2.0
    retry: int = 2
    fetch_code: str | None = None
    fetch_group: str | None = None
    incremental: bool = False
    lookback_days: int = 10
    fetch_source: str = "auto"


@dataclass
class FetchResult:
    code: str
    name: str
    type: str
    raw_type: str
    source: str
    enabled_raw: str
    enabled: bool
    start_date: str
    end_date: str
    rows: int
    success: bool
    status: str
    download_mode: str
    message: str
    file_path: str
    attempts: list[str]
    interface_name: str = ""
    raw_columns: list[str] | None = None
    raw_rows: int = 0
    field_mapping_success: bool = False
    save_success: bool = False
    used_cache: bool = False
    attempted_sources: list[str] | None = None
    final_source: str = ""


@dataclass
class QualityResult:
    code: str
    name: str
    rows: int
    passed: bool
    issues: list[str]


@dataclass
class DiagnosticResult:
    interface: str
    success: bool
    rows: int
    exception_type: str
    message: str


def fetch_watchlist_data(
    watchlist: pd.DataFrame,
    start_date: str,
    end_date: str,
    batch_size: int = 5,
    sleep_seconds: float = 2.0,
    retry: int = 2,
    fetch_code: str | None = None,
    fetch_group: str | None = None,
    incremental: bool = False,
    lookback_days: int = 10,
    fetch_source: str = "auto",
) -> list[FetchResult]:
    """按观察名单下载公开行情数据，支持分批、限速、指定代码和指定分组。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    config = FetchRunConfig(
        batch_size=max(1, int(batch_size)),
        sleep_seconds=max(0.0, float(sleep_seconds)),
        retry=max(1, int(retry)),
        fetch_code=str(fetch_code).strip() if fetch_code else None,
        fetch_group=str(fetch_group).strip() if fetch_group else None,
        incremental=bool(incremental),
        lookback_days=max(0, int(lookback_days)),
        fetch_source=_normalize_fetch_source(fetch_source),
    )
    diagnostics = run_akshare_diagnostics(start_date, end_date) if config.fetch_source in {"auto", "akshare"} else []
    items = _select_fetch_items(watchlist, config)
    results: list[FetchResult] = []

    for batch_start in range(0, len(items), config.batch_size):
        batch = items[batch_start : batch_start + config.batch_size]
        for index, item in enumerate(batch):
            results.append(
                fetch_one_symbol(
                    item,
                    start_date,
                    end_date,
                    config.retry,
                    config.sleep_seconds,
                    config.incremental,
                    config.lookback_days,
                    config.fetch_source,
                )
            )
            is_last_symbol = batch_start + index + 1 >= len(items)
            if not is_last_symbol:
                time.sleep(config.sleep_seconds)

    write_data_update_log(results, diagnostics, config)
    quality_results = [
        check_data_quality(result)
        if result.success
        else QualityResult(result.code, result.name, 0, False, [f"下载失败，未检查：{result.message}"])
        for result in results
    ]
    write_data_quality_report(quality_results)
    write_watchlist_health_report(watchlist, results, config)
    return results


def run_akshare_diagnostics(start_date: str, end_date: str) -> list[DiagnosticResult]:
    """单独诊断 AKShare ETF 和 A 股股票接口，并记录异常类型和文本。"""
    try:
        import akshare as ak
    except Exception as exc:
        message = _format_exception(exc)
        return [
            DiagnosticResult("akshare.fund_etf_hist_em(510300)", False, 0, type(exc).__name__, message),
            DiagnosticResult("akshare.stock_zh_a_hist(600519)", False, 0, type(exc).__name__, message),
        ]

    start = _compact_date(start_date)
    end = _compact_date(end_date)
    tests = [
        ("akshare.fund_etf_hist_em(510300)", lambda: ak.fund_etf_hist_em(symbol="510300", period="daily", start_date=start, end_date=end, adjust="")),
        ("akshare.stock_zh_a_hist(600519)", lambda: ak.stock_zh_a_hist(symbol="600519", period="daily", start_date=start, end_date=end, adjust="")),
    ]
    diagnostics: list[DiagnosticResult] = []
    for label, func in tests:
        try:
            raw = func()
            rows = 0 if raw is None else len(raw)
            diagnostics.append(DiagnosticResult(label, rows > 0, rows, "", "成功" if rows > 0 else "返回空数据"))
        except Exception as exc:
            diagnostics.append(DiagnosticResult(label, False, 0, type(exc).__name__, _format_exception(exc)))
    return diagnostics


def fetch_one_symbol(
    item: pd.Series,
    start_date: str,
    end_date: str,
    retry: int = 2,
    sleep_seconds: float = 2.0,
    incremental: bool = False,
    lookback_days: int = 10,
    fetch_source: str = "auto",
) -> FetchResult:
    """下载单个 ETF 或股票的日线行情，失败时返回清晰错误。"""
    code = str(item.get("code", "")).strip()
    name = str(item.get("name", code)).strip()
    raw_type = str(item.get("type", "ETF")).strip()
    type_name = _normalize_security_type(raw_type)
    source = _normalize_fetch_source(fetch_source if fetch_source != "auto" else item.get("source", "auto"))
    enabled_raw = item.get("enabled", True)
    enabled = _is_enabled(enabled_raw)
    output_path = DATA_DIR / f"{code}.csv"
    attempts: list[str] = [
        f"读取字段：code={code}，type={raw_type} -> {type_name or '不支持'}，source={source}，enabled={enabled_raw} -> {enabled}"
    ]

    if type_name not in {"ETF", "STOCK"}:
        return _failed_result(code, name, type_name or raw_type, raw_type, source, enabled_raw, enabled, start_date, end_date, f"暂不支持标的类型：{raw_type}", output_path, attempts)

    effective_start_date, download_mode, cache_rows_before = _resolve_download_range(output_path, start_date, incremental, lookback_days)
    start = _compact_date(effective_start_date)
    end = _compact_date(end_date)
    attempts.append(f"下载模式：{download_mode}；本地缓存行数={cache_rows_before}；请求日期：{effective_start_date} -> {end_date}")
    attempts.append(f"日期转换：{effective_start_date} -> {start}，{end_date} -> {end}")
    last_error = "未执行下载"
    steps = _build_fetch_steps(code, type_name, start, end, source)
    max_attempts = min(len(steps), MAX_ATTEMPTS_PER_SYMBOL)
    last_interface = ""
    last_raw_columns: list[str] = []
    last_raw_rows = 0
    last_mapping_success = False
    last_save_success = False

    for attempt_no, (label, fetch_func) in enumerate(steps[:max_attempts], start=1):
        last_interface = label
        for retry_no in range(1, retry + 1):
            try:
                raw = fetch_func()
                raw_rows = 0 if raw is None else len(raw)
                raw_columns = _column_list(raw)
                last_raw_rows = raw_rows
                last_raw_columns = raw_columns
                attempts.append(f"接口 {attempt_no} / 重试 {retry_no}：实际调用接口={label}；原始字段={raw_columns or '无'}；返回行数={raw_rows}")
                normalized = normalize_daily(raw)
                last_mapping_success = not normalized.empty
                if normalized.empty:
                    last_error = f"{label} 返回空数据"
                    attempts.append(f"接口 {attempt_no} / 重试 {retry_no}：字段映射失败或返回空数据")
                else:
                    saved = _merge_and_save_csv(output_path, normalized, incremental)
                    last_save_success = output_path.exists()
                    attempts.append(f"接口 {attempt_no} / 重试 {retry_no}：字段映射成功；保存 CSV={'成功' if last_save_success else '失败'}；标准字段={OUTPUT_COLUMNS}；保存后行数={len(saved)}")
                    return FetchResult(
                        code,
                        name,
                        type_name,
                        raw_type,
                        source,
                        str(enabled_raw),
                        enabled,
                        start_date,
                        end_date,
                        len(saved),
                        True,
                        "fresh_download_success",
                        download_mode,
                        f"{label} 下载成功",
                        str(output_path),
                        attempts,
                        label,
                        raw_columns,
                        raw_rows,
                        True,
                        last_save_success,
                        False,
                        _attempted_sources(steps[:max_attempts]),
                        _source_from_interface(label),
                    )
            except Exception as exc:
                last_error = _format_exception(exc)
                attempts.append(f"接口 {attempt_no} / 重试 {retry_no}：{label} 失败，{last_error}")

            if retry_no < retry:
                time.sleep(sleep_seconds)

        if attempt_no < max_attempts:
            time.sleep(sleep_seconds)

    existing_rows = _existing_csv_rows(output_path)
    if existing_rows > 0:
        attempts.append(f"本次下载失败，但发现已有合格本地 CSV：{output_path.name}，{existing_rows} 行；本次保留旧数据继续使用")
        return FetchResult(
            code,
            name,
            type_name,
            raw_type,
            source,
            str(enabled_raw),
            enabled,
            start_date,
            end_date,
            existing_rows,
            True,
            "cached_success",
            "cache",
            f"本次下载失败，使用已有本地 CSV；最后失败原因：{last_error}",
            str(output_path),
            attempts,
            last_interface,
            last_raw_columns,
            last_raw_rows,
            True,
            True,
            True,
            _attempted_sources(steps[:max_attempts]),
            "cache",
        )

    return _failed_result(
        code,
        name,
        type_name,
        raw_type,
        source,
        enabled_raw,
        enabled,
        start_date,
        end_date,
        last_error,
        output_path,
        attempts,
        download_mode,
        last_interface,
        last_raw_columns,
        last_raw_rows,
        last_mapping_success,
        last_save_success,
        _attempted_sources(steps[:max_attempts]),
    )


def _build_fetch_steps(code: str, type_name: str, start: str, end: str, source: str) -> list[tuple[str, object]]:
    """根据数据源和标的类型生成行情接口尝试顺序。"""
    source = _normalize_fetch_source(source)
    if source == "akshare":
        return _akshare_steps(code, type_name, start, end)
    if source == "baostock":
        return [("BaoStock query_history_k_data_plus", lambda: fetch_baostock_daily(code, start, end))]
    if source == "tushare":
        return [("Tushare Pro 占位", lambda: fetch_tushare_daily_placeholder(code, start, end))]

    steps: list[tuple[str, object]] = [("BaoStock query_history_k_data_plus", lambda: fetch_baostock_daily(code, start, end))]
    steps.extend(_akshare_steps(code, type_name, start, end))
    return steps


def _akshare_steps(code: str, type_name: str, start: str, end: str) -> list[tuple[str, object]]:
    """生成 AKShare 和东方财富公开行情步骤。"""
    try:
        import akshare as ak
    except Exception as exc:
        return [("AKShare 导入失败", lambda: (_raise_exception(exc)))]

    if type_name == "ETF":
        return [
            ("AKShare fund_etf_hist_em", lambda: ak.fund_etf_hist_em(symbol=code, period="daily", start_date=start, end_date=end, adjust="")),
            ("AKShare stock_zh_a_hist ETF 备用", lambda: ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="")),
            ("东方财富公开 K 线接口", lambda: fetch_eastmoney_public_kline(code, start, end)),
        ]

    prefixed = _stock_prefixed_symbol(code)
    suffixed = _stock_suffixed_symbol(code)
    return [
        (f"AKShare stock_zh_a_hist {code}", lambda: ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="")),
        (f"AKShare stock_zh_a_hist {prefixed}", lambda: ak.stock_zh_a_hist(symbol=prefixed, period="daily", start_date=start, end_date=end, adjust="")),
        (f"AKShare stock_zh_a_hist {suffixed}", lambda: ak.stock_zh_a_hist(symbol=suffixed, period="daily", start_date=start, end_date=end, adjust="")),
        ("东方财富公开 K 线接口", lambda: fetch_eastmoney_public_kline(code, start, end)),
    ]


def normalize_daily(raw: pd.DataFrame) -> pd.DataFrame:
    """把 AKShare 或公开 K 线接口返回字段统一成 date,open,high,low,close,volume。"""
    if raw is None or raw.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    df = raw.rename(columns={col: AKSHARE_COLUMN_MAP.get(col, col) for col in raw.columns}).copy()
    missing = [col for col in OUTPUT_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"行情字段缺失：{', '.join(missing)}")

    df = df[OUTPUT_COLUMNS].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def normalize_akshare_daily(raw: pd.DataFrame) -> pd.DataFrame:
    """兼容旧调用：把 AKShare 返回字段统一成标准字段。"""
    return normalize_daily(raw)


def fetch_eastmoney_public_kline(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """通过东方财富公开 K 线 URL 获取历史行情，不涉及任何交易接口。"""
    import requests

    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": "101",
        "fqt": "0",
        "beg": start_date,
        "end": end_date,
        "secid": make_eastmoney_secid(code),
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://quote.eastmoney.com/",
        "Accept": "application/json,text/plain,*/*",
    }
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data") or {}
    klines = data.get("klines") or []
    rows = []
    for item in klines:
        parts = item.split(",")
        if len(parts) < 6:
            continue
        rows.append({"date": parts[0], "open": parts[1], "high": parts[3], "low": parts[4], "close": parts[2], "volume": parts[5]})
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def fetch_baostock_daily(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """通过 BaoStock 免费行情接口获取日 K 数据，不涉及任何交易接口。"""
    try:
        import baostock as bs
    except Exception as exc:
        raise RuntimeError(f"BaoStock 导入失败：{exc}") from exc

    bs_code = make_baostock_code(code)
    start = pd.to_datetime(start_date, format="%Y%m%d").strftime("%Y-%m-%d")
    end = pd.to_datetime(end_date, format="%Y%m%d").strftime("%Y-%m-%d")
    fields = "date,open,high,low,close,volume"
    login_result = bs.login()
    try:
        if login_result.error_code != "0":
            raise RuntimeError(f"BaoStock 登录失败：{login_result.error_msg}")
        rs = bs.query_history_k_data_plus(
            bs_code,
            fields,
            start_date=start,
            end_date=end,
            frequency="d",
            adjustflag="3",
        )
        if rs.error_code != "0":
            raise RuntimeError(f"BaoStock 查询失败：{rs.error_msg}")
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        if not rows:
            return pd.DataFrame(columns=OUTPUT_COLUMNS)
        return pd.DataFrame(rows, columns=rs.fields)
    finally:
        bs.logout()


def fetch_tushare_daily_placeholder(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Tushare Pro 预留接口：检测 token，但暂不实现完整下载。"""
    if not os.environ.get("TUSHARE_TOKEN"):
        raise RuntimeError("未配置 TUSHARE_TOKEN，跳过 Tushare Pro。")
    raise NotImplementedError("Tushare Pro 行情下载暂未完整实现；已检测到 token，但本版本只保留安全占位。")


def check_data_quality(result: FetchResult) -> QualityResult:
    """检查数据条数、空值、重复日期、价格和成交量是否合法。"""
    issues: list[str] = []
    path = Path(result.file_path)
    if not path.exists():
        return QualityResult(result.code, result.name, 0, False, ["CSV 文件不存在"])

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return QualityResult(result.code, result.name, 0, False, [f"CSV 读取失败：{exc}"])

    missing_columns = [col for col in OUTPUT_COLUMNS if col not in df.columns]
    if missing_columns:
        return QualityResult(result.code, result.name, len(df), False, [f"缺少字段：{', '.join(missing_columns)}"])
    if len(df) < 60:
        issues.append(f"数据少于 60 条：当前 {len(df)} 条")
    if df[OUTPUT_COLUMNS].isna().any().any():
        issues.append("存在空值")
    if df["date"].duplicated().any():
        issues.append("存在重复日期")
    for col in ["open", "high", "low", "close"]:
        if (pd.to_numeric(df[col], errors="coerce") <= 0).any():
            issues.append(f"{col} 存在非正数")
    if (pd.to_numeric(df["volume"], errors="coerce") < 0).any():
        issues.append("volume 存在负数")

    return QualityResult(result.code, result.name, len(df), not issues, issues)


def write_data_update_log(results: list[FetchResult], diagnostics: list[DiagnosticResult] | None = None, config: FetchRunConfig | None = None) -> Path:
    """保存数据更新日志。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fresh_count = sum(1 for item in results if item.status == "fresh_download_success")
    cached_count = sum(1 for item in results if item.status == "cached_success")
    failed_count = sum(1 for item in results if item.status == "failed")
    lines = [
        f"# 数据更新日志 {now}",
        "",
        "本日志只记录公开行情下载情况，不包含任何交易账号或下单信息。",
        "",
        "## 本次运行参数",
        "",
        f"- batch-size：{config.batch_size if config else '默认'}",
        f"- sleep-seconds：{config.sleep_seconds if config else '默认'}",
        f"- retry：{config.retry if config else '默认'}",
        f"- fetch-code：{config.fetch_code if config and config.fetch_code else '无'}",
        f"- fetch-group：{config.fetch_group if config and config.fetch_group else '无'}",
        f"- fetch-source：{config.fetch_source if config else 'auto'}",
        f"- incremental：{config.incremental if config else False}",
        f"- lookback-days：{config.lookback_days if config else '默认'}",
        "",
        "## 成功统计",
        "",
        f"- fresh_download_success：{fresh_count}",
        f"- cached_success：{cached_count}",
        f"- failed：{failed_count}",
        "",
        "## AKShare 接口诊断",
        "",
        "| 接口 | 是否成功 | 行数 | 异常类型 | 异常文本 |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for item in diagnostics or []:
        lines.append(f"| {item.interface} | {'成功' if item.success else '失败'} | {item.rows} | {item.exception_type or '无'} | {_escape_markdown_cell(item.message)} |")

    lines += [
        "",
        "## 标的下载结果",
        "",
        "| 代码 | 名称 | 类型 | 配置来源 | 尝试数据源 | 最终成功源 | enabled | 起始日期 | 结束日期 | 行数 | 状态 | 下载模式 | 使用本地缓存 | 失败原因 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for result in results:
        attempted_sources = ", ".join(result.attempted_sources or []) or "未调用"
        final_source = result.final_source or ("cache" if result.used_cache else "无")
        lines.append(
            f"| {result.code} | {result.name} | {result.raw_type} -> {result.type} | {result.source} | {attempted_sources} | {final_source} | {result.enabled_raw} -> {result.enabled} | {result.start_date} | {result.end_date} | "
            f"{result.rows} | {result.status} | {result.download_mode} | {'是' if result.used_cache else '否'} | {_escape_markdown_cell('' if result.success else result.message)} |"
        )

    lines += [
        "",
        "## 字段映射和保存诊断",
        "",
        "| 代码 | 实际接口 | 最终成功源 | AKShare/BaoStock/公开接口原始字段 | 原始返回行数 | 标准 CSV 行数 | 字段映射 | 保存 CSV |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for result in results:
        raw_columns = ", ".join(result.raw_columns or [])
        lines.append(
            f"| {result.code} | {_escape_markdown_cell(result.interface_name or '未调用')} | {result.final_source or ('cache' if result.used_cache else '无')} | {_escape_markdown_cell(raw_columns or '无')} | "
            f"{result.raw_rows} | {result.rows} | {'成功' if result.field_mapping_success else '失败'} | {'成功' if result.save_success else '失败'} |"
        )

    lines += ["", "## 每次尝试明细", ""]
    for result in results:
        lines.append(f"### {result.code} {result.name}")
        if result.attempts:
            lines.extend([f"- {_escape_markdown_cell(item)}" for item in result.attempts])
        else:
            lines.append("- 未执行下载尝试")
    DATA_UPDATE_LOG_FILE.write_text("\n".join(lines), encoding="utf-8")
    return DATA_UPDATE_LOG_FILE


def write_data_quality_report(results: list[QualityResult]) -> Path:
    """保存数据质量检查报告。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# 数据质量报告 {now}",
        "",
        "| 代码 | 名称 | 行数 | 是否通过 | 问题 |",
        "| --- | --- | ---: | --- | --- |",
    ]
    if not results:
        lines.append("| 无 | 无 | 0 | 否 | 没有成功下载的数据可检查 |")
    for result in results:
        issue_text = "无" if result.passed else "；".join(result.issues)
        lines.append(f"| {result.code} | {result.name} | {result.rows} | {'通过' if result.passed else '不通过'} | {_escape_markdown_cell(issue_text)} |")
    DATA_QUALITY_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    return DATA_QUALITY_REPORT_FILE


def write_watchlist_health_report(watchlist: pd.DataFrame, results: list[FetchResult], config: FetchRunConfig) -> Path:
    """生成观察池可用性报告。"""
    enabled_trade_pool = watchlist[(watchlist["enabled"].astype(bool)) & (watchlist["role"] == "trade_pool")]
    full_pool_total = len(enabled_trade_pool)
    checked_total = len(results)
    fresh = [item for item in results if item.status == "fresh_download_success"]
    cached = [item for item in results if item.status == "cached_success"]
    failed = [item for item in results if item.status == "failed"]
    checked_available_rate = (len(fresh) + len(cached)) / checked_total if checked_total else 0.0
    full_pool_cached = sum(1 for code in enabled_trade_pool["code"].astype(str) if _existing_csv_rows(DATA_DIR / f"{code}.csv") > 0)
    full_pool_cached_rate = full_pool_cached / full_pool_total if full_pool_total else 0.0

    if config.fetch_code:
        scope_note = "本次为单标的检查，不代表全池健康度。"
    elif config.fetch_group:
        scope_note = "本次为指定 group 检查，不代表全池健康度。"
    else:
        scope_note = "本次为全池检查。"

    lines = [
        f"# Watchlist 健康报告 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "本报告只评估公开行情数据可用性，不包含任何交易接口或下单操作。",
        "",
        "## 本次运行参数",
        f"- batch-size：{config.batch_size}",
        f"- sleep-seconds：{config.sleep_seconds}",
        f"- retry：{config.retry}",
        f"- fetch-code：{config.fetch_code or '无'}",
        f"- fetch-group：{config.fetch_group or '无'}",
        f"- fetch-source：{config.fetch_source}",
        f"- incremental：{config.incremental}",
        f"- lookback-days：{config.lookback_days}",
        "",
        "## 检查范围说明",
        f"- {scope_note}",
        f"- 全部 enabled trade_pool 总数：{full_pool_total}",
        f"- 本次实际检查标的数：{checked_total}",
        "",
        "## 本次检查范围",
    ]
    if results:
        lines.append("| 代码 | 名称 | 状态 | 下载模式 | 尝试数据源 | 最终成功源 | 使用本地缓存 |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for item in results:
            attempted_sources = ", ".join(item.attempted_sources or []) or "未调用"
            final_source = item.final_source or ("cache" if item.used_cache else "无")
            lines.append(f"| {item.code} | {item.name} | {item.status} | {item.download_mode} | {attempted_sources} | {final_source} | {'是' if item.used_cache else '否'} |")
    else:
        lines.append("- 本次没有实际检查标的。")

    lines += [
        "",
        "## 总览",
        f"- 全部 enabled trade_pool 总数：{full_pool_total}",
        f"- 本次实际检查标的数：{checked_total}",
        f"- 本次新下载成功数：{len(fresh)}",
        f"- 本地缓存可用数：{len(cached)}",
        f"- 失败数：{len(failed)}",
        f"- 本次检查范围可用率：{checked_available_rate:.2%}",
        f"- 全池已有合格 CSV 数量：{full_pool_cached}",
        f"- 全池已缓存可用率：{full_pool_cached_rate:.2%}",
        "",
        "## 失败标的建议",
    ]
    if not failed:
        lines.append("- 本次没有失败标的。")
    else:
        lines.append("| 代码 | 名称 | 尝试数据源 | 是否有本地缓存 | 失败原因 | 建议 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for item in failed:
            attempted_sources = ", ".join(item.attempted_sources or []) or "未调用"
            has_cache = _existing_csv_rows(DATA_DIR / f"{item.code}.csv") > 0
            lines.append(f"| {item.code} | {item.name} | {attempted_sources} | {'是' if has_cache else '否'} | {_escape_markdown_cell(item.message)} | {_failure_suggestion(item)} |")

    WATCHLIST_HEALTH_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    return WATCHLIST_HEALTH_REPORT_FILE


def make_eastmoney_secid(code: str) -> str:
    """生成东方财富公开 K 线接口 secid。"""
    code = str(code).strip()
    if code.startswith(("6", "510", "511", "512", "513", "515", "516", "588")):
        return f"1.{code}"
    if code.startswith(("0", "3", "159")):
        return f"0.{code}"
    return f"1.{code}"


def make_baostock_code(code: str) -> str:
    """生成 BaoStock 代码，例如 sh.512880 或 sz.159928。"""
    code = str(code).strip()
    if code.startswith(("6", "510", "511", "512", "513", "515", "516", "518", "588")):
        return f"sh.{code}"
    if code.startswith(("0", "3", "159")):
        return f"sz.{code}"
    return f"sh.{code}"


def _source_from_interface(label: str) -> str:
    """从接口名称判断实际数据源。"""
    if label.startswith("BaoStock"):
        return "baostock"
    if label.startswith("Tushare"):
        return "tushare"
    if label.startswith("AKShare") or label.startswith("东方财富"):
        return "akshare"
    return ""


def _attempted_sources(steps: list[tuple[str, object]]) -> list[str]:
    """返回本次按顺序尝试过的数据源，去重保序。"""
    sources: list[str] = []
    for label, _ in steps:
        source = _source_from_interface(label)
        if source and source not in sources:
            sources.append(source)
    return sources


def _compact_date(value: str) -> str:
    """把 YYYY-MM-DD 转成 AKShare 和公开 K 线接口常用的 YYYYMMDD。"""
    return pd.to_datetime(value).strftime("%Y%m%d")


def _stock_prefixed_symbol(code: str) -> str:
    """生成 sh600519 或 sz000001 这类股票代码。"""
    return f"sh{code}" if str(code).startswith("6") else f"sz{code}"


def _stock_suffixed_symbol(code: str) -> str:
    """生成 600519.SH 或 000001.SZ 这类股票代码。"""
    return f"{code}.SH" if str(code).startswith("6") else f"{code}.SZ"


def _is_enabled(value: object) -> bool:
    """兼容 1、1.0、True、true 等观察名单启用值。"""
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "1.0", "true", "yes", "y", "启用"}


def _normalize_security_type(value: object) -> str:
    """把 ETF/STOCK 等类型统一为内部类型。"""
    text = str(value).strip().lower()
    if text in {"etf", "a_share_etf", "ashare_etf", "a-share-etf"}:
        return "ETF"
    if text in {"stock", "a_share_stock", "ashare_stock", "a-share-stock"}:
        return "STOCK"
    return ""


def _normalize_fetch_source(value: object) -> str:
    """统一数据源参数。"""
    text = str(value or "auto").strip().lower()
    return text if text in {"auto", "akshare", "baostock", "tushare"} else "auto"


def _raise_exception(exc: Exception) -> None:
    raise exc


def _column_list(raw: object) -> list[str]:
    """返回行情源原始字段列表，用于调试日志。"""
    if raw is None or not hasattr(raw, "columns"):
        return []
    return [str(col) for col in raw.columns]


def _existing_csv_rows(path: Path) -> int:
    """本次下载失败时，检查是否已有可继续使用的标准 CSV。"""
    if not path.exists():
        return 0
    try:
        df = pd.read_csv(path)
    except Exception:
        return 0
    if any(col not in df.columns for col in OUTPUT_COLUMNS):
        return 0
    return len(df)


def _resolve_download_range(path: Path, start_date: str, incremental: bool, lookback_days: int) -> tuple[str, str, int]:
    """根据本地 CSV 决定全量或增量下载区间。"""
    if not incremental:
        return start_date, "full_download", _existing_csv_rows(path)
    if not path.exists():
        return start_date, "full_download", 0
    try:
        df = pd.read_csv(path)
    except Exception:
        return start_date, "full_download", 0
    if any(col not in df.columns for col in OUTPUT_COLUMNS) or df.empty:
        return start_date, "full_download", 0
    dates = pd.to_datetime(df["date"], errors="coerce").dropna()
    if dates.empty:
        return start_date, "full_download", 0
    last_date = dates.max()
    incremental_start = (last_date - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    return incremental_start, "incremental_download", len(df)


def _merge_and_save_csv(path: Path, new_df: pd.DataFrame, incremental: bool) -> pd.DataFrame:
    """保存行情 CSV；增量模式下与旧 CSV 合并并按日期去重。"""
    frames = []
    if incremental and path.exists():
        try:
            old_df = pd.read_csv(path)
            if all(col in old_df.columns for col in OUTPUT_COLUMNS):
                frames.append(old_df[OUTPUT_COLUMNS].copy())
        except Exception:
            pass
    frames.append(new_df[OUTPUT_COLUMNS].copy())
    combined = pd.concat(frames, ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for col in ["open", "high", "low", "close", "volume"]:
        combined[col] = pd.to_numeric(combined[col], errors="coerce")
    combined = combined.dropna(subset=["date"]).drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
    combined.to_csv(path, index=False)
    return combined


def _select_fetch_items(watchlist: pd.DataFrame, config: FetchRunConfig) -> list[pd.Series]:
    """根据 code/group/enabled 选择本次需要下载的标的。"""
    df = watchlist.copy()
    if config.fetch_code:
        df = df[df["code"].astype(str) == config.fetch_code]
    else:
        df = df[df["enabled"].apply(_is_enabled)]
        if config.fetch_group:
            df = df[df["group"].astype(str) == config.fetch_group]
    return [row for _, row in df.iterrows()]


def _failure_suggestion(result: FetchResult) -> str:
    """根据失败原因给出下一步处理建议。"""
    message = result.message
    if not result.used_cache and _existing_csv_rows(DATA_DIR / f"{result.code}.csv") == 0:
        return "可通过 raw/ 手动导入 CSV 后继续参与模型数据集；保留重试；分批下载"
    if "RemoteDisconnected" in message or "网络/DNS" in message or "ProxyError" in message:
        return "保留重试；分批下载"
    if "返回空数据" in message or "字段缺失" in message or "暂不支持" in message:
        return "需要人工确认代码"
    return "分批下载；暂时禁用"


def _format_exception(exc: Exception) -> str:
    """记录异常类型和异常文本。"""
    return _clean_error(f"{type(exc).__name__}: {exc}")


def _clean_error(message: str) -> str:
    """把网络库的长异常整理成适合写入 Markdown 报告的短提示。"""
    if "NameResolutionError" in message or "Failed to resolve" in message:
        return "公开行情源网络/DNS 访问失败：无法解析 push2his.eastmoney.com，请检查本机网络或稍后重试。"
    if "RemoteDisconnected" in message or "Remote end closed connection" in message:
        return "公开行情源远端主动断开连接：RemoteDisconnected，已尝试备用公开接口。"
    if "Max retries exceeded" in message:
        return "公开行情源请求多次重试失败，请检查网络连接或稍后重试。"
    return message.replace("\n", " ").replace("|", "/")


def _escape_markdown_cell(value: str) -> str:
    """避免日志中的竖线破坏 Markdown 表格。"""
    return str(value).replace("|", "/").replace("\n", " ")


def _failed_result(
    code: str,
    name: str,
    type_name: str,
    raw_type: str,
    source: str,
    enabled_raw: object,
    enabled: bool,
    start_date: str,
    end_date: str,
    message: str,
    output_path: Path,
    attempts: list[str] | None = None,
    download_mode: str = "full_download",
    interface_name: str = "",
    raw_columns: list[str] | None = None,
    raw_rows: int = 0,
    field_mapping_success: bool = False,
    save_success: bool = False,
    attempted_sources: list[str] | None = None,
) -> FetchResult:
    return FetchResult(
        code,
        name,
        type_name,
        raw_type,
        source,
        str(enabled_raw),
        enabled,
        start_date,
        end_date,
        0,
        False,
        "failed",
        download_mode,
        message,
        str(output_path),
        attempts or [],
        interface_name,
        raw_columns or [],
        raw_rows,
        field_mapping_success,
        save_success,
        False,
        attempted_sources or [],
        "",
    )
