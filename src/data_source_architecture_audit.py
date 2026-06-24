"""Generate Phase 4C data-source architecture audit reports.

This is a research/audit script. It reads local project files and reports only.
It never downloads market data, never connects to broker APIs, never places
orders, and never modifies paper trading files.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = PROJECT_ROOT / "reports"
SRC_DIR = PROJECT_ROOT / "src"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

ARCH_MD = REPORT_DIR / "data_source_architecture_audit.md"
ARCH_JSON = REPORT_DIR / "data_source_architecture_audit.json"
PROVIDER_DESIGN_MD = REPORT_DIR / "data_provider_design.md"
INTELLIGENCE_PLAN_MD = REPORT_DIR / "intelligence_data_source_plan.md"
NO_LOOKAHEAD_MD = REPORT_DIR / "no_lookahead_data_rules.md"
NEXT_STEP_MD = REPORT_DIR / "phase4c_data_next_step.md"
SUMMARY_JSON = REPORT_DIR / "phase4c_data_summary.json"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    audit = build_audit()
    ARCH_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    ARCH_MD.write_text(render_architecture_report(audit), encoding="utf-8")
    PROVIDER_DESIGN_MD.write_text(render_provider_design(audit), encoding="utf-8")
    INTELLIGENCE_PLAN_MD.write_text(render_intelligence_plan(), encoding="utf-8")
    NO_LOOKAHEAD_MD.write_text(render_no_lookahead_rules(), encoding="utf-8")
    NEXT_STEP_MD.write_text(render_next_step(audit), encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(build_phase4c_summary(audit), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written: {ARCH_MD}")
    print(f"written: {ARCH_JSON}")
    print(f"written: {PROVIDER_DESIGN_MD}")
    print(f"written: {INTELLIGENCE_PLAN_MD}")
    print(f"written: {NO_LOOKAHEAD_MD}")
    print(f"written: {NEXT_STEP_MD}")
    print(f"written: {SUMMARY_JSON}")


def build_audit() -> dict[str, Any]:
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    source_status = _read_json(REPORT_DIR / "data_source_status.json")
    update_status = _read_json(REPORT_DIR / "data_update_status.json")
    akshare = _read_json(REPORT_DIR / "akshare_connectivity_check.json")
    files = {
        "config": _file_snapshot(SRC_DIR / "config.py"),
        "update_etf_data": _file_snapshot(SCRIPTS_DIR / "update_etf_data.py"),
        "data_health": _file_snapshot(SRC_DIR / "data_health.py"),
        "data_coverage": _file_snapshot(SRC_DIR / "data_coverage.py"),
        "features": _file_snapshot(SRC_DIR / "features.py"),
        "ranking_model_v2_backtest": _file_snapshot(SRC_DIR / "ranking_model_v2_backtest.py"),
        "strategy_preview_tracking": _file_snapshot(SRC_DIR / "strategy_preview_tracking.py"),
        "watchlist_root": _file_snapshot(PROJECT_ROOT / "watchlist.csv"),
        "watchlist_data": _file_snapshot(DATA_DIR / "watchlist.csv"),
        "backtest_trade_pool": _file_snapshot(DATA_DIR / "backtest_trade_pool.csv"),
        "data_source_status_json": _file_snapshot(REPORT_DIR / "data_source_status.json"),
        "data_update_status_json": _file_snapshot(REPORT_DIR / "data_update_status.json"),
        "latest_data_health": _file_snapshot(REPORT_DIR / "latest_data_health.md"),
        "latest_data_coverage": _file_snapshot(REPORT_DIR / "latest_data_coverage.md"),
    }
    universe = _universe_snapshot()
    architecture_findings = [
        {
            "area": "daily_update",
            "finding": "scripts/update_etf_data.py is still the operational daily-update entry. It supports source selection and delegates non-BaoStock sources to src/data_sources/source_router.py.",
            "risk": "source priority and provider health are not yet managed by a formal provider abstraction.",
            "recommendation": "Keep current path stable, then introduce provider layer in staged dry-run mode.",
        },
        {
            "area": "source_router",
            "finding": "src/data_sources/source_router.py records machine-readable source status and fallback decisions.",
            "risk": "Tushare is currently not implemented as a working daily source, and JQData may be unavailable for daily updates.",
            "recommendation": "Use Tushare only after explicit token/config tests; treat JQData as historical/staging unless daily access is proven.",
        },
        {
            "area": "formal_data",
            "finding": "data_health/data_coverage read local CSVs only and are suitable downstream validators.",
            "risk": "source metadata columns are not consistently present in existing formal CSVs.",
            "recommendation": "Add source/fetch_time/available_date in future staging files; do not retroactively rewrite trusted old rows unless audited.",
        },
        {
            "area": "research_model",
            "finding": "features and v2 backtest use local confirmed daily bars and do not require provider credentials.",
            "risk": "new intelligence data could introduce look-ahead if available_date is not tracked.",
            "recommendation": "Any non-price data must include publish_time, fetch_time, available_date, and confirmed_after_close flags.",
        },
    ]
    safety = {
        "broker_api": False,
        "real_order": False,
        "real_account": False,
        "paper_trades_modified": False,
        "paper_positions_modified": False,
        "paper_trade_engine_modified": False,
        "execution_integration": False,
    }
    return {
        "generated_at": generated_at,
        "phase": "Phase 4C-Data",
        "research_only": True,
        "universe": universe,
        "source_status": source_status,
        "update_status": update_status,
        "akshare_connectivity": akshare,
        "files": files,
        "architecture_findings": architecture_findings,
        "recommended_priorities": {
            "daily_source_priority": ["tushare_if_configured", "baostock", "akshare_fallback"],
            "history_source_priority": ["jqdata", "baostock", "tushare_if_configured", "akshare_fallback"],
            "special_data_priority": ["akshare", "tushare", "manual"],
        },
        "target_schema": ["date", "open", "high", "low", "close", "volume", "amount", "source", "fetch_time", "available_date"],
        "safety": safety,
    }


def build_phase4c_summary(audit: dict[str, Any]) -> dict[str, Any]:
    akshare_status = audit.get("akshare_connectivity", {}).get("akshare_status") or "not_checked"
    if akshare_status in {"usable", "partially_usable"}:
        next_step = "先把 AKShare 接为低频情报/特殊数据源候选；日线主源仍保留现有验证链路。"
    else:
        next_step = "AKShare 暂不适合作为自动化主源；优先修复 BaoStock/本地缓存链路，并评估 Tushare 只读日线。"
    return {
        "status": "completed",
        "research_only": True,
        "akshare_status": akshare_status,
        "data_provider_design_ready": True,
        "intelligence_data_plan_ready": True,
        "no_lookahead_rules_ready": True,
        "recommended_next_step": next_step,
        "summary": "Phase 4C completed data-source architecture audit, AKShare connectivity diagnosis, provider-layer design, intelligence-data plan, and no-lookahead rules. No execution-layer integration.",
        "report_href": "../reports/data_source_architecture_audit.md",
        "provider_design_href": "../reports/data_provider_design.md",
        "akshare_report_href": "../reports/akshare_connectivity_check.md",
        "intelligence_plan_href": "../reports/intelligence_data_source_plan.md",
        "no_lookahead_href": "../reports/no_lookahead_data_rules.md",
        "next_step_href": "../reports/phase4c_data_next_step.md",
    }


def render_architecture_report(audit: dict[str, Any]) -> str:
    source = audit.get("source_status", {})
    update = audit.get("update_status", {})
    universe = audit.get("universe", {})
    lines = [
        f"# 数据源架构审计 {audit['generated_at']}",
        "",
        "本报告是 Phase 4C-Data 研究审计，不修改交易策略、不修改模拟持仓、不接券商 API、不真实下单。",
        "",
        "## 摘要结论",
        f"- 当前正式 ETF 文件数量：{universe.get('etf_daily_file_count', 0)}",
        f"- 最近数据源实际使用：{source.get('actual_source_used', update.get('source_used', 'unknown'))}",
        f"- 最近最新数据日：{source.get('latest_data_date', update.get('latest_data_date', update.get('latest_local_date', 'unknown')))}",
        f"- 最近新增行数：{source.get('new_rows', update.get('added_rows', 0))}",
        f"- BaoStock API calls：{update.get('baostock_api_calls', update.get('actual_api_calls', 0))}",
        "- 当前运行层已具备状态报告和 fallback 记录，但 provider 抽象层仍处于设计/轻实现阶段。",
        "- 新情报/新闻/资金数据必须先进入研究层，不能直接接入 BUY 或 SELL 执行层。",
        "",
        "## 当前数据链路",
        "| 环节 | 当前实现 | 审计判断 |",
        "| --- | --- | --- |",
        "| 日线更新入口 | scripts/update_etf_data.py | 可继续保留为稳定入口 |",
        "| 数据源路由 | src/data_sources/source_router.py | 已记录 JQData/BaoStock 状态，但 Tushare 未正式实现 |",
        "| JQData | src/data_sources/jqdata_source.py | 适合 staging/history，不应绕过 validate/dry-run |",
        "| BaoStock | update_etf_data 主路径 | 当前可用但延迟较高，适合作 fallback/日更低频 |",
        "| AKShare | 本轮新增诊断 | 先按诊断结果决定是否只能辅助 |",
        "| 本地 CSV | data/etf_daily | 正式研究主库，本地原行优先 |",
        "",
        "## 发现与建议",
    ]
    for item in audit.get("architecture_findings", []):
        lines.extend(
            [
                f"### {item['area']}",
                f"- 发现：{item['finding']}",
                f"- 风险：{item['risk']}",
                f"- 建议：{item['recommendation']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 目标统一字段",
            "`date, open, high, low, close, volume, amount, source, fetch_time, available_date`",
            "",
            "## 推荐数据源优先级",
            f"- 日更：{', '.join(audit['recommended_priorities']['daily_source_priority'])}",
            f"- 历史补齐：{', '.join(audit['recommended_priorities']['history_source_priority'])}",
            f"- 情报/特殊数据：{', '.join(audit['recommended_priorities']['special_data_priority'])}",
            "",
            "## 安全边界",
            "- 不接券商 API",
            "- 不真实下单",
            "- 不读取真实账户",
            "- 不修改 paper_trades.csv / paper_positions.csv / paper_trade_engine.py",
            "- 不把新数据因子直接接入正式执行层",
        ]
    )
    return "\n".join(lines)


def render_provider_design(audit: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# 数据源 Provider 分层设计 {audit['generated_at']}",
            "",
            "本设计只描述未来数据接入层，不替换当前自动化，不接入交易执行。",
            "",
            "## 目标",
            "- 所有行情数据先进入 staging 或本地缓存检查层。",
            "- 统一 schema：`date, open, high, low, close, volume, amount, source, fetch_time, available_date`。",
            "- 合并时永远本地高可信旧行优先，不允许旧源覆盖更新、更可信数据。",
            "- 每个 provider 必须暴露 status、fetch_daily、错误原因和源状态。",
            "",
            "## 已新增轻实现骨架",
            "- `src/data_providers/base.py`",
            "- `src/data_providers/local_cache_provider.py`",
            "- `src/data_providers/baostock_provider.py`",
            "- `src/data_providers/tushare_provider.py`",
            "- `src/data_providers/akshare_provider.py`",
            "- `src/data_providers/jqdata_provider.py`",
            "",
            "## 数据源职责",
            "| 数据源 | 建议角色 | 备注 |",
            "| --- | --- | --- |",
            "| local_cache | 第一读取层 | 回测/研究优先读本地正式 CSV |",
            "| BaoStock | 日更 fallback/低频补齐 | 当前可用但延迟较高，必须估算调用量 |",
            "| Tushare | 可配置日线候选 | 需要 token，仅环境变量，不打印 |",
            "| JQData | 历史/staging 候选 | 当前不宜强行作为日常主源 |",
            "| AKShare | 情报/特殊数据/低频 fallback | 不适合高频并发或主源，需看诊断结果 |",
            "",
            "## 必须实现的工程保护",
            "- retry：有限次数，记录错误类型。",
            "- timeout：每个请求必须有上限。",
            "- backoff：失败后退避，不能死循环重试。",
            "- rate_limit：每天调用量上限，BaoStock 远低于 50000。",
            "- circuit_breaker：连续失败时停止该源，切换 fallback 或停止。",
            "- local_cache_first：能用本地已确认数据就不重复请求。",
            "- no_overwrite_newer_data：不允许旧数据源覆盖本地高可信行。",
            "- source_status_report：每次更新写机器可读 JSON 和 Markdown。",
            "",
            "## 明确禁止",
            "- 高频并发暴力请求。",
            "- 没有 source / fetch_time / available_date 的新数据进入研究因子。",
            "- 旧源覆盖新源或正式高可信数据。",
            "- 情报数据直接进入 BUY 主因子或自动卖出执行层。",
            "- 任何券商 API、真实下单、真实账户读取。",
        ]
    )


def render_intelligence_plan() -> str:
    return "\n".join(
        [
            f"# 情报数据抓取规划 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "本规划只用于研究层，不接入正式交易执行。",
            "",
            "## 数据类型",
            "| 类型 | 可能来源 | 初期用途 | 风险 |",
            "| --- | --- | --- | --- |",
            "| 行业新闻 | AKShare/东方财富/财联社/官方媒体 | 解释层、风险提醒 | 噪声、重复、滞后 |",
            "| 政策事件 | 交易所/证监会/部委官网/新闻源 | 事件标记、人工复核 | 发布时间和可得时间错配 |",
            "| 资金流/成交热度 | AKShare/Tushare/公开数据 | 风险过滤、拥挤度观察 | 接口稳定性和口径变化 |",
            "| ETF 溢价/QDII 信息 | 交易所/基金公告/公开行情 | QDII 自动交易禁用或降权 | 缺少实时溢价易误判 |",
            "| 主题关键词 | 本地关键词库 + 新闻标题 | 主题热度衰减研究 | 小作文和追涨风险 |",
            "",
            "## 初期接入原则",
            "- 先做 explanation/risk_filter，不做 BUY 主因子。",
            "- 每条情报必须记录 `publish_time`、`fetch_time`、`available_date`、`source`、`url/title/hash`。",
            "- 同一标题/正文 hash 去重，低可信来源降权。",
            "- 收盘后生成的信号只能使用当时已可得的信息。",
            "- 对主题 ETF 只生成 `positive / neutral / negative / noisy / event_risk` 标签。",
            "",
            "## 推荐落地顺序",
            "1. 建立本地 `data/intelligence_staging/`，只存研究样本。",
            "2. 用 AKShare/Tushare 做低频接口可用性测试。",
            "3. 按 ETF group 维护关键词映射，不直接驱动交易。",
            "4. 在 dashboard 展示情报标签和风险，不改 paper_trade_engine。",
            "5. 至少积累 1-3 个月 shadow tracking 后再评估是否降权接入。",
        ]
    )


def render_no_lookahead_rules() -> str:
    return "\n".join(
        [
            f"# 无未来函数数据规则 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "本规则适用于行情、新闻、资金流、政策事件和未来所有情报数据。",
            "",
            "## 核心规则",
            "1. T 日收盘后生成的信号，只能使用 T 日收盘时已经确认可得的数据。",
            "2. 任何 T 日之后发布、抓取或修订的数据，不得用于生成 T 日信号。",
            "3. 所有新数据必须包含 `source`、`fetch_time`、`available_date`。",
            "4. 新闻/事件必须额外包含 `publish_time`；若无法确认发布时间，只能作为人工解释，不进模型。",
            "5. QDII 和跨市场数据必须记录海外交易日和本地可得时间，默认不自动交易。",
            "6. 回测中不能用完整未来样本决定当日 ETF 池、阈值或分组表现。",
            "7. 参数研究必须单独标注 in-sample / out-of-sample / shadow tracking。",
            "",
            "## 日线数据时点",
            "- BaoStock/JQData/Tushare/AKShare 获取的日线，只有在本地写入并通过 validate/health 后才能进入研究。",
            "- `available_date` 默认不得早于该数据在本地可验证的日期。",
            "- 当日收盘价若实际在盘后才可得，只能用于收盘后报告或次日模拟执行判断。",
            "",
            "## 情报数据时点",
            "- 新闻标题看到不等于模型可用；必须记录抓取时间。",
            "- 同一事件的后续解读不得回填到事件发生日前。",
            "- 人工复核标签需要记录复核时间，不能回写历史信号。",
            "",
            "## 禁止事项",
            "- 用未来收益筛选当天 BUY 候选。",
            "- 为了回测好看降低样本要求或改 ETF 池。",
            "- 把尚未验证的新闻情绪直接接入 paper_trade_engine。",
        ]
    )


def render_next_step(audit: dict[str, Any]) -> str:
    phase4c = build_phase4c_summary(audit)
    return "\n".join(
        [
            f"# Phase 4C-Data 下一步建议 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 当前结论",
            f"- AKShare 状态：{phase4c['akshare_status']}",
            f"- 推荐下一步：{phase4c['recommended_next_step']}",
            "",
            "## 建议路线",
            "1. 不替换当前日常更新主链路，先保留 BaoStock/local cache 的稳定路径。",
            "2. 若 Tushare token 可用，下一阶段只做 staging dry-run，不直接正式写入。",
            "3. AKShare 若可用，优先做情报/特殊数据和低频补充，不做 183 只 ETF 日更主源。",
            "4. 新 provider 层先做 dry-run 报告，对比现有 update_etf_data.py 的结果。",
            "5. 所有情报数据先进入 dashboard 解释层和 research/shadow，不接执行层。",
            "",
            "## Phase 4D 候选任务",
            "- 建立 provider dry-run orchestrator。",
            "- 建立 intelligence_staging schema 和关键词映射样例。",
            "- 对 Tushare 日线做 5-10 只 ETF staging 对比测试。",
            "- 对 AKShare 做一周低频稳定性监控。",
            "- 在 dashboard 增加 source freshness / provider circuit breaker 展示。",
        ]
    )


def _universe_snapshot() -> dict[str, Any]:
    etf_files = sorted((DATA_DIR / "etf_daily").glob("*.csv")) if (DATA_DIR / "etf_daily").exists() else []
    backtest_pool = _read_csv(DATA_DIR / "backtest_trade_pool.csv")
    watchlist = _read_csv(PROJECT_ROOT / "watchlist.csv")
    candidates = _read_csv(DATA_DIR / "etf_pool_expansion_candidates.csv")
    latest_dates: list[str] = []
    for path in etf_files[:]:
        try:
            df = pd.read_csv(path, usecols=["date"])
            if not df.empty:
                latest_dates.append(str(pd.to_datetime(df["date"], errors="coerce").max().date()))
        except Exception:
            continue
    return {
        "etf_daily_file_count": len(etf_files),
        "backtest_trade_pool_rows": int(len(backtest_pool)),
        "watchlist_rows": int(len(watchlist)),
        "expansion_candidate_rows": int(len(candidates)),
        "latest_data_date": max(latest_dates) if latest_dates else "",
    }


def _file_snapshot(path: Path) -> dict[str, Any]:
    exists = path.exists()
    text = ""
    if exists and path.is_file():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            text = ""
    return {
        "path": str(path.relative_to(PROJECT_ROOT)) if path.exists() or PROJECT_ROOT in path.parents else str(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists and path.is_file() else 0,
        "mentions_baostock": "baostock" in text.lower(),
        "mentions_jqdata": "jqdata" in text.lower(),
        "mentions_tushare": "tushare" in text.lower(),
        "mentions_akshare": "akshare" in text.lower(),
        "mentions_staging": "staging" in text.lower(),
        "mentions_available_date": "available_date" in text.lower(),
        "line_count": len(text.splitlines()) if text else 0,
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"read_error": str(exc)}
    return {}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    for encoding in ["utf-8-sig", "utf-8", "gbk", "gb18030"]:
        try:
            return pd.read_csv(path, dtype=str, encoding=encoding).fillna("")
        except UnicodeDecodeError:
            continue
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


if __name__ == "__main__":
    main()
