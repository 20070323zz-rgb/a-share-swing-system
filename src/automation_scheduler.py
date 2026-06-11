"""Catchup scheduler for local launchd automation.

The scheduler compensates for missed launchd times after login/wakeup. It only
runs local scripts for data/reports/paper simulation. It never connects to
broker APIs or places real orders.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess

import pandas as pd

from automation_state import get_day_state, is_success, mark_node, read_state
from config import PROJECT_ROOT, REPORT_DIR


REPORT_FILE = REPORT_DIR / "launchd_catchup_upgrade_report.md"
STATUS_REPORT_FILE = REPORT_DIR / "catchup_scheduler_status.md"

NODE_SCRIPTS = {
    "open_check": "scripts/run_open_check.sh",
    "midday_check": "scripts/run_midday_check.sh",
    "afternoon_open_check": "scripts/run_afternoon_open_check.sh",
    "daily_close": "scripts/run_daily_close.sh",
    "weekly_review": "scripts/run_weekly_review.sh",
    "monthly_model_review": "scripts/run_monthly_model_review.sh",
}

NODE_LABELS = {
    "open_check": "09:40 open_check",
    "midday_check": "12:40 midday_check",
    "afternoon_open_check": "13:10 afternoon_open_check",
    "daily_close": "15:30 daily_close",
    "weekly_review": "Friday weekly_review",
    "monthly_model_review": "Monthly monthly_model_review",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="launchd catchup/supervisor")
    parser.add_argument("--mode", choices=["status", "catchup"], default="status")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--now", help="测试用当前时间，例如 2026-06-10 12:50:00")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    now = pd.Timestamp(args.now) if args.now else pd.Timestamp.now()
    if args.mode == "status":
        actions = plan_actions(now, dry_run=True)
        write_status_report(now, actions, dry_run=True)
        print_status(now, actions)
        return
    actions = plan_actions(now, dry_run=args.dry_run)
    if args.dry_run:
        write_status_report(now, actions, dry_run=True)
        print_status(now, actions)
        return
    executed = execute_actions(actions, now)
    write_status_report(now, executed, dry_run=False)
    print_status(now, executed)


def plan_actions(now: pd.Timestamp, dry_run: bool) -> list[dict]:
    day = now.strftime("%Y-%m-%d")
    if not is_trading_day(now):
        return [{"node": "scheduler", "action": "skip", "reason": "not_trading_day", "status": "skipped"}]

    actions: list[dict] = []
    state = get_day_state(day)
    hhmm = now.hour * 100 + now.minute

    if 940 <= hhmm <= 1239:
        _schedule_run(actions, "open_check", state, "catchup_open_window")
    elif 1240 <= hhmm <= 1309:
        _schedule_missed(actions, "open_check", state, "missed_before_midday")
        _schedule_run(actions, "midday_check", state, "catchup_midday_window")
    elif 1310 <= hhmm <= 1529:
        _schedule_missed(actions, "open_check", state, "missed_before_afternoon")
        _schedule_run(actions, "midday_check", state, "catchup_midday_proxy")
        _schedule_run(actions, "afternoon_open_check", state, "catchup_afternoon_window")
    elif hhmm >= 1530:
        for node in ["open_check", "midday_check", "afternoon_open_check"]:
            _schedule_missed(actions, node, state, "missed_after_close")
        _schedule_run(actions, "daily_close", state, "catchup_after_close")
        if now.weekday() == 4 and hhmm >= 1540:
            latest_state = _projected_state(state, actions)
            if latest_state.get("daily_close", {}).get("status") == "success" or _has_run_action(actions, "daily_close"):
                _schedule_run(actions, "weekly_review", state, "catchup_friday_weekly")
        if _monthly_due(now):
            latest_state = _projected_state(state, actions)
            if latest_state.get("daily_close", {}).get("status") == "success" or _has_run_action(actions, "daily_close"):
                _schedule_run(actions, "monthly_model_review", state, "catchup_monthly")
    else:
        actions.append({"node": "scheduler", "action": "wait", "reason": "before_first_node", "status": "pending"})

    if not actions:
        actions.append({"node": "scheduler", "action": "noop", "reason": "all_due_nodes_success", "status": "success"})
    return actions


def execute_actions(actions: list[dict], now: pd.Timestamp) -> list[dict]:
    result = []
    for action in actions:
        node = action["node"]
        if action["action"] == "run":
            if is_success(node, now.strftime("%Y-%m-%d")):
                result.append({**action, "status": "skipped", "reason": "already_success"})
                continue
            run_result = run_node(node)
            result.append({**action, **run_result})
        elif action["action"] == "mark":
            mark_node(node, action["mark_status"], source="catchup", note=action["reason"])
            result.append({**action, "status": action["mark_status"]})
        else:
            result.append(action)
    return result


def run_node(node: str) -> dict:
    script = NODE_SCRIPTS[node]
    env = os.environ.copy()
    env["AUTOMATION_SOURCE"] = "catchup"
    proc = subprocess.run(["bash", script], cwd=PROJECT_ROOT, env=env, text=True, capture_output=True)
    if proc.returncode == 0:
        return {"status": "success", "returncode": proc.returncode}
    error = (proc.stderr or proc.stdout or f"returncode={proc.returncode}")[-800:]
    mark_node(node, "failed", source="catchup", error=error)
    return {"status": "failed", "returncode": proc.returncode, "error": error}


def write_status_report(now: pd.Timestamp, actions: list[dict], dry_run: bool) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    day_state = get_day_state(now.strftime("%Y-%m-%d"))
    lines = [
        "# Catchup Scheduler Status",
        "",
        f"- 检查时间：{now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- dry-run：{'yes' if dry_run else 'no'}",
        f"- 交易日判断：{'yes' if is_trading_day(now) else 'no'}",
        "- 安全边界：只运行本地数据/报告/模拟盘脚本，不接券商 API，不真实下单。",
        "",
        "## 本次计划/执行",
        "| node | action | status | reason |",
        "| --- | --- | --- | --- |",
    ]
    for item in actions:
        lines.append(f"| {item.get('node','')} | {item.get('action','')} | {item.get('status','planned')} | {item.get('reason','')} |")
    lines += [
        "",
        "## 今日状态",
        "| node | status | last_run | source | note/error |",
        "| --- | --- | --- | --- | --- |",
    ]
    for node in NODE_SCRIPTS:
        record = day_state.get(node, {})
        lines.append(
            f"| {node} | {record.get('status','pending')} | {record.get('last_run','')} | "
            f"{record.get('source','')} | {record.get('note', record.get('error',''))} |"
        )
    STATUS_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    write_upgrade_report()


def write_upgrade_report() -> None:
    lines = [
        "# launchd catchup 自动化升级报告",
        "",
        f"- 生成时间：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- 权限等级：L2 联网数据权限。",
        "- 本报告只说明本地自动化调度，不涉及真实交易。",
        "",
        "## 为什么需要 catchup",
        "- Mac 可能不在固定时间开机、登录或保持唤醒。",
        "- 固定时间 launchd 可能错过节点。",
        "- catchup 每 30 分钟检查一次，判断哪些节点应补跑或标记 missed。",
        "",
        "## 当前 7 个 launchd job",
        "| job | 触发方式 | 作用 |",
        "| --- | --- | --- |",
        "| open_check | 工作日 09:40 | 开盘风险观察 |",
        "| midday_check | 工作日 12:40 | 午盘模拟执行检查 |",
        "| afternoon_open_check | 工作日 13:10 | 下午开盘复核 |",
        "| daily_close | 工作日 15:30 | 收盘数据更新与主报告 |",
        "| weekly_review | 周五 15:40 | 周度完整复盘 |",
        "| monthly_model_review | 每月 1 日 16:10 | 月度模型复盘 |",
        "| catchup_check | RunAtLoad + 每 30 分钟 | 登录/唤醒补偿检查 |",
        "",
        "## 固定时间 job 与 catchup job 分工",
        "- 固定时间 job：在理想情况下按时运行节点。",
        "- catchup job：登录/加载后和每 30 分钟检查状态，补跑仍有意义的节点。",
        "- catchup 不重复执行已经 success 的节点。",
        "",
        "## catchup 补偿规则",
        "- 09:40-12:39：open_check 未成功则补跑。",
        "- 12:40-13:09：midday_check 未成功则补跑，open_check 标记 missed。",
        "- 13:10-15:29：afternoon_open_check 未成功则补跑；midday_check 未成功则补跑 proxy 检查。",
        "- 15:30 后：不再补跑盘中节点；daily_close 未成功则补跑。",
        "- 周五 15:40 后：daily_close 成功后才补跑 weekly_review。",
        "- 每月 1 日 16:10 后：daily_close 成功后才补跑 monthly_model_review。",
        "",
        "## automation_state.json 状态结构",
        "```json",
        "{",
        '  "2026-06-10": {',
        '    "open_check": {"status": "success", "last_run": "2026-06-10 09:40:12", "source": "launchd"},',
        '    "daily_close": {"status": "success", "last_run": "2026-06-10 15:31:08", "source": "catchup"}',
        "  }",
        "}",
        "```",
        "",
        "## 如何避免重复执行",
        "- 每个脚本成功或失败后写入 data/automation_state.json。",
        "- catchup 执行前先检查当日节点是否 status=success。",
        "- success 节点直接跳过。",
        "",
        "## 如何避免重复下载和重复写模拟交易",
        "- daily_close 仍使用 update_etf_data.py --skip-existing 和本地原行优先合并。",
        "- src/main.py 的模拟买入逻辑已有同日同信号幂等检查，不重复写相同模拟买入。",
        "- catchup 不直接写交易，只调用既有本地脚本。",
        "",
        "## 场景示例",
        "- 如果电脑 12:50 开机：open_check 标记 missed，补跑 midday_check。",
        "- 如果电脑 16:00 开机：盘中节点标记 missed_after_close，补跑 daily_close；如果是周五且 daily_close 成功，再补跑 weekly_review。",
        "- 如果电脑当天不开机：不会补跑当天盘中节点；下次开机只处理当前日期。",
        "",
        "## 用户如何查看 catchup 是否运行",
        "- 查看状态：python3 src/automation_scheduler.py --mode status",
        "- 查看状态文件：data/automation_state.json",
        "- 查看日志：logs/catchup_check.log",
        "- 查看 launchd 日志：logs/launchd_catchup_check.out.log 和 logs/launchd_catchup_check.err.log",
        "",
        "## 安全边界确认",
        "- 不接券商 API。",
        "- 不真实下单。",
        "- 不读取真实账户。",
        "- 不保存密码/token。",
        "- 不修改交易规则或仓位规则。",
        "- 不自动调参。",
        "- 不把网页变成交易终端。",
        "- 不删除 ETF 数据。",
        "- 不把 failed/quarantine ETF 放回主流程。",
        "- 不使用未来数据。",
        "- 不绕过人工审查。",
    ]
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def print_status(now: pd.Timestamp, actions: list[dict]) -> None:
    print(f"catchup scheduler checked at {now.strftime('%Y-%m-%d %H:%M:%S')}")
    for item in actions:
        print(f"- {item.get('node')}: {item.get('action')} {item.get('status', 'planned')} {item.get('reason', '')}")
    print(f"status report: {STATUS_REPORT_FILE}")


def is_trading_day(now: pd.Timestamp) -> bool:
    return now.weekday() < 5


def _schedule_run(actions: list[dict], node: str, state: dict, reason: str) -> None:
    if state.get(node, {}).get("status") in {"success", "failed", "missed", "missed_after_close"}:
        return
    actions.append({"node": node, "action": "run", "reason": reason, "status": "planned"})


def _schedule_missed(actions: list[dict], node: str, state: dict, reason: str) -> None:
    if state.get(node, {}).get("status") in {"success", "missed", "missed_after_close"}:
        return
    mark_status = "missed_after_close" if reason == "missed_after_close" else "missed"
    actions.append({"node": node, "action": "mark", "mark_status": mark_status, "reason": reason, "status": "planned"})


def _projected_state(state: dict, actions: list[dict]) -> dict:
    projected = dict(state)
    for action in actions:
        if action.get("action") == "run":
            projected[action["node"]] = {"status": "success"}
    return projected


def _has_run_action(actions: list[dict], node: str) -> bool:
    return any(action.get("node") == node and action.get("action") == "run" for action in actions)


def _monthly_due(now: pd.Timestamp) -> bool:
    return now.day == 1 and (now.hour * 100 + now.minute) >= 1610


if __name__ == "__main__":
    main()
