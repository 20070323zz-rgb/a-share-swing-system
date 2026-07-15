#!/usr/bin/env python3
"""Run one read-only ETF availability probe or the current scheduled slot."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_sources.tushare.availability_models import AuditPaths, active_tushare_times, schedule_times  # noqa: E402
from data_sources.tushare.availability_summary import build_availability_reports  # noqa: E402
from data_sources.tushare.etf_availability_probe import (  # noqa: E402
    load_audit_config,
    record_missed_probe,
    refresh_trade_calendar,
    run_availability_probe,
    write_universe_mapping_report,
)


TZ = ZoneInfo("Asia/Shanghai")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/tushare_etf_availability_audit.yaml")
    parser.add_argument("--source", choices=("tushare", "baostock", "scheduled"), default="scheduled")
    parser.add_argument("--trade-date", help="Target date, YYYY-MM-DD. Defaults to today in Asia/Shanghai.")
    parser.add_argument("--scheduled-time", help="Scheduled slot, HH:MM. Required for an explicit source.")
    parser.add_argument("--refresh-calendar-only", action="store_true")
    parser.add_argument("--reconcile-missed", action="store_true", help="Record elapsed unobserved slots as MISSED_PROBE.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_audit_config(args.config)
    now = datetime.now(TZ)
    trade_date = args.trade_date or now.date().isoformat()
    mapping = write_universe_mapping_report(ROOT, config)
    if not mapping["mapping_complete"]:
        raise SystemExit(f"Universe mapping failed: {mapping}")

    paths = AuditPaths.from_config(ROOT, config)
    if args.refresh_calendar_only:
        calendar = refresh_trade_calendar(ROOT, config, anchor_date=datetime.fromisoformat(trade_date).date())
        print(json.dumps({key: calendar[key] for key in ("response_status", "date_min", "date_max", "request_count")}, ensure_ascii=False))
        return 0 if calendar["response_status"] == "ACCESS_PASS" else 2

    if not _calendar_has_date(paths.calendar_cache, trade_date):
        refresh_trade_calendar(ROOT, config, anchor_date=datetime.fromisoformat(trade_date).date())

    if args.reconcile_missed or args.source == "scheduled":
        _reconcile_missed(ROOT, config, paths.calendar_cache, now)

    if args.source == "scheduled":
        scheduled_time = _current_slot(now, active_tushare_times(config), int(config["schedule"]["tolerance_minutes"]))
        if not scheduled_time:
            build_availability_reports(ROOT, config)
            print(json.dumps({"status": "NO_SCHEDULED_SLOT", "now": now.isoformat(timespec="seconds")}, ensure_ascii=False))
            return 0
        sources = ["tushare"]
        if scheduled_time in config["schedule"]["baostock_times"]:
            sources.append("baostock")
    else:
        if not args.scheduled_time:
            raise SystemExit("--scheduled-time is required when --source is tushare or baostock")
        scheduled_time = args.scheduled_time
        sources = [args.source]

    results = []
    for source in sources:
        results.append(run_availability_probe(
            ROOT,
            config,
            source=source,
            trade_date=trade_date,
            scheduled_time=scheduled_time,
            now=now,
        ))
    summary = build_availability_reports(ROOT, config)
    print(json.dumps({
        "results": [{key: item.get(key) for key in ("source", "probe_id", "response_status", "matched_etf_count", "coverage_ratio", "quality_complete", "manifest_path")} for item in results],
        "audit_status": summary["status"],
        "observation_days_completed": summary["observation_days_completed"],
    }, ensure_ascii=False, indent=2))
    blocked = {"BLOCKED_TOKEN_MISSING", "BLOCKED_CALENDAR_UNCONFIRMED", "PERMISSION_BLOCKED", "NETWORK_FAILED"}
    return 2 if any(item.get("response_status") in blocked for item in results) else 0


def _calendar_has_date(path: Path, trade_date: str) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return any(row.get("cal_date") == trade_date for row in payload.get("rows", []))


def _current_slot(now: datetime, times: list[str], tolerance: int) -> str:
    current = now.hour * 60 + now.minute
    candidates = []
    for value in times:
        hour, minute = map(int, value.split(":"))
        delta = current - (hour * 60 + minute)
        if 0 <= delta <= tolerance:
            candidates.append((delta, value))
    return min(candidates)[1] if candidates else ""


def _reconcile_missed(project_root: Path, config: dict, calendar_path: Path, now: datetime) -> None:
    try:
        calendar = json.loads(calendar_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    tolerance = int(config["schedule"]["tolerance_minutes"])
    for row in calendar.get("rows", []):
        if int(row.get("is_open", 0)) != 1 or not row.get("cal_date"):
            continue
        trade_date = str(row["cal_date"])
        if trade_date < str(config["activation_date"]):
            continue
        if trade_date > now.date().isoformat():
            continue
        for source in ("tushare", "baostock"):
            times = schedule_times(config, source, trade_date)
            for value in times:
                deadline = datetime.fromisoformat(f"{trade_date}T{value}:00").replace(tzinfo=TZ) + timedelta(minutes=tolerance)
                if now > deadline:
                    record_missed_probe(
                        project_root,
                        config,
                        source=source,
                        trade_date=trade_date,
                        scheduled_time=value,
                        reason="Scheduled slot elapsed while the observer was unavailable; no vendor availability inference was made.",
                        now=now,
                    )


if __name__ == "__main__":
    raise SystemExit(main())
