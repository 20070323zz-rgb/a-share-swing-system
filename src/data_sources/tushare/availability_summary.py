"""Build committed, sanitized summaries from local append-only timing evidence."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from .availability_models import AuditPaths


TZ = ZoneInfo("Asia/Shanghai")
REAL_RESPONSE_STATUSES = {"ACCESS_PASS", "EMPTY_UNEXPECTED", "NETWORK_FAILED", "PERMISSION_BLOCKED", "VALIDATION_FAILED"}
TIMING_COLUMNS = [
    "trade_date", "day_status", "tushare_slots_recorded", "tushare_slots_expected",
    "first_available_time", "first_complete_time", "first_quality_complete_time",
    "first_stable_time", "last_revision_time", "late_revision_risk",
    "sh_first_complete_time", "sz_first_complete_time", "delayed_codes",
    "max_coverage_ratio", "revision_count", "evidence_class",
]
COMPARISON_COLUMNS = [
    "trade_date", "source", "day_status", "first_available_time", "first_complete_time",
    "first_stable_time", "max_coverage_ratio", "error_statuses", "later_than_tushare_minutes",
]


def load_manifests(paths: AuditPaths) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    if not paths.staging_root.exists():
        return manifests
    for path in sorted(paths.staging_root.glob("????-??-??/*/manifests/*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        payload["_manifest_path"] = str(path.relative_to(paths.project_root))
        manifests.append(payload)
    return manifests


def summarize_source_day(
    manifests: list[dict[str, Any]],
    *,
    source: str,
    trade_date: str,
    expected_times: list[str],
    stability_minutes: int,
    late_revision_threshold: str,
) -> dict[str, Any]:
    attempts = [
        item for item in manifests
        if item.get("source") == source
        and item.get("trade_date") == trade_date
        and item.get("evidence_mode") == "real"
        and item.get("response_status") not in {"DUPLICATE_ATTEMPT_SKIPPED", "BLOCKED_EARLY_PROBE"}
    ]
    latest_by_probe: dict[str, dict[str, Any]] = {}
    for item in sorted(attempts, key=lambda row: str(row.get("completed_at", ""))):
        latest_by_probe[str(item.get("probe_id", ""))] = item
    rows = sorted(latest_by_probe.values(), key=lambda row: str(row.get("scheduled_at", "")))
    observed_times = {_hhmm(row.get("scheduled_at", "")) for row in rows}
    recorded = len(set(expected_times) & observed_times)
    all_slots_recorded = recorded == len(expected_times)
    real_slots = [row for row in rows if row.get("response_status") in REAL_RESPONSE_STATUSES]
    day_status = "COMPLETE" if all_slots_recorded and len(real_slots) == len(expected_times) else "IN_PROGRESS"
    if all_slots_recorded and len(real_slots) < len(expected_times):
        day_status = "INCOMPLETE_WITH_MISSED_PROBES"

    available = [row for row in real_slots if int(row.get("matched_etf_count", 0)) > 0]
    complete = [row for row in real_slots if _is_complete(row)]
    quality_complete = [row for row in real_slots if _is_quality_complete(row)]
    first_available = min((_hhmm(row.get("scheduled_at", "")) for row in available), default="")
    first_complete = min((_hhmm(row.get("scheduled_at", "")) for row in complete), default="")
    stable = _first_stable_time(real_slots, stability_minutes) if day_status == "COMPLETE" else ""
    revisions = [row for row in real_slots if bool(row.get("material_revision"))]
    last_revision = max((_hhmm(row.get("scheduled_at", "")) for row in revisions), default="")
    late_risk = bool(last_revision and last_revision >= late_revision_threshold)

    sh_complete = [row for row in real_slots if float(row.get("sh_coverage_ratio", 0)) >= 1.0]
    sz_complete = [row for row in real_slots if float(row.get("sz_coverage_ratio", 0)) >= 1.0]
    delayed = _delayed_codes(real_slots)
    errors = sorted({str(row.get("response_status")) for row in real_slots if row.get("response_status") != "ACCESS_PASS"})
    return {
        "trade_date": trade_date,
        "source": source,
        "day_status": day_status,
        "slots_recorded": recorded,
        "slots_expected": len(expected_times),
        "first_available_time": first_available,
        "first_complete_time": first_complete,
        "first_quality_complete_time": min((_hhmm(row.get("scheduled_at", "")) for row in quality_complete), default=""),
        "first_stable_time": stable,
        "last_revision_time": last_revision,
        "late_revision_risk": late_risk,
        "sh_first_complete_time": min((_hhmm(row.get("scheduled_at", "")) for row in sh_complete), default=""),
        "sz_first_complete_time": min((_hhmm(row.get("scheduled_at", "")) for row in sz_complete), default=""),
        "delayed_codes": ";".join(delayed),
        "max_coverage_ratio": max((float(row.get("coverage_ratio", 0)) for row in real_slots), default=0.0),
        "revision_count": sum(int(row.get("revision_count", 0)) for row in revisions),
        "error_statuses": ";".join(errors),
    }


def build_availability_reports(project_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    root = project_root.resolve()
    paths = AuditPaths.from_config(root, config)
    paths.reports_dir.mkdir(parents=True, exist_ok=True)
    manifests = load_manifests(paths)
    dates = sorted({str(item.get("trade_date")) for item in manifests if item.get("calendar_decision") == "TRADING_DAY_CONFIRMED"})
    tushare_rows = [
        summarize_source_day(
            manifests,
            source="tushare",
            trade_date=trade_date,
            expected_times=list(config["schedule"]["tushare_times"]),
            stability_minutes=int(config["observation"]["stability_min_interval_minutes"]),
            late_revision_threshold=str(config["observation"]["late_revision_threshold"]),
        )
        for trade_date in dates
    ]
    complete_days = sum(row["day_status"] == "COMPLETE" for row in tushare_rows)
    valid_days = sum(row["day_status"] == "COMPLETE" and bool(row["first_stable_time"]) for row in tushare_rows)
    evidence_class = _evidence_class(tushare_rows, config)
    cross_day = _cross_day_statistics(tushare_rows, config)
    timing_rows = []
    for row in tushare_rows:
        timing_rows.append({
            "trade_date": row["trade_date"],
            "day_status": row["day_status"],
            "tushare_slots_recorded": row["slots_recorded"],
            "tushare_slots_expected": row["slots_expected"],
            "first_available_time": row["first_available_time"],
            "first_complete_time": row["first_complete_time"],
            "first_quality_complete_time": row["first_quality_complete_time"],
            "first_stable_time": row["first_stable_time"],
            "last_revision_time": row["last_revision_time"],
            "late_revision_risk": row["late_revision_risk"],
            "sh_first_complete_time": row["sh_first_complete_time"],
            "sz_first_complete_time": row["sz_first_complete_time"],
            "delayed_codes": row["delayed_codes"],
            "max_coverage_ratio": row["max_coverage_ratio"],
            "revision_count": row["revision_count"],
            "evidence_class": evidence_class,
        })
    pd.DataFrame(timing_rows, columns=TIMING_COLUMNS).to_csv(paths.timing_summary, index=False, lineterminator="\n")

    comparison_rows: list[dict[str, Any]] = []
    for trade_date in dates:
        source_rows = {}
        for source, times in (("tushare", config["schedule"]["tushare_times"]), ("baostock", config["schedule"]["baostock_times"])):
            source_rows[source] = summarize_source_day(
                manifests,
                source=source,
                trade_date=trade_date,
                expected_times=list(times),
                stability_minutes=int(config["observation"]["stability_min_interval_minutes"]),
                late_revision_threshold=str(config["observation"]["late_revision_threshold"]),
            )
        base_minutes = _minutes(source_rows["tushare"]["first_complete_time"])
        for source, row in source_rows.items():
            source_minutes = _minutes(row["first_complete_time"])
            delta = "" if source == "tushare" or base_minutes is None or source_minutes is None else source_minutes - base_minutes
            comparison_rows.append({
                "trade_date": trade_date,
                "source": source,
                "day_status": row["day_status"],
                "first_available_time": row["first_available_time"],
                "first_complete_time": row["first_complete_time"],
                "first_stable_time": row["first_stable_time"],
                "max_coverage_ratio": row["max_coverage_ratio"],
                "error_statuses": row["error_statuses"],
                "later_than_tushare_minutes": delta,
            })
    pd.DataFrame(comparison_rows, columns=COMPARISON_COLUMNS).to_csv(paths.source_comparison, index=False, lineterminator="\n")

    payload = {
        "status": "ACTIVE_COLLECTING",
        "observation_days_started": len(dates),
        "observation_days_completed": complete_days,
        "valid_observation_days": valid_days,
        "evidence_class": evidence_class,
        "tushare_rows": tushare_rows,
        "manifest_count": len(manifests),
        "cross_day_statistics": cross_day,
    }
    paths.status_report.write_text(_status_markdown(payload, config), encoding="utf-8")
    return payload


def _first_stable_time(rows: list[dict[str, Any]], minimum_interval: int) -> str:
    ordered = sorted(rows, key=lambda row: str(row.get("scheduled_at", "")))
    for index, row in enumerate(ordered[:-1]):
        if not _is_complete(row):
            continue
        current_time = _minutes(_hhmm(row.get("scheduled_at", "")))
        later = ordered[index + 1:]
        next_row = later[0]
        next_time = _minutes(_hhmm(next_row.get("scheduled_at", "")))
        if current_time is None or next_time is None or next_time - current_time < minimum_interval:
            continue
        expected_hash = str(row.get("source_snapshot_hash", ""))
        if expected_hash and all(_is_complete(item) and str(item.get("source_snapshot_hash", "")) == expected_hash for item in later):
            return _hhmm(row.get("scheduled_at", ""))
    return ""


def _delayed_codes(rows: list[dict[str, Any]]) -> list[str]:
    complete_index = next((index for index, row in enumerate(rows) if _is_complete(row)), None)
    if complete_index is None:
        return sorted({code for row in rows for code in row.get("missing_codes", [])})
    return sorted({code for row in rows[:complete_index] for code in row.get("missing_codes", [])})


def _is_complete(row: dict[str, Any]) -> bool:
    return (
        float(row.get("coverage_ratio", 0)) >= 1.0
        and not row.get("duplicate_codes")
        and int(row.get("critical_field_error_count", 0)) == 0
    )


def _is_quality_complete(row: dict[str, Any]) -> bool:
    return _is_complete(row) and bool(row.get("field_complete")) and bool(row.get("quality_complete"))


def _evidence_class(rows: list[dict[str, Any]], config: dict[str, Any]) -> str:
    completed = [row for row in rows if row["day_status"] == "COMPLETE"]
    valid = [row for row in completed if row["first_stable_time"]]
    valid_days = len(valid)
    if valid_days >= int(config["observation"]["supported_min_valid_days"]):
        return "SUPPORTED_CANDIDATE_MAIN_REVIEW_REQUIRED"
    if len(completed) >= int(config["observation"]["preliminary_min_valid_days"]):
        if len(valid) < len(completed) or any(row["late_revision_risk"] for row in completed):
            return "EXTEND_TO_10_DAYS"
        return "PRELIMINARY_PASS_MAIN_REVIEW_REQUIRED"
    return "COLLECTING_INSUFFICIENT_DAYS"


def _cross_day_statistics(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    completed = [row for row in rows if row["day_status"] == "COMPLETE"]
    required = int(config["observation"]["preliminary_min_valid_days"])
    result: dict[str, Any] = {
        "status": "NOT_ISSUED_INSUFFICIENT_DAYS",
        "sample_days": len(completed),
        "first_available": _timing_stats([row["first_available_time"] for row in completed]),
        "first_complete": _timing_stats([row["first_complete_time"] for row in completed]),
        "first_stable": _timing_stats([row["first_stable_time"] for row in completed]),
        "recommended_first_probe_time": "",
        "recommended_retry_interval_minutes": int(config["observation"]["stability_min_interval_minutes"]),
        "recommended_safety_cutoff": str(config["schedule"]["tushare_times"][-1]),
        "maximum_retry_count": 0,
        "data_not_ready_rule": "No recommendation before five completed valid trading days.",
        "paper_execution_rule": "No change; the existing freshness gate remains authoritative.",
    }
    stable_p90 = result["first_stable"]["p90"]
    if len(completed) < required or not stable_p90:
        return result
    buffer_minutes = int(config["observation"]["safety_buffer_minutes"])
    recommended_minutes = min(_minutes(stable_p90) + buffer_minutes, 24 * 60 - 1)
    cutoff_minutes = _minutes(result["recommended_safety_cutoff"])
    retry_interval = result["recommended_retry_interval_minutes"]
    result.update({
        "status": "PRELIMINARY" if len(completed) < int(config["observation"]["supported_min_valid_days"]) else "SUPPORTED_CANDIDATE_MAIN_REVIEW_REQUIRED",
        "recommended_first_probe_time": _format_minutes(recommended_minutes),
        "maximum_retry_count": max(0, (cutoff_minutes - recommended_minutes) // retry_interval) if cutoff_minutes is not None else 0,
        "data_not_ready_rule": "Emit DATA_NOT_READY when no quality-complete stable snapshot exists by the safety cutoff; do not fall back to an earlier trade date.",
        "paper_execution_rule": "Keep paper execution blocked unless the independent freshness gate passes for the expected trade date.",
    })
    return result


def _timing_stats(values: list[str]) -> dict[str, str]:
    minutes = sorted(value for value in (_minutes(item) for item in values) if value is not None)
    if not minutes:
        return {"p50": "", "p90": "", "worst": ""}
    return {
        "p50": _format_minutes(_nearest_rank(minutes, 0.50)),
        "p90": _format_minutes(_nearest_rank(minutes, 0.90)),
        "worst": _format_minutes(max(minutes)),
    }


def _nearest_rank(values: list[int], percentile: float) -> int:
    index = max(0, int((len(values) * percentile + 0.999999999) // 1) - 1)
    return values[min(index, len(values) - 1)]


def _status_markdown(payload: dict[str, Any], config: dict[str, Any]) -> str:
    generated = datetime.now(TZ).isoformat(timespec="seconds")
    rows = payload["tushare_rows"]
    lines = [
        "# Tushare ETF Daily Availability Timing Audit Status",
        "",
        f"- Generated at: `{generated}`",
        "- Audit status: `ACTIVE_COLLECTING`",
        f"- Observation days started: `{payload['observation_days_started']}`",
        f"- Observation days completed: `{payload['observation_days_completed']}`",
        f"- Valid stable observation days: `{payload['valid_observation_days']}`",
        f"- Timing evidence: `{payload['evidence_class']}`",
        "- Tushare role: `SHADOW_PRIMARY_CANDIDATE`",
        "- BaoStock role: `COMPARATOR_ONLY`",
        "- Canonical ETF data: `data/etf_daily/` (unchanged)",
        "- Primary upstream migration: `NOT_STARTED`",
        "- Formal execution logic: `UNCHANGED`",
        "",
        "## Schedule",
        "",
        f"- Tushare: `{', '.join(config['schedule']['tushare_times'])}` CST",
        f"- BaoStock: `{', '.join(config['schedule']['baostock_times'])}` CST",
        "- A trading day is accepted only when confirmed by the cached Tushare trade calendar.",
        "",
        "## Daily Progress",
        "",
        "| Trade date | Status | Slots | First available | First complete | First stable | Last revision |",
        "|---|---|---:|---|---|---|---|",
    ]
    if rows:
        for row in rows:
            lines.append(
                f"| {row['trade_date']} | {row['day_status']} | {row['slots_recorded']}/{row['slots_expected']} | "
                f"{row['first_available_time'] or '-'} | {row['first_complete_time'] or '-'} | "
                f"{row['first_stable_time'] or '-'} | {row['last_revision_time'] or '-'} |"
            )
    else:
        lines.append("| - | Waiting for first real probe | 0/10 | - | - | - | - |")
    lines.extend([
        "",
        "## Cross-Day Statistics And Safety Candidate",
        "",
        f"- Statistics status: `{payload['cross_day_statistics']['status']}`",
        f"- FIRST_AVAILABLE P50 / P90 / worst: `{_stats_text(payload['cross_day_statistics']['first_available'])}`",
        f"- FIRST_COMPLETE P50 / P90 / worst: `{_stats_text(payload['cross_day_statistics']['first_complete'])}`",
        f"- FIRST_STABLE P50 / P90 / worst: `{_stats_text(payload['cross_day_statistics']['first_stable'])}`",
        f"- Candidate first probe time: `{payload['cross_day_statistics']['recommended_first_probe_time'] or 'NOT_ISSUED'}`",
        f"- Candidate retry interval: `{payload['cross_day_statistics']['recommended_retry_interval_minutes']} minutes`",
        f"- Candidate safety cutoff: `{payload['cross_day_statistics']['recommended_safety_cutoff']}`",
        f"- Candidate maximum retries: `{payload['cross_day_statistics']['maximum_retry_count']}`",
        f"- DATA_NOT_READY rule: {payload['cross_day_statistics']['data_not_ready_rule']}",
        f"- Paper execution rule: {payload['cross_day_statistics']['paper_execution_rule']}",
        "",
        "## Decision Boundary",
        "",
        "No safety-time or primary-source recommendation is issued before five valid days. Five-day evidence is preliminary; ten valid trading days are required before a supported timing verdict can be proposed to Main.",
        "",
    ])
    return "\n".join(lines)


def _hhmm(value: Any) -> str:
    text = str(value or "")
    try:
        return datetime.fromisoformat(text).strftime("%H:%M")
    except ValueError:
        return text[:5] if len(text) >= 5 and text[2:3] == ":" else ""


def _minutes(value: str) -> int | None:
    if not value:
        return None
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def _format_minutes(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


def _stats_text(stats: dict[str, str]) -> str:
    return f"{stats['p50'] or '-'} / {stats['p90'] or '-'} / {stats['worst'] or '-'}"
