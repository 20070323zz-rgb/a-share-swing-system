from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from .common import RunContext, path_is_within, posix_relative, read_text_lossy, sha256_file, stable_id


DATE_PATTERN = re.compile(r"(?<!\d)(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)(?!\d)")
CONTENT_DATE_PATTERN = re.compile(
    r"(?im)(?:business_date|as_of_date|trade_date|report_date|audited_at|generated_at|检查时间|生成时间)"
    r"[^\n\d]{0,24}(20\d{2}-[01]\d-[0-3]\d)"
)
CONTROL_ARTIFACT_PATTERN = re.compile(
    r'(?im)(?:^|["{,]\s*)artifact_type["\s:]+' r'(?:["\s]*)GOVERNANCE_CONTROL(?:["\s,}]*)'
)


def _valid_date(match: re.Match[str]) -> str | None:
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()
    except ValueError:
        return None


def infer_business_date(path: Path) -> tuple[str | None, bool]:
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".txt", ".yaml", ".yml", ".csv"}:
        content = read_text_lossy(path, limit=131072)
        match = CONTENT_DATE_PATTERN.search(content)
        if match:
            try:
                return date.fromisoformat(match.group(1)).isoformat(), True
            except ValueError:
                pass
    for match in DATE_PATTERN.finditer(path.name):
        value = _valid_date(match)
        if value:
            return value, False
    return None, False


def is_governance_control_artifact(path: Path) -> bool:
    if path.suffix.lower() not in {".md", ".json", ".jsonl", ".txt", ".yaml", ".yml"}:
        return False
    return bool(CONTROL_ARTIFACT_PATTERN.search(read_text_lossy(path, limit=8192)))


def infer_role(relative_path: str, extension: str, context: RunContext) -> str:
    lower = relative_path.lower()
    name = Path(relative_path).name.lower()
    if path_is_within(relative_path, context.config["archive_roots"]):
        return "ARCHIVED_ARTIFACT"
    if relative_path in context.config["formal_execution_inputs"]:
        return "FORMAL_EXECUTION_INPUT"
    if relative_path in context.config["app_dashboard_entrypoints"]:
        return "APP_DASHBOARD_ENTRYPOINT"
    if any(relative_path.startswith(prefix) for prefix in context.config["availability_active_prefixes"]):
        return "AVAILABILITY_ACTIVE_ARTIFACT"
    if any(token in name for token in ("latest", "current")):
        return "CURRENT_ALIAS"
    if "decision" in name or "verdict" in name:
        return "DECISION"
    if "audit" in name:
        return "AUDIT_EVIDENCE"
    if "status" in name or "preflight" in name or "manifest" in name:
        return "RUNTIME_STATUS"
    if extension in {".csv", ".parquet", ".json", ".jsonl"}:
        return "REPORT_DATASET"
    if extension in {".md", ".html", ".txt"}:
        return "HUMAN_REPORT"
    return "UNKNOWN"


def infer_naming_status(relative_path: str, business_date: str | None, context: RunContext) -> str:
    stem = Path(relative_path).stem.lower()
    if any(token in stem.split("_") for token in context.config["current_alias_tokens"]):
        return "CURRENT_ALIAS"
    if any(_valid_date(match) for match in DATE_PATTERN.finditer(Path(relative_path).name)):
        return "COMPLIANT_DATED"
    return "NEEDS_DATE_NORMALIZATION" if business_date is not None else "UNDATED_STABLE_NAME"


def infer_retention(role: str, business_date: str | None) -> str:
    if role == "ARCHIVED_ARTIFACT":
        return "PERMANENT_ARCHIVE"
    if role in {"FORMAL_EXECUTION_INPUT", "APP_DASHBOARD_ENTRYPOINT", "AVAILABILITY_ACTIVE_ARTIFACT", "CURRENT_ALIAS", "RUNTIME_STATUS"}:
        return "ACTIVE_PROJECT_LIFETIME"
    if business_date:
        return "HISTORICAL_SNAPSHOT"
    return "MANUAL_REVIEW"


def infer_location(relative_path: str, context: RunContext) -> str:
    if path_is_within(relative_path, context.config["archive_roots"]):
        return "ALREADY_ARCHIVED"
    if path_is_within(relative_path, context.config["governance_control_roots"]):
        return "GOVERNANCE_CONTROL"
    return "REPORTS_ROOT" if len(Path(relative_path).parts) == 2 else "REPORTS_NESTED"


def build_inventory(context: RunContext) -> list[dict[str, Any]]:
    extensions = set(context.config["allowed_report_extensions"])
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for root_name in context.config["report_roots"]:
        report_root = context.root / root_name
        for path in sorted(report_root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in extensions:
                continue
            relative_path = posix_relative(path, context.root)
            if path_is_within(relative_path, context.config["governance_control_roots"]):
                continue
            if is_governance_control_artifact(path):
                continue
            report_id = stable_id("report", relative_path)
            if report_id in seen_ids:
                raise ValueError(f"duplicate report_id: {report_id}")
            seen_ids.add(report_id)
            business_date, created_from_content = infer_business_date(path)
            role = infer_role(relative_path, path.suffix.lower(), context)
            records.append(
                {
                    "report_id": report_id,
                    "relative_path": relative_path,
                    "filename": path.name,
                    "extension": path.suffix.lower(),
                    "size": path.stat().st_size,
                    "content_sha256": sha256_file(path),
                    "business_date": business_date,
                    "created_from_content": created_from_content,
                    "role": role,
                    "naming_status": infer_naming_status(relative_path, business_date, context),
                    "retention_status": infer_retention(role, business_date),
                    "location_status": infer_location(relative_path, context),
                    "schema_version": "report-inventory-record-v1",
                    "catalog_version": context.config["catalog_version"],
                }
            )
    return records
