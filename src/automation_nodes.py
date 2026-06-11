"""Trading-day automation reports for the local paper ETF system.

The reports in this module are read-only checks or offline research outputs.
They never connect to broker APIs, never place orders, and never read or store
account credentials.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import pandas as pd

from backtest import run_backtest
from config import DATA_DIR, ETF_DAILY_DIR, INITIAL_CASH, REPORT_DIR, WATCHLIST_FILE
from data_loader import read_watchlist
from factor_analysis import write_factor_analysis_report
from model_research import write_model_research_report


NODE_DEFINITIONS = {
    "open_check": {
        "title": "开盘风险观察",
        "md": REPORT_DIR / "open_check.md",
        "json": REPORT_DIR / "open_check.json",
        "time_window": "09:40",
        "conclusion": "observe_only",
        "purpose": "开盘后只做风险观察，不主动买入。",
    },
    "midday_check": {
        "title": "午盘模拟执行检查",
        "md": REPORT_DIR / "midday_check.md",
        "json": REPORT_DIR / "midday_check.json",
        "time_window": "12:40",
        "conclusion": "review_before_afternoon",
        "purpose": "午盘判断下午是否需要人工复核模拟执行计划。",
    },
    "afternoon_open_check": {
        "title": "下午开盘复核",
        "md": REPORT_DIR / "afternoon_open_check.md",
        "json": REPORT_DIR / "afternoon_open_check.json",
        "time_window": "13:10",
        "conclusion": "manual_review_only",
        "purpose": "下午开盘后复核风险与模拟计划，不真实下单。",
    },
}

ROLLING_WINDOWS = [20, 60, 120]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ETF 模拟盘交易日自动化节点")
    parser.add_argument(
        "--node",
        choices=[
            "open_check",
            "midday_check",
            "afternoon_open_check",
            "daily_rolling_backtest",
            "weekly_full_review",
            "monthly_model_review",
            "sync_report",
            "all_reports",
        ],
        required=True,
    )
    parser.add_argument("--dry-run", action="store_true", help="标记为 dry-run；仍会写本地检查报告。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if args.node in NODE_DEFINITIONS:
        path = write_intraday_node_report(args.node, dry_run=args.dry_run)
        print(f"已生成{NODE_DEFINITIONS[args.node]['title']}报告：{path}")
    elif args.node == "daily_rolling_backtest":
        path = write_daily_rolling_backtest_report(dry_run=args.dry_run)
        print(f"已生成每日轻量滚动回测报告：{path}")
    elif args.node == "weekly_full_review":
        path = write_weekly_full_review_report(dry_run=args.dry_run)
        print(f"已生成周度完整复盘报告：{path}")
    elif args.node == "monthly_model_review":
        path = write_monthly_model_review_report(dry_run=args.dry_run)
        print(f"已生成月度模型复盘报告：{path}")
    elif args.node == "sync_report":
        path = write_four_node_sync_report(dry_run=args.dry_run)
        print(f"已生成四节点同步报告：{path}")
    elif args.node == "all_reports":
        for node in NODE_DEFINITIONS:
            write_intraday_node_report(node, dry_run=args.dry_run)
        write_daily_rolling_backtest_report(dry_run=args.dry_run)
        write_weekly_full_review_report(dry_run=args.dry_run)
        write_monthly_model_review_report(dry_run=args.dry_run)
        path = write_four_node_sync_report(dry_run=args.dry_run)
        print(f"已生成全部自动化报告，汇总：{path}")


def write_intraday_node_report(node: str, dry_run: bool = False) -> Path:
    definition = NODE_DEFINITIONS[node]
    positions = _read_positions()
    latest_map = _latest_price_map()
    health = _health_summary()
    rows = _position_check_rows(positions, latest_map)
    alerts = _risk_alerts(rows, health)
    generated_at = _now_text()
    payload = {
        "node": node,
        "title": definition["title"],
        "generated_at": generated_at,
        "time_window": definition["time_window"],
        "dry_run": dry_run,
        "position_count": len(rows),
        "positions": rows,
        "alerts": alerts,
        "conclusion": definition["conclusion"],
        "safety": _safety_payload(),
    }
    definition["json"].write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# {definition['title']}",
        "",
        f"- 检查时间：{generated_at}",
        f"- 建议运行窗口：{definition['time_window']}",
        f"- dry-run：{'yes' if dry_run else 'no'}",
        f"- 节点目标：{definition['purpose']}",
        "- 数据来源：本地 ETF 日线、模拟持仓、模拟交易与已有报告。",
        "- 当日分时行情：未接入；如无可靠分时数据，仅使用最近本地收盘价做观察。",
        "",
        "## 当前持仓",
    ]
    if not rows:
        lines.append("- 当前无模拟持仓。")
    else:
        lines += [
            "| symbol | name | entry_date | entry_price | latest_close | stop_loss | market_value | unrealized_pnl | risk_alert |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
        for row in rows:
            lines.append(
                f"| {row['symbol']} | {row['name']} | {row['entry_date']} | {row['entry_price']:.4f} | "
                f"{row['latest_close']:.4f} | {row['stop_loss']:.4f} | {row['market_value']:.2f} | "
                f"{row['unrealized_pnl']:.2f} | {row['risk_alert'] or '无'} |"
            )
    lines += [
        "",
        "## 风险观察",
    ]
    if alerts:
        lines += [f"- {item}" for item in alerts]
    else:
        lines.append("- 未发现需要升级处理的模拟盘风险。")
    lines += [
        "",
        "## 节点结论",
        f"- conclusion：{definition['conclusion']}",
        "- 本节点只允许观察、记录和人工复核提醒。",
        "- 不主动买入，不真实卖出，不生成真实交易指令。",
        "",
        "## 安全边界",
        *_safety_lines(),
    ]
    definition["md"].write_text("\n".join(lines), encoding="utf-8")
    return definition["md"]


def write_daily_rolling_backtest_report(dry_run: bool = False) -> Path:
    positions = _read_positions()
    ranking = _read_buy_ranking_codes(limit=8)
    symbols = _dedupe([*positions.get("symbol", pd.Series(dtype=str)).astype(str).tolist(), *ranking])
    rows = []
    for symbol in symbols:
        price_df = _load_etf_price(symbol)
        if price_df.empty:
            rows.append({"symbol": symbol, "name": _name_for(symbol), "status": "missing_price"})
            continue
        row = {"symbol": symbol, "name": _name_for(symbol), "status": "ok", "latest_date": str(price_df["date"].max().date())}
        for window in ROLLING_WINDOWS:
            stats = _rolling_stats(price_df, window)
            row.update({f"{window}d_return": stats["return"], f"{window}d_max_drawdown": stats["max_drawdown"], f"{window}d_volatility": stats["volatility"]})
        rows.append(row)
    csv_path = REPORT_DIR / "daily_rolling_backtest.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)

    lines = [
        "# 每日轻量滚动回测",
        "",
        f"- 检查时间：{_now_text()}",
        f"- dry-run：{'yes' if dry_run else 'no'}",
        "- 范围：当前模拟持仓 + BUY ranking 前 8。",
        "- 窗口：20 / 60 / 120 日。",
        "- 说明：这是收盘后轻量滚动风险/表现观察，不替代周度完整历史回测。",
        "",
        "| symbol | name | status | latest_date | 20d_return | 60d_return | 120d_return | 20d_max_dd | 60d_max_dd | 120d_max_dd |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('symbol','')} | {row.get('name','')} | {row.get('status','')} | {row.get('latest_date','')} | "
            f"{_pct(row.get('20d_return'))} | {_pct(row.get('60d_return'))} | {_pct(row.get('120d_return'))} | "
            f"{_pct(row.get('20d_max_drawdown'))} | {_pct(row.get('60d_max_drawdown'))} | {_pct(row.get('120d_max_drawdown'))} |"
        )
    lines += ["", "## 安全边界", *_safety_lines()]
    path = REPORT_DIR / "daily_rolling_backtest.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_weekly_full_review_report(dry_run: bool = False) -> Path:
    symbols = _weekly_review_symbols()
    rows = []
    for symbol in symbols:
        for strategy in ["mid_trend", "short_swing"]:
            try:
                summary, _ = run_backtest(symbol, strategy=strategy)
            except Exception as exc:
                summary = {"code": symbol, "name": _name_for(symbol), "strategy": strategy, "error": f"{type(exc).__name__}: {exc}"}
            rows.append(summary)
    csv_path = REPORT_DIR / "weekly_full_backtest_results.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    lines = [
        "# 周度完整复盘",
        "",
        f"- 检查时间：{_now_text()}",
        f"- dry-run：{'yes' if dry_run else 'no'}",
        "- 回测范围：当前持仓、BUY ranking 前 8、核心基准 510300。",
        "- 回测方式：复用 src/backtest.py 的本地 CSV 历史回测，不修改策略规则。",
        "",
        "| code | name | strategy | total_return | max_drawdown | win_rate | trade_count | avg_holding_days | profit_loss_ratio | max_consecutive_losses | note |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in rows:
        if "error" in item:
            lines.append(f"| {item.get('code','')} | {item.get('name','')} | {item.get('strategy','')} |  |  |  |  |  |  |  | {item['error']} |")
            continue
        lines.append(
            f"| {item['code']} | {item['name']} | {item.get('strategy','')} | {_pct(item.get('total_return'))} | "
            f"{_pct(item.get('max_drawdown'))} | {_pct(item.get('win_rate'))} | {item.get('trade_count',0)} | "
            f"{float(item.get('avg_holding_days',0)):.1f} | {float(item.get('profit_loss_ratio',0)):.2f} | "
            f"{item.get('max_consecutive_losses',0)} | {item.get('data_note','')} |"
        )
    lines += [
        "",
        "## 周度复盘结论",
        "- mid_trend 仍为主策略；short_swing 只作为小仓实验观察。",
        "- 回测结果用于复盘和样本积累，不用于自动交易。",
        "",
        "## 安全边界",
        *_safety_lines(),
    ]
    path = REPORT_DIR / "weekly_full_review.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_monthly_model_review_report(dry_run: bool = False) -> Path:
    factor_path = write_factor_analysis_report()
    write_model_research_report()
    candidates = _read_csv(DATA_DIR / "etf_pool_expansion_candidates.csv")
    watchlist = _read_watchlist_safe()
    status_counts = candidates["status"].value_counts().to_dict() if "status" in candidates.columns else {}
    pool_counts = candidates["pool"].value_counts().to_dict() if "pool" in candidates.columns else {}
    watch_counts = watchlist["role"].value_counts().to_dict() if "role" in watchlist.columns else {}
    lines = [
        "# 月度模型复盘",
        "",
        f"- 检查时间：{_now_text()}",
        f"- dry-run：{'yes' if dry_run else 'no'}",
        "- 模型复盘只读取本地 model_dataset.csv 与已有 ETF 池状态。",
        "- 模型结果只用于研究，不参与当天信号，不替代人工确认。",
        "",
        "## 已刷新研究报告",
        f"- 因子报告：{factor_path}",
        "- 模型研究报告：reports/model_research_report.md",
        "",
        "## ETF 池质量摘要",
        f"- watchlist role 分布：{watch_counts}",
        f"- 扩池候选 status 分布：{status_counts}",
        f"- 扩池候选 pool 分布：{pool_counts}",
        "",
        "## 月度检查项",
        "- 因子 IC / Rank IC：见 reports/factor_analysis_report.md。",
        "- 分组表现：见 reports/factor_analysis_report.md 的 group 拆分。",
        "- ETF 池质量：关注 imported、failed_validation、unresolved 的变化。",
        "- 参数稳定性：本轮不修改 mid_trend / short_swing 核心交易规则，只记录表现。",
        "",
        "## 安全边界",
        *_safety_lines(),
    ]
    path = REPORT_DIR / "monthly_model_review.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_four_node_sync_report(dry_run: bool = False) -> Path:
    report_status = _report_status()
    scripts = _script_status()
    launchd = _launchd_status()
    data_files = len(list(ETF_DAILY_DIR.glob("*.csv"))) if ETF_DAILY_DIR.exists() else 0
    lines = [
        "# 四节点自动化同步报告",
        "",
        f"- 检查时间：{_now_text()}",
        f"- dry-run：{'yes' if dry_run else 'no'}",
        f"- 正式 ETF 日线文件数量：{data_files}",
        "- 权限等级：L2 联网数据权限；本轮未读取账号、未接券商、未真实下单。",
        "",
        "## 节点脚本",
        "| node | script | exists | purpose |",
        "| --- | --- | --- | --- |",
    ]
    for item in scripts:
        lines.append(f"| {item['node']} | {item['script']} | {item['exists']} | {item['purpose']} |")
    lines += [
        "",
        "## launchd plist",
        "| label | plist | exists | scheduled |",
        "| --- | --- | --- | --- |",
    ]
    for item in launchd:
        lines.append(f"| {item['label']} | {item['plist']} | {item['exists']} | {item['scheduled']} |")
    lines += [
        "",
        "## 报告同步状态",
        "| report | exists | updated_at |",
        "| --- | --- | --- |",
    ]
    for item in report_status:
        lines.append(f"| {item['report']} | {item['exists']} | {item['updated_at']} |")
    lines += [
        "",
        "## 诊断结论",
        "- 当前 launchd 调用项目内 scripts/run_*.sh 脚本。",
        "- daily_close 使用 update_etf_data.py --all-etf --source baostock --skip-existing，覆盖扩池后正式 ETF 数据目录。",
        "- paper_portfolio.py 已在 src/main.py 中更新模拟盘盈亏。",
        "- dashboard/build_dashboard.py 读取 dashboard_data.json、模拟持仓、交易、ranking 与四节点报告摘要。",
        "- backtest.py、factor_analysis.py、model_research.py 已复用为周/月复盘基础。",
        "",
        "## 安全边界",
        *_safety_lines(),
    ]
    path = REPORT_DIR / "automation_four_node_sync_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _position_check_rows(positions: pd.DataFrame, latest_map: dict[str, dict]) -> list[dict]:
    rows = []
    for item in positions.to_dict(orient="records"):
        symbol = str(item.get("symbol", "")).strip()
        latest = latest_map.get(symbol, {})
        latest_close = _float(latest.get("close"), _float(item.get("current_price"), _float(item.get("entry_price"))))
        quantity = _float(item.get("quantity"))
        cost = _float(item.get("cost"))
        stop_loss = _float(item.get("stop_loss"))
        market_value = latest_close * quantity
        pnl = market_value - cost
        alert = str(item.get("risk_alert", "") or "").strip()
        if stop_loss > 0 and latest_close <= stop_loss:
            alert = "触及或低于模拟止损价"
        if market_value > INITIAL_CASH * 0.20:
            alert = (alert + "；" if alert else "") + "单只 ETF 超过 20% 上限"
        rows.append(
            {
                "symbol": symbol,
                "name": str(item.get("name", "")),
                "entry_date": str(item.get("entry_date", "")),
                "entry_price": _float(item.get("entry_price")),
                "latest_date": str(latest.get("date", "")),
                "latest_close": latest_close,
                "quantity": quantity,
                "cost": cost,
                "stop_loss": stop_loss,
                "market_value": market_value,
                "unrealized_pnl": pnl,
                "risk_alert": alert,
            }
        )
    return rows


def _risk_alerts(rows: list[dict], health: dict) -> list[str]:
    alerts = []
    for row in rows:
        if row["risk_alert"]:
            alerts.append(f"{row['symbol']} {row['name']}：{row['risk_alert']}")
    if health.get("异常") not in ("0", 0, None, ""):
        alerts.append(f"数据健康报告存在异常数量：{health.get('异常')}")
    return alerts


def _rolling_stats(df: pd.DataFrame, window: int) -> dict:
    part = df.tail(window + 1).copy()
    if len(part) < 2:
        return {"return": None, "max_drawdown": None, "volatility": None}
    close = pd.to_numeric(part["close"], errors="coerce").dropna()
    if len(close) < 2:
        return {"return": None, "max_drawdown": None, "volatility": None}
    total_return = close.iloc[-1] / close.iloc[0] - 1
    curve = close / close.iloc[0]
    max_drawdown = (curve / curve.cummax() - 1).min()
    volatility = close.pct_change().dropna().std() * (252 ** 0.5)
    return {"return": float(total_return), "max_drawdown": float(max_drawdown), "volatility": float(volatility)}


def _weekly_review_symbols() -> list[str]:
    positions = _read_positions()
    ranking = _read_buy_ranking_codes(limit=8)
    return _dedupe(["510300", *positions.get("symbol", pd.Series(dtype=str)).astype(str).tolist(), *ranking])


def _read_buy_ranking_codes(limit: int) -> list[str]:
    path = REPORT_DIR / "buy_signal_ranking.md"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    table = [line for line in lines if line.strip().startswith("|")]
    codes = []
    for line in table[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        for cell in cells:
            if cell.isdigit() and len(cell) == 6:
                codes.append(cell)
                break
        if len(codes) >= limit:
            break
    return codes


def _latest_price_map() -> dict[str, dict]:
    result: dict[str, dict] = {}
    for path in ETF_DAILY_DIR.glob("*.csv"):
        symbol = path.stem.split("_")[-1]
        df = _read_csv(path)
        if df.empty or "date" not in df.columns or "close" not in df.columns:
            continue
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["date", "close"]).sort_values("date")
        if df.empty:
            continue
        last = df.iloc[-1]
        result[symbol] = {"date": last["date"].strftime("%Y-%m-%d"), "close": float(last["close"])}
    return result


def _load_etf_price(symbol: str) -> pd.DataFrame:
    for prefix in ["sh", "sz"]:
        path = ETF_DAILY_DIR / f"{prefix}_{symbol}.csv"
        if path.exists():
            df = _read_csv(path)
            if "date" in df.columns and "close" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df["close"] = pd.to_numeric(df["close"], errors="coerce")
                return df.dropna(subset=["date", "close"]).sort_values("date")
    return pd.DataFrame()


def _read_positions() -> pd.DataFrame:
    path = DATA_DIR / "paper_positions.csv"
    return _read_csv(path)


def _read_watchlist_safe() -> pd.DataFrame:
    try:
        return read_watchlist(WATCHLIST_FILE)
    except Exception:
        return _read_csv(WATCHLIST_FILE)


def _name_for(symbol: str) -> str:
    positions = _read_positions()
    if not positions.empty and "symbol" in positions.columns:
        matched = positions[positions["symbol"].astype(str) == str(symbol)]
        if not matched.empty:
            return str(matched.iloc[0].get("name", symbol))
    watchlist = _read_watchlist_safe()
    if not watchlist.empty and "code" in watchlist.columns:
        matched = watchlist[watchlist["code"].astype(str) == str(symbol)]
        if not matched.empty:
            return str(matched.iloc[0].get("name", symbol))
    return symbol


def _health_summary() -> dict:
    path = REPORT_DIR / "latest_data_health.md"
    if not path.exists():
        return {}
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- ") and "：" in line:
            key, value = line[2:].split("：", 1)
            result[key.strip()] = value.strip()
    return result


def _report_status() -> list[dict]:
    names = [
        "open_check.md",
        "midday_check.md",
        "afternoon_open_check.md",
        "daily_rolling_backtest.md",
        "weekly_full_review.md",
        "monthly_model_review.md",
        "latest_brief.md",
        "latest_paper_portfolio.md",
        "buy_signal_ranking.md",
        "dashboard_data.json",
    ]
    return [{"report": name, "exists": (REPORT_DIR / name).exists(), "updated_at": _mtime(REPORT_DIR / name)} for name in names]


def _script_status() -> list[dict]:
    rows = [
        ("open_check", "scripts/run_open_check.sh", "开盘只读风险观察"),
        ("midday_check", "scripts/run_midday_check.sh", "午盘模拟执行检查"),
        ("afternoon_open_check", "scripts/run_afternoon_open_check.sh", "下午开盘复核"),
        ("daily_close_update", "scripts/run_daily_close.sh", "收盘数据更新、主报告、滚动回测、看板刷新"),
        ("weekly_full_review", "scripts/run_weekly_review.sh", "周度完整复盘"),
        ("monthly_model_review", "scripts/run_monthly_model_review.sh", "月度模型复盘"),
    ]
    return [{"node": node, "script": script, "exists": (Path.cwd() / script).exists(), "purpose": purpose} for node, script, purpose in rows]


def _launchd_status() -> list[dict]:
    labels = [
        ("com.dayin.a-share.open-check", "09:40 weekdays"),
        ("com.dayin.a-share.midday-check", "12:40 weekdays"),
        ("com.dayin.a-share.afternoon-open-check", "13:10 weekdays"),
        ("com.dayin.a-share.daily-close", "15:30 weekdays"),
        ("com.dayin.a-share.weekly-review", "15:40 Friday"),
        ("com.dayin.a-share.monthly-model-review", "16:10 day 1 monthly"),
    ]
    rows = []
    for label, scheduled in labels:
        plist = Path.cwd() / "launchd" / f"{label}.plist"
        rows.append({"label": label, "plist": str(plist), "exists": plist.exists(), "scheduled": scheduled})
    return rows


def _safety_payload() -> dict:
    return {
        "broker_api": False,
        "real_order": False,
        "account_credentials": False,
        "auto_trading": False,
        "strategy_rule_change": False,
        "local_paper_only": True,
    }


def _safety_lines() -> list[str]:
    return [
        "- 不接券商 API。",
        "- 不真实下单。",
        "- 不读取真实账户。",
        "- 不保存账号、密码或 token。",
        "- 不自动交易。",
        "- 不修改 mid_trend / short_swing 核心交易规则。",
        "- 所有交易相关输出仅为本地模拟盘和研究报告。",
    ]


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str).fillna("")


def _dedupe(items: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _float(value: object, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    if pd.isna(numeric):
        return fallback
    return numeric


def _pct(value: object) -> str:
    if value is None or value == "":
        return ""
    return f"{_float(value):.2%}"


def _now_text() -> str:
    return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")


def _mtime(path: Path) -> str:
    if not path.exists():
        return ""
    return pd.Timestamp.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    main()
