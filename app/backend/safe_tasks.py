"""Whitelisted local tasks for the dynamic app.

The frontend may request only a task name. It can never pass shell commands,
paths, credentials, or trading instructions.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
PYTHON = str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))
STABLE_DATE_TOKEN = "__LATEST_STABLE_BUSINESS_DATE__"


class StableObservationUnavailableError(RuntimeError):
    pass


class TargetDateMismatchError(ValueError):
    def __init__(self, requested: str, latest_stable: str):
        super().__init__(f"requested target {requested!r} does not match latest stable business date {latest_stable!r}")
        self.requested = requested
        self.latest_stable = latest_stable


@dataclass(frozen=True)
class CommandSpec:
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskSpec:
    name: str
    description: str
    safe_note: str
    modifies_paper_positions: bool
    real_trade: bool
    commands: list[CommandSpec]


def _cmd(*args: str, env: dict[str, str] | None = None) -> CommandSpec:
    return CommandSpec(list(args), env or {})


def _today() -> str:
    return date.today().isoformat()


def _previous_weekday(day: date) -> date:
    day = day - timedelta(days=1)
    while day.weekday() >= 5:
        day = day - timedelta(days=1)
    return day


def _daily_update_end() -> str:
    """Use the latest plausibly published A-share daily bar as the target."""
    now = datetime.now()
    today = now.date()
    if today.weekday() >= 5:
        while today.weekday() >= 5:
            today = today - timedelta(days=1)
        return today.isoformat()
    if now.hour < 18:
        return _previous_weekday(today).isoformat()
    return today.isoformat()


def latest_stable_observation(project_root: Path | None = None) -> dict[str, str] | None:
    """Return the latest day confirmed by two consecutive complete equal snapshots."""
    root = (project_root or PROJECT_ROOT).resolve()
    evidence_root = root / "data/staging/tushare_etf_availability"
    for day_dir in sorted(evidence_root.glob("????-??-??"), reverse=True):
        rows: list[dict] = []
        for path in sorted((day_dir / "tushare/manifests").glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if payload.get("evidence_mode") == "real":
                rows.append(payload)
        latest_by_probe: dict[str, dict] = {}
        for row in sorted(rows, key=lambda item: str(item.get("completed_at", ""))):
            latest_by_probe[str(row.get("probe_id", ""))] = row
        previous: dict | None = None
        stable: dict | None = None
        for row in sorted(latest_by_probe.values(), key=lambda item: str(item.get("scheduled_at", ""))):
            if not _is_stable_quality_snapshot(row):
                previous = row
                stable = None
                continue
            current_hash = str(row.get("source_snapshot_hash", ""))
            if previous is not None and _is_stable_quality_snapshot(previous):
                previous_hash = str(previous.get("source_snapshot_hash", ""))
                stable = row if current_hash and current_hash == previous_hash else None
            else:
                stable = None
            previous = row
        if stable is not None:
            return {
                "business_date": day_dir.name,
                "manifest_hash": str(stable.get("source_snapshot_hash", "")),
                "confirmed_at": str(stable.get("scheduled_at", "")),
            }
    return None


def resolve_backfill_target(requested_date: str | None, project_root: Path | None = None) -> dict[str, str]:
    observation = latest_stable_observation(project_root)
    if observation is None:
        raise StableObservationUnavailableError("no FIRST_STABLE observation is available")
    latest_stable = observation["business_date"]
    requested = str(requested_date or latest_stable)
    try:
        normalized = date.fromisoformat(requested).isoformat()
    except ValueError as exc:
        raise TargetDateMismatchError(requested, latest_stable) from exc
    if normalized != latest_stable:
        raise TargetDateMismatchError(normalized, latest_stable)
    return observation


def _is_stable_quality_snapshot(row: dict) -> bool:
    required = int(row.get("required_etf_count", 0) or 0)
    return (
        row.get("response_status") == "ACCESS_PASS"
        and required == 183
        and int(row.get("matched_etf_count", 0) or 0) == required
        and bool(row.get("quality_complete"))
        and bool(row.get("field_complete"))
        and bool(row.get("trade_date_valid"))
    )


def _recent_start() -> str:
    return (date.fromisoformat(_daily_update_end()) - timedelta(days=21)).isoformat()


SAFE_TASKS: dict[str, TaskSpec] = {
    "check_app_env": TaskSpec(
        "check_app_env",
        "检查脱离 PyCharm 独立启动环境。",
        "只读检查本地 App 环境；不打印密码；不会真实下单。",
        False,
        False,
        [_cmd("bash", "scripts/check_app_env.sh")],
    ),
    "check_data_source": TaskSpec(
        "check_data_source",
        "小样本检查日常数据源状态。",
        "dry-run 小样本数据源检查；不写正式 ETF 数据；不会真实下单。",
        False,
        False,
        [
            _cmd(
                PYTHON,
                "scripts/update_etf_data.py",
                "--source",
                "auto",
                "--primary",
                "baostock",
                "--fallback",
                "jqdata",
                "--symbols",
                "510300",
                "159915",
                "--start",
                _today(),
                "--end",
                _daily_update_end(),
                "--dry-run",
                "--skip-existing",
                "--skip-backfill",
                "--source-ready-probe",
                "--max-api-calls",
                "100",
                "--request-timeout",
                "15",
                "--login-retries",
                "1",
                "--retries",
                "0",
                "--status-json",
                "reports/data_update_status.datasource_check.json",
            )
        ],
    ),
    "health_check": TaskSpec(
        "health_check",
        "刷新静态看板快照，验证本地报告可读。",
        "不会真实下单；不会修改模拟持仓。",
        False,
        False,
        [_cmd(PYTHON, "dashboard/build_dashboard.py")],
    ),
    "update_daily_data": TaskSpec(
        "update_daily_data",
        "按正式 ETF universe 执行稳健日更并刷新派生绩效。",
        "只更新本地 ETF 日线与派生绩效报告；不改交易流水或持仓；不接券商；不会真实下单。",
        False,
        False,
        [
            _cmd(
                PYTHON,
                "scripts/update_etf_data.py",
                "--source",
                "auto",
                "--primary",
                "baostock",
                "--fallback",
                "jqdata",
                "--all-etf",
                "--skip-existing",
                "--skip-backfill",
                "--max-api-calls",
                "50000",
                "--end",
                _daily_update_end(),
                "--adjustflag",
                "2",
                "--request-timeout",
                "20",
                "--login-retries",
                "2",
                "--login-retry-delay",
                "3",
                "--retries",
                "1",
                "--retry-delay",
                "2",
                "--request-interval",
                "0.05",
                "--relogin-every",
                "60",
                "--max-consecutive-failures",
                "20",
                "--status-json",
                "reports/data_update_status.json",
            ),
            _cmd(PYTHON, "src/data_coverage.py"),
            _cmd(PYTHON, "src/data_health.py"),
            _cmd(PYTHON, "src/paper_performance.py"),
            _cmd(PYTHON, "src/paper_equity_backfill.py"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
    "backfill_etf_data": TaskSpec(
        "backfill_etf_data",
        "一键补齐 ETF 数据。",
        "使用 Tushare 生成完整 ETF 候选目录；正式 Promotion 默认关闭；无 BaoStock/JQData fallback。",
        False,
        False,
        [
            _cmd(
                PYTHON,
                "scripts/update_etf_data_tushare.py",
                "--trade-date",
                STABLE_DATE_TOKEN,
                "--status-json",
                "reports/data_update_status.json",
            ),
            _cmd(PYTHON, "src/data_coverage.py"),
            _cmd(PYTHON, "src/data_health.py"),
            _cmd(PYTHON, "src/paper_performance.py"),
            _cmd(PYTHON, "src/paper_equity_backfill.py"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
    "backfill_recent_data": TaskSpec(
        "backfill_recent_data",
        "补齐最近约三周 ETF 日线缺口。",
        "只写本地行情 CSV 与派生绩效报告；本地原行优先；不改交易流水或持仓；不会真实下单。",
        False,
        False,
        [
            _cmd(
                PYTHON,
                "scripts/update_etf_data.py",
                "--source",
                "auto",
                "--primary",
                "baostock",
                "--fallback",
                "jqdata",
                "--all-etf",
                "--skip-existing",
                "--source-ready-probe",
                "--max-api-calls",
                "50000",
                "--start",
                _recent_start(),
                "--end",
                _today(),
                "--adjustflag",
                "2",
                "--request-timeout",
                "20",
                "--login-retries",
                "2",
                "--login-retry-delay",
                "3",
                "--retries",
                "1",
                "--retry-delay",
                "2",
                "--request-interval",
                "0.05",
                "--relogin-every",
                "60",
                "--max-consecutive-failures",
                "20",
                "--status-json",
                "reports/data_update_status.json",
            ),
            _cmd(PYTHON, "src/data_coverage.py"),
            _cmd(PYTHON, "src/data_health.py"),
            _cmd(PYTHON, "src/paper_performance.py"),
            _cmd(PYTHON, "src/paper_equity_backfill.py"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
    "run_daily_close_dryrun": TaskSpec(
        "run_daily_close_dryrun",
        "完整 daily_close dry-run。",
        "dry-run 模式；不修改 paper_trades / paper_positions；不会真实下单。",
        False,
        False,
        [_cmd("bash", "scripts/run_daily_close.sh", env={"DAILY_CLOSE_DRY_RUN": "1"})],
    ),
    "run_paper_engine_dryrun": TaskSpec(
        "run_paper_engine_dryrun",
        "模拟交易引擎 dry-run。",
        "只生成计划；不写模拟交易和持仓；不会真实下单。",
        False,
        False,
        [_cmd(PYTHON, "scripts/run_paper_execution_guarded.py", "--dry-run")],
    ),
    "run_paper_performance": TaskSpec(
        "run_paper_performance",
        "刷新模拟仓绩效统计。",
        "只生成模拟仓绩效派生报告；不改交易流水；不改持仓；不会真实下单。",
        False,
        False,
        [
            _cmd(PYTHON, "src/paper_performance.py"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
    "run_trade_review": TaskSpec(
        "run_trade_review",
        "生成交易复盘报告。",
        "只生成交易复盘派生报告；不改交易流水；不改持仓；不改交易引擎；不会真实下单。",
        False,
        False,
        [
            _cmd(PYTHON, "src/trade_review.py"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
    "run_paper_equity_backfill": TaskSpec(
        "run_paper_equity_backfill",
        "回填模拟仓历史权益曲线。",
        "只生成权益曲线派生文件；不改交易流水；不改持仓；不改交易引擎；不会真实下单。",
        False,
        False,
        [
            _cmd(PYTHON, "src/paper_equity_backfill.py"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
    "create_app_shortcut": TaskSpec(
        "create_app_shortcut",
        "创建本地 App 快捷图标。",
        "只生成本地启动包装器和图标资源；不读取密钥；不接券商；不会真实下单。",
        False,
        False,
        [
            _cmd("bash", "scripts/create_app_shortcut.sh"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
    "diagnose_app_launch": TaskSpec(
        "diagnose_app_launch",
        "诊断 App 启动问题。",
        "只检查本地启动环境、端口、权限和日志；不读取密钥；不接券商；不会真实下单。",
        False,
        False,
        [
            _cmd("bash", "scripts/diagnose_app_launch.sh"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
    "fix_app_launch_permissions": TaskSpec(
        "fix_app_launch_permissions",
        "修复 App 启动权限。",
        "只修复本地启动脚本和 App 包装器权限；不改模型；不改交易流水；不会真实下单。",
        False,
        False,
        [
            _cmd("bash", "scripts/fix_app_launch_permissions.sh"),
            _cmd("bash", "scripts/diagnose_app_launch.sh"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
    "run_strategy_preview": TaskSpec(
        "run_strategy_preview",
        "刷新策略增强预览。",
        "只更新研究报告；不接入执行层。",
        False,
        False,
        [_cmd(PYTHON, "src/strategy_enhancement_preview.py")],
    ),
    "run_strategy_tracking": TaskSpec(
        "run_strategy_tracking",
        "刷新 original vs adjusted 影子跟踪。",
        "只更新研究账本；不执行交易。",
        False,
        False,
        [_cmd(PYTHON, "src/strategy_preview_tracking.py")],
    ),
    "run_strategy_preview_tracking": TaskSpec(
        "run_strategy_preview_tracking",
        "刷新 original vs adjusted 影子跟踪。",
        "只更新研究账本；不执行交易。",
        False,
        False,
        [_cmd(PYTHON, "src/strategy_preview_tracking.py")],
    ),
    "run_persistence_breakout_shadow": TaskSpec(
        "run_persistence_breakout_shadow",
        "刷新 persistence_breakout_v2 影子跟踪。",
        "只更新 shadow tracking 报告；不写模拟持仓；不执行交易。",
        False,
        False,
        [
            _cmd(PYTHON, "src/persistence_breakout_shadow.py"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
    "run_missed_opportunity_tracker": TaskSpec(
        "run_missed_opportunity_tracker",
        "刷新 missed opportunity 事后追踪。",
        "只更新 diagnostics/tracking 报告；不改规则；不写模拟持仓；不执行交易。",
        False,
        False,
        [
            _cmd(PYTHON, "src/missed_opportunity_tracker.py"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
    "run_shadow_observation_weekly": TaskSpec(
        "run_shadow_observation_weekly",
        "刷新每周 shadow observation 复盘。",
        "只更新每周观察报告；不改模型规则；不写模拟持仓；不执行交易。",
        False,
        False,
        [
            _cmd(PYTHON, "src/shadow_observation_weekly.py"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
    "build_dashboard": TaskSpec(
        "build_dashboard",
        "生成静态 dashboard fallback。",
        "只生成本地 HTML/JSON；不会真实下单。",
        False,
        False,
        [_cmd(PYTHON, "dashboard/build_dashboard.py")],
    ),
    "run_dashboard_build": TaskSpec(
        "run_dashboard_build",
        "生成静态 dashboard fallback。",
        "只生成本地 HTML/JSON；不会真实下单。",
        False,
        False,
        [_cmd(PYTHON, "dashboard/build_dashboard.py")],
    ),
    "refresh_all_reports": TaskSpec(
        "refresh_all_reports",
        "刷新信号、持仓估值、研究和看板。",
        "不会运行模拟交易执行；不会真实下单。",
        False,
        False,
        [
            _cmd(PYTHON, "src/main.py"),
            _cmd(PYTHON, "src/paper_portfolio.py"),
            _cmd(PYTHON, "src/paper_performance.py"),
            _cmd(PYTHON, "src/paper_equity_backfill.py"),
            _cmd(PYTHON, "src/trade_review.py"),
            _cmd(PYTHON, "src/sell_signal_review.py"),
            _cmd(PYTHON, "src/market_state.py"),
            _cmd(PYTHON, "src/etf_classifier.py"),
            _cmd(PYTHON, "src/portfolio_exposure.py"),
            _cmd(PYTHON, "src/strategy_enhancement_preview.py"),
            _cmd(PYTHON, "src/strategy_preview_tracking.py"),
            _cmd(PYTHON, "src/persistence_breakout_shadow.py"),
            _cmd(PYTHON, "src/missed_opportunity_tracker.py"),
            _cmd(PYTHON, "src/shadow_observation_weekly.py"),
            _cmd(PYTHON, "dashboard/build_dashboard.py"),
        ],
    ),
}


FORBIDDEN_TASK_NAMES = {
    "real_buy",
    "real_sell",
    "broker_login",
    "read_real_account",
    "sync_real_position",
}


def get_task(task_name: str, target_business_date: str | None = None) -> TaskSpec | None:
    if task_name in FORBIDDEN_TASK_NAMES:
        return None
    task = SAFE_TASKS.get(task_name)
    if task is None or task_name != "backfill_etf_data":
        return task
    if not target_business_date:
        raise StableObservationUnavailableError("backfill_etf_data requires a resolved FIRST_STABLE business date")
    commands = [
        CommandSpec(
            [target_business_date if arg == STABLE_DATE_TOKEN else arg for arg in command.args],
            dict(command.env),
        )
        for command in task.commands
    ]
    return TaskSpec(
        task.name,
        task.description,
        task.safe_note,
        task.modifies_paper_positions,
        task.real_trade,
        commands,
    )


def merged_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    if extra:
        env.update(extra)
    env["REAL_TRADE_ENABLED"] = "0"
    env["BROKER_API_ENABLED"] = "0"
    return env
