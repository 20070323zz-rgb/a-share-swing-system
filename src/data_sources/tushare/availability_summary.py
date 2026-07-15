"""Build committed, sanitized summaries from local append-only timing evidence."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from .availability_models import AuditPaths, active_tushare_times, schedule_times


TZ = ZoneInfo("Asia/Shanghai")
REAL_RESPONSE_STATUSES = {"ACCESS_PASS", "EMPTY_UNEXPECTED", "NETWORK_FAILED", "PERMISSION_BLOCKED", "VALIDATION_FAILED"}
COMPLETED_SLOT_STATUSES = REAL_RESPONSE_STATUSES | {"SKIPPED_STABLE_CONFIRMED"}
TIMING_COLUMNS = [
    "trade_date", "day_status", "tushare_slots_recorded", "tushare_slots_expected",
    "first_available_time", "first_complete_time", "first_quality_complete_time",
    "first_stable_time", "availability_state", "data_readiness_status",
    "last_revision_time", "late_revision_risk",
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
    late_revision_threshold: str,
) -> dict[str, Any]:
    eligible_times = set(expected_times)
    attempts = [
        item for item in manifests
        if item.get("source") == source
        and item.get("trade_date") == trade_date
        and item.get("evidence_mode") == "real"
        and item.get("response_status") not in {"DUPLICATE_ATTEMPT_SKIPPED", "BLOCKED_EARLY_PROBE"}
        and _hhmm(item.get("scheduled_at", "")) in eligible_times
    ]
    latest_by_probe: dict[str, dict[str, Any]] = {}
    for item in sorted(attempts, key=lambda row: str(row.get("completed_at", ""))):
        latest_by_probe[str(item.get("probe_id", ""))] = item
    rows = sorted(latest_by_probe.values(), key=lambda row: str(row.get("scheduled_at", "")))
    observed_times = {_hhmm(row.get("scheduled_at", "")) for row in rows}
    recorded = len(set(expected_times) & observed_times)
    all_slots_recorded = recorded == len(expected_times)
    completed_slots = [row for row in rows if row.get("response_status") in COMPLETED_SLOT_STATUSES]
    real_slots = [row for row in rows if row.get("response_status") in REAL_RESPONSE_STATUSES]
    day_status = "COMPLETE" if all_slots_recorded and len(completed_slots) == len(expected_times) else "IN_PROGRESS"
    if all_slots_recorded and len(completed_slots) < len(expected_times):
        day_status = "INCOMPLETE_WITH_MISSED_PROBES"

    available = [row for row in real_slots if int(row.get("matched_etf_count", 0)) > 0]
    complete = [row for row in real_slots if _is_complete(row)]
    quality_complete = [row for row in real_slots if _is_quality_complete(row)]
    first_available = min((_hhmm(row.get("scheduled_at", "")) for row in available), default="")
    first_complete = min((_hhmm(row.get("scheduled_at", "")) for row in complete), default="")
    stable = _first_stable_time(real_slots)
    availability_state = _observation_state(real_slots)
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
        "availability_state": availability_state,
        "data_readiness_status": "SHADOW_STABLE" if availability_state == "STABLE" else "DATA_NOT_READY",
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
            expected_times=schedule_times(config, "tushare", trade_date),
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
            "availability_state": row["availability_state"],
            "data_readiness_status": row["data_readiness_status"],
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
        for source in ("tushare", "baostock"):
            source_rows[source] = summarize_source_day(
                manifests,
                source=source,
                trade_date=trade_date,
                expected_times=schedule_times(config, source, trade_date),
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


def _first_stable_time(rows: list[dict[str, Any]]) -> str:
    """Return the confirmation slot, invalidating it after any later change/failure."""
    ordered = sorted(rows, key=lambda row: str(row.get("scheduled_at", "")))
    candidate = ""
    previous: dict[str, Any] | None = None
    for row in ordered:
        if not _is_quality_complete(row):
            candidate = ""
            previous = row
            continue
        current_hash = str(row.get("source_snapshot_hash", ""))
        if previous is not None and _is_quality_complete(previous):
            previous_hash = str(previous.get("source_snapshot_hash", ""))
            if current_hash and current_hash == previous_hash:
                if not candidate:
                    candidate = _hhmm(row.get("scheduled_at", ""))
            else:
                candidate = ""
        else:
            candidate = ""
        previous = row
    return candidate


def _observation_state(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "NOT_AVAILABLE"
    ordered = sorted(rows, key=lambda row: str(row.get("scheduled_at", "")))
    latest = ordered[-1]
    if latest.get("response_status") != "ACCESS_PASS":
        return "NOT_AVAILABLE" if int(latest.get("matched_etf_count", 0)) == 0 else "PARTIAL"
    if int(latest.get("matched_etf_count", 0)) == 0:
        return "NOT_AVAILABLE"
    if not _is_quality_complete(latest):
        return "PARTIAL"
    if len(ordered) < 2 or not _is_quality_complete(ordered[-2]):
        return "COMPLETE_UNCONFIRMED"
    latest_hash = str(latest.get("source_snapshot_hash", ""))
    previous_hash = str(ordered[-2].get("source_snapshot_hash", ""))
    return "STABLE" if latest_hash and latest_hash == previous_hash else "REVISION_DETECTED"


def _delayed_codes(rows: list[dict[str, Any]]) -> list[str]:
    first_available_index = next((index for index, row in enumerate(rows) if int(row.get("matched_etf_count", 0)) > 0), None)
    if first_available_index is None:
        return []
    complete_index = next((index for index, row in enumerate(rows) if _is_complete(row)), None)
    if complete_index is None:
        return sorted({code for row in rows[first_available_index:] for code in row.get("missing_codes", [])})
    return sorted({code for row in rows[first_available_index:complete_index] for code in row.get("missing_codes", [])})


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
    return "INSUFFICIENT_FOR_FIVE_DAY_STABILITY_CERTIFICATION"


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
        "recommended_retry_interval_minutes": int(config["observation"]["candidate_retry_interval_minutes"]),
        "recommended_safety_cutoff": str(active_tushare_times(config)[-1]),
        "maximum_retry_count": 0,
        "data_not_ready_rule": "At 18:00, emit DATA_NOT_READY if no current field-quality-complete stable pair exists; preserve the existing SSOT and do not invoke BaoStock fallback. No timing recommendation is issued before five completed valid trading days.",
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
        "- Tushare role: `APPROVED_PRIMARY_UPSTREAM`",
        "- Decision evidence confidence: `LIMITED_TWO_DAY_EVIDENCE`",
        "- Decision authority: `USER_AUTHORIZED_EARLY_PROMOTION`",
        "- BaoStock role: `RECONCILIATION_ONLY`",
        "- Canonical ETF data: `data/etf_daily/` (unchanged)",
        "- Primary upstream migration: `AUTHORIZED_NOT_STARTED`",
        "- Data promotion: `BLOCKED_PENDING_IMPLEMENTATION_VALIDATION`",
        "- Formal execution logic: `UNCHANGED`",
        "",
        "## Schedule",
        "",
        f"- Core Tushare: `{', '.join(config['schedule']['core_times'])}` CST",
        f"- Conditional Tushare: `{', '.join(config['schedule']['conditional_times'])}` CST",
        f"- Low-frequency health check (excluded from timing): `{', '.join(config['schedule']['health_check_times'])}` CST",
        f"- BaoStock: `{', '.join(config['schedule']['baostock_times'])}` CST",
        "- A trading day is accepted only when confirmed by the cached Tushare trade calendar.",
        "",
        "## Daily Progress",
        "",
        "| Trade date | Status | Observation state | Slots | First available | First complete | First stable | Last revision |",
        "|---|---|---|---:|---|---|---|---|",
    ]
    if rows:
        for row in rows:
            lines.append(
                f"| {row['trade_date']} | {row['day_status']} | {row['availability_state']} | {row['slots_recorded']}/{row['slots_expected']} | "
                f"{row['first_available_time'] or '-'} | {row['first_complete_time'] or '-'} | "
                f"{row['first_stable_time'] or '-'} | {row['last_revision_time'] or '-'} |"
            )
    else:
        lines.append("| - | Waiting for first real probe | NOT_AVAILABLE | 0/8 | - | - | - | - |")
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
        "## Migration Timing Design Candidate",
        "",
        f"- First formal staging fetch candidate: `{config['migration_timing_candidate']['first_formal_staging_fetch']}`",
        f"- Confirmation / validation / atomic-promotion candidate: `{config['migration_timing_candidate']['confirmation_validation_atomic_promotion_candidate']}`",
        f"- Fail-closed manual-review cutoff: `{config['migration_timing_candidate']['fail_closed_manual_review_cutoff']}`",
        "- Formal promotion authorized: `false`",
        "",
        "## Decision Boundary",
        "",
        "Tushare adoption is already approved by user authorization. Five-day and ten-day evidence gates now govern only timing-window optimization and safety-buffer certification; they do not reopen the upstream-source decision. Formal promotion remains blocked until migration implementation and validation pass.",
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
