"""Shared deterministic helpers for Reports Governance Phase A.

The helpers in this module are inventory-only. They never move, rename, delete,
or rewrite an existing report and they do not read credentials or runtime data
outside tracked/report metadata needed for classification.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import date as calendar_date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Sequence
from zoneinfo import ZoneInfo

try:
    from scripts.governance.dependency_classifier import (
        GENERATOR_VERSION,
        classify_source_text,
        extract_report_references as structured_extract_report_references,
    )
except ModuleNotFoundError:  # Direct script execution.
    from dependency_classifier import (  # type: ignore
        GENERATOR_VERSION,
        classify_source_text,
        extract_report_references as structured_extract_report_references,
    )


ROLE_VALUES = (
    "RUNTIME_INPUT",
    "CURRENT_ALIAS",
    "DATED_DAILY",
    "DATED_WEEKLY",
    "DATED_MONTHLY",
    "RESEARCH_ARTIFACT",
    "AUDIT_ARTIFACT",
    "GOVERNANCE_ARTIFACT",
    "VALIDATION_ARTIFACT",
    "GENERATED_SNAPSHOT",
    "ARCHIVED_ARTIFACT",
    "UNKNOWN",
)

MIGRATION_RISK_VALUES = (
    "RUNTIME_LOCKED",
    "HIGH_DEPENDENCY",
    "ACTIVE_REFERENCED",
    "MEDIUM_DEPENDENCY",
    "LOW_RISK_ARCHIVE_CANDIDATE",
    "UNKNOWN_REQUIRES_REVIEW",
)

REFERENCE_TYPE_VALUES = (
    "PRODUCER_WRITE",
    "CONSUMER_READ",
    "FILE_COPY_SOURCE",
    "FILE_MOVE_SOURCE",
    "APP_RUNTIME_READ",
    "DASHBOARD_RUNTIME_READ",
    "TEST_REFERENCE",
    "DOCUMENTATION_LINK",
    "STATIC_LINK",
    "EXAMPLE_REFERENCE",
    "HISTORICAL_REFERENCE",
    "STATE_INDEX_REFERENCE",
    "DYNAMIC_PATH_PATTERN",
    "PATH_DECLARATION",
    "UNKNOWN_REFERENCE",
)

CONTROL_REPORT_PATHS = {
    "reports/report_catalog.csv",
    "reports/report_catalog.json",
    "reports/report_catalog.md",
    "reports/report_dependency_registry.csv",
    "reports/report_dependency_registry.json",
    "reports/report_dependency_registry.md",
    "reports/reports_governance_phase_a_summary.md",
}

CONTROL_REPORT_RE = re.compile(
    r"^reports/(?:"
    r"report_catalog_(?:v\d+_)?20\d{2}-\d{2}-\d{2}\.(?:csv|json|md)|"
    r"report_dependency_registry_(?:v\d+_)?20\d{2}-\d{2}-\d{2}\.(?:csv|json)|"
    r"report_dependency_summary_(?:v\d+_)?20\d{2}-\d{2}-\d{2}\.md|"
    r"report_governance_evidence_registry_(?:v\d+_)?20\d{2}-\d{2}-\d{2}\.(?:csv|json)|"
    r"report_naming_compliance_audit_(?:v\d+_)?20\d{2}-\d{2}-\d{2}\.(?:csv|metadata\.json)|"
    r"reports_governance_phase_a_(?:summary|remediation|final_blocker_remediation|dynamic_producer_remediation|final_semantic_remediation|evidence_and_archive_state_remediation)_(?:v\d+_)?20\d{2}-\d{2}-\d{2}\.md"
    r")$"
)

DEFAULT_ARCHIVE_ROOTS = ("reports/archive/",)
CLASSIFICATION_SCHEMA_VERSION = 3
EVIDENCE_REGISTRY_VERSION = "v1"

LOCATION_STATUS_VALUES = (
    "ACTIVE_ROOT",
    "ACTIVE_SUBDIRECTORY",
    "ALREADY_ARCHIVED",
    "TEMPORARY_STAGING",
    "RUNTIME_ALIAS_LOCATION",
    "GOVERNANCE_CONTROL_LOCATION",
    "UNKNOWN_LOCATION",
)

RUNTIME_LOCKED_PATHS = {
    "reports/dashboard_data.json",
    "reports/paper_performance_summary.json",
    "reports/paper_performance_summary.md",
    "reports/portfolio_exposure.json",
    "reports/position_review_state.json",
    "reports/profit_protection_preview.json",
    "reports/high_beta_risk_watch.json",
    "reports/broad_base_balance_preview.json",
    "reports/chatgpt_weekly_analysis_packet_latest.json",
    "reports/chatgpt_weekly_analysis_packet_latest.md",
    "reports/paper_execution_preflight.json",
    "reports/paper_execution_preflight.md",
}

STABLE_ALIAS_NAMES = {
    "dashboard_data.json",
    "buy_signal_ranking.md",
    "sell_signal_review.md",
    "paper_performance_summary.json",
    "paper_performance_summary.md",
    "portfolio_exposure.json",
    "portfolio_exposure.md",
    "position_review_state.json",
    "position_review_state.md",
    "profit_protection_preview.json",
    "profit_protection_preview.md",
    "high_beta_risk_watch.json",
    "high_beta_risk_watch.md",
    "broad_base_balance_preview.json",
    "broad_base_balance_preview.md",
    "chatgpt_weekly_analysis_packet_latest.json",
    "chatgpt_weekly_analysis_packet_latest.md",
}

TEXT_EXTENSIONS = {
    ".cjs",
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".plist",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

REPORT_EXTENSIONS = (".csv", ".html", ".json", ".md", ".txt", ".yaml", ".yml")
DATE_RE = re.compile(r"(?<!\d)(20\d{2}-\d{2}-\d{2})(?!\d)")
MONTH_RE = re.compile(r"(?<!\d)(20\d{2}-\d{2})(?!-\d{2})(?!\d)")
TERMINAL_DATE_RE = re.compile(r"_20\d{2}-\d{2}-\d{2}$")
TERMINAL_MONTH_RE = re.compile(r"_20\d{2}-\d{2}$")
SNAKE_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
EXPLICIT_REPORT_RE = re.compile(r"(?<![A-Za-z0-9_.-])/?(reports/[A-Za-z0-9_./*?{}\[\]-]+)")
QUOTED_VALUE_RE = re.compile(r"[furbFURB]*[\"']([^\"']+)[\"']")
REPORT_DIR_MARKER_RE = re.compile(r"(?:REPORTS?_DIR|reports?_dir|Path\([\"']reports[\"']\))")
REPORT_DIR_SLASH_RE = re.compile(
    r"(?:REPORTS?_DIR|reports?_dir|Path\([\"']reports[\"']\))"
    r"(?P<tail>(?:\s*/\s*[furbFURB]*[\"'][^\"']+[\"'])+)"
)
REPORT_DIR_JOIN_RE = re.compile(
    r"(?:os\.path\.join|joinpath)\(\s*(?:REPORTS?_DIR|reports?_dir|Path\([\"']reports[\"']\))"
    r"\s*,(?P<tail>[^)]*)\)"
)
REPORT_DIR_METHOD_JOIN_RE = re.compile(
    r"(?:REPORTS?_DIR|reports?_dir)\.joinpath\((?P<tail>[^)]*)\)"
)
SHELL_REPORT_DIR_RE = re.compile(
    r"\$(?:\{)?REPORTS?_DIR(?:\})?/([^\"'\s]+(?:\.csv|\.html|\.json|\.md|\.txt|\.yaml|\.yml))"
)
BUSINESS_DATE_LINE_RE = re.compile(
    r"(?:business_date|as_of_date|trade_date|data_date|业务日期|数据日期)\s*[:=：]\s*[`\"']?(20\d{2}-\d{2}-\d{2})",
    re.IGNORECASE,
)
WRITE_CUES = (
    "write_text(",
    "write_bytes(",
    "write_json(",
    "write_csv(",
    ".to_csv(",
    ".to_json(",
    "json.dump(",
    "writerow(",
    "writerows(",
    "lineterminator",
)
READ_CUES = (
    "read_text(",
    "read_bytes(",
    "read_csv(",
    "read_json(",
    "json.load(",
    "fetch(",
    "exists(",
)


def project_root_from_script(script_file: str) -> Path:
    return Path(script_file).resolve().parents[2]


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.absolute().relative_to(root.absolute()).as_posix()


def stable_report_id(current_path: str) -> str:
    digest = hashlib.sha256(current_path.encode("utf-8")).hexdigest()[:16]
    return f"report_{digest}"


def is_control_report_path(path: str) -> bool:
    return path in CONTROL_REPORT_PATHS or bool(CONTROL_REPORT_RE.fullmatch(path))


def normalize_governance_path(path: str) -> str:
    """Normalize a repository-relative governance path without resolving symlinks."""

    value = path.replace("\\", "/").lstrip("/")
    parts: list[str] = []
    for part in value.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def normalize_archive_roots(archive_roots: Sequence[str]) -> tuple[str, ...]:
    roots = []
    for root in archive_roots:
        normalized = normalize_governance_path(root).rstrip("/") + "/"
        if normalized == "/" or not normalized.startswith("reports/"):
            raise ValueError(f"archive root must be repository-relative under reports/: {root}")
        roots.append(normalized)
    if not roots:
        raise ValueError("at least one explicit archive root is required")
    return tuple(sorted(set(roots)))


def load_report_governance_config(root: Path) -> dict:
    path = root / "configs/report_governance.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["archive_roots"] = list(
        normalize_archive_roots(payload.get("archive_roots", DEFAULT_ARCHIVE_ROOTS))
    )
    return payload


def classify_location_status(
    path: str,
    archive_roots: Sequence[str] = DEFAULT_ARCHIVE_ROOTS,
    *,
    is_symlink: bool = False,
) -> str:
    normalized = normalize_governance_path(path)
    roots = normalize_archive_roots(archive_roots)
    if any(normalized.startswith(root) for root in roots):
        return "ALREADY_ARCHIVED"
    if is_control_report_path(normalized):
        return "GOVERNANCE_CONTROL_LOCATION"
    if is_symlink or is_current_alias(normalized):
        return "RUNTIME_ALIAS_LOCATION"
    if normalized.startswith(("reports/staging/", "reports/tmp/", "reports/temporary/")):
        return "TEMPORARY_STAGING"
    if normalized.startswith("reports/"):
        remainder = normalized.removeprefix("reports/")
        return "ACTIVE_SUBDIRECTORY" if "/" in remainder else "ACTIVE_ROOT"
    return "UNKNOWN_LOCATION"


def business_date_today() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()


def superseded_artifact(root: Path, business_date: str, path_template: str) -> str:
    """Return the immediately prior dated artifact when it exists."""

    try:
        previous = (calendar_date.fromisoformat(business_date) - timedelta(days=1)).isoformat()
    except ValueError:
        return ""
    candidate = path_template.format(date=previous)
    return candidate if (root / candidate).exists() else ""


def revisioned_artifact_path(base: str, business_date: str, extension: str, revision: str) -> str:
    revision_token = f"_{revision}" if revision else ""
    return f"reports/{base}{revision_token}_{business_date}.{extension}"


def superseded_revision_artifact(
    root: Path,
    base: str,
    business_date: str,
    extension: str,
    revision: str,
) -> str:
    if not revision:
        return superseded_artifact(
            root, business_date, f"reports/{base}_{{date}}.{extension}"
        )
    previous_revision = "" if revision in {"v1", "v2"} else f"v{int(revision[1:]) - 1}"
    candidate = revisioned_artifact_path(base, business_date, extension, previous_revision)
    return candidate if (root / candidate).exists() else ""


def source_tree_commit(root: Path) -> str:
    """Return the latest commit affecting inputs, excluding generated control outputs."""

    command = [
        "git",
        "log",
        "-1",
        "--format=%H",
        "--",
        ".",
        ":(exclude)reports/report_catalog.csv",
        ":(exclude)reports/report_catalog.json",
        ":(exclude)reports/report_catalog.md",
        ":(exclude,glob)reports/report_catalog_*.csv",
        ":(exclude,glob)reports/report_catalog_*.json",
        ":(exclude,glob)reports/report_catalog_*.md",
        ":(exclude)reports/report_dependency_registry.csv",
        ":(exclude)reports/report_dependency_registry.json",
        ":(exclude)reports/report_dependency_registry.md",
        ":(exclude,glob)reports/report_dependency_registry_*.csv",
        ":(exclude,glob)reports/report_dependency_registry_*.json",
        ":(exclude,glob)reports/report_dependency_summary_*.md",
        ":(exclude,glob)reports/report_governance_evidence_registry_*.csv",
        ":(exclude,glob)reports/report_governance_evidence_registry_*.json",
        ":(exclude,glob)reports/report_naming_compliance_audit_*",
        ":(exclude)reports/reports_governance_phase_a_summary.md",
        ":(exclude,glob)reports/reports_governance_phase_a_summary_*.md",
        ":(exclude,glob)reports/reports_governance_phase_a_remediation_*.md",
        ":(exclude,glob)reports/reports_governance_phase_a_final_blocker_remediation_*.md",
        ":(exclude,glob)reports/reports_governance_phase_a_dynamic_producer_remediation_*.md",
        ":(exclude,glob)reports/reports_governance_phase_a_final_semantic_remediation_*.md",
        ":(exclude,glob)reports/reports_governance_phase_a_evidence_and_archive_state_remediation_*.md",
    ]
    value = subprocess.run(command, cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    return value or subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def deterministic_created_at(root: Path, commit: str) -> str:
    raw = subprocess.run(
        ["git", "show", "-s", "--format=%cI", commit],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return datetime.fromisoformat(raw).astimezone(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")


def artifact_metadata(
    root: Path,
    business_date: str,
    report_id: str,
    record_count: int,
    supersedes: str | None = None,
    snapshot_revision: str = "",
) -> dict:
    commit = source_tree_commit(root)
    metadata = {
        "report_id": report_id,
        "business_date": business_date,
        "generated_at": deterministic_created_at(root, commit),
        "generator_version": GENERATOR_VERSION,
        "source_tree_commit": commit,
        "record_count": record_count,
        "schema_version": CLASSIFICATION_SCHEMA_VERSION,
        "snapshot_revision": snapshot_revision or "v1",
        "immutable": True,
        "evidence_registry_version": EVIDENCE_REGISTRY_VERSION,
        "classification_schema_version": CLASSIFICATION_SCHEMA_VERSION,
    }
    if supersedes:
        metadata["supersedes"] = supersedes
    return metadata


def markdown_front_matter(
    *,
    report_id: str,
    report_type: str,
    business_date: str,
    created_at: str,
    status: str,
    producer: str,
    source_run_id: str,
    retention_class: str = "PERMANENT",
    supersedes: str = "",
    snapshot_revision: str = "v1",
    immutable: bool = True,
) -> str:
    lines = [
            "---",
            f"report_id: {report_id}",
            f"report_type: {report_type}",
            f"business_date: {business_date}",
            f"created_at: {created_at}",
            f"status: {status}",
            "phase: reports_governance_phase_a",
            f"producer: {producer}",
            f"source_run_id: {source_run_id}",
            f"retention_class: {retention_class}",
            f"schema_version: {CLASSIFICATION_SCHEMA_VERSION}",
            f"snapshot_revision: {snapshot_revision}",
            f"immutable: {'true' if immutable else 'false'}",
            f"evidence_registry_version: {EVIDENCE_REGISTRY_VERSION}",
            f"classification_schema_version: {CLASSIFICATION_SCHEMA_VERSION}",
    ]
    if supersedes:
        lines.append(f"supersedes: {supersedes}")
    lines.extend(("---", ""))
    return "\n".join(lines)


class ImmutableSnapshotError(RuntimeError):
    pass


def _write_immutable_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() == content:
            return
        raise ImmutableSnapshotError(
            f"immutable snapshot differs; create a new revision instead: {path}"
        )
    path.write_bytes(content)


def write_immutable_text(path: Path, content: str) -> None:
    _write_immutable_bytes(path, content.encode("utf-8"))


def write_json(path: Path, payload: object, *, immutable: bool = False) -> None:
    content = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if immutable:
        _write_immutable_bytes(path, content)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def write_csv(path: Path, rows: list[dict], fields: list[str], *, immutable: bool = False) -> None:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    content = handle.getvalue().encode("utf-8")
    if immutable:
        _write_immutable_bytes(path, content)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _git_file_list(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return sorted(item for item in result.stdout.decode("utf-8", errors="replace").split("\0") if item)


def _allowed_scan_path(path: str) -> bool:
    if path in {"PROJECT_INDEX.md", "Makefile"}:
        return True
    if "/node_modules/" in f"/{path}/" or path.startswith("app/frontend/dist/"):
        return False
    prefixes = (
        "app/backend/",
        "app/frontend/src/",
        "configs/",
        "dashboard/",
        "docs/",
        "launchd/",
        "reports/",
        "scripts/",
        "src/",
        "tests/",
    )
    if path.startswith(prefixes):
        return True
    return "/" not in path and Path(path).suffix.lower() in {".command", ".sh"}


def iter_repository_text_files(root: Path) -> Iterable[tuple[str, Path]]:
    for item in _git_file_list(root):
        if is_control_report_path(item) or not _allowed_scan_path(item):
            continue
        path = root / item
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS and path.name not in {"Makefile", "PROJECT_INDEX.md"}:
            continue
        yield item, path


def _clean_reference(raw: str) -> str:
    value = raw.lstrip("/").rstrip(".,;:)")
    while "//" in value:
        value = value.replace("//", "/")
    return value


def _is_dynamic(reference: str) -> bool:
    return any(token in reference for token in ("*", "?", "{", "}", "[", "]", "$"))


def extract_report_references(line: str) -> list[tuple[str, str]]:
    """Return (reference, resolution) without expanding dynamic patterns."""
    return structured_extract_report_references(line)


def _producer_line(line: str) -> bool:
    lowered = line.lower()
    if any(cue in lowered for cue in WRITE_CUES):
        return True
    if re.search(r"open\([^)]*,\s*[\"'][wa]", lowered):
        return True
    left = lowered.split("=", 1)[0] if "=" in lowered else ""
    if re.search(r"(?:output|destination|report_(?:path|file)|status_(?:json|md)|audit_(?:json|md))", left):
        return True
    if ">" in line and not any(token in line for token in (">=", "->", "=>")):
        return True
    return False


def classify_reference(source_file: str, line: str, resolution: str) -> tuple[str, str, str, str]:
    producer = _producer_line(line)
    dynamic = resolution == "DYNAMIC"
    if producer:
        reference_type = "DYNAMIC_PATH_PATTERN" if dynamic else "PRODUCER_WRITE"
        actor = "PRODUCER"
    elif dynamic:
        reference_type = "DYNAMIC_PATH_PATTERN"
        actor = "CONSUMER"
    elif source_file.startswith(("app/backend/", "app/frontend/")):
        reference_type = "APP_RUNTIME_READ"
        actor = "CONSUMER"
    elif source_file.startswith("dashboard/"):
        reference_type = "DASHBOARD_RUNTIME_READ"
        actor = "CONSUMER"
    elif source_file.startswith("tests/"):
        reference_type = "TEST_REFERENCE"
        actor = "CONSUMER"
    elif source_file in {"PROJECT_INDEX.md", "docs/current_project_state.md", "docs/current_phase_status.json"}:
        reference_type = "STATE_INDEX_REFERENCE"
        actor = "CONSUMER"
    elif source_file.endswith((".md", ".txt")) or source_file.startswith("reports/"):
        reference_type = "DOCUMENTATION_LINK"
        actor = "CONSUMER"
    elif any(cue in line.lower() for cue in READ_CUES):
        reference_type = "CONSUMER_READ"
        actor = "CONSUMER"
    elif source_file.endswith((".py", ".sh", ".js", ".jsx", ".ts", ".tsx")):
        reference_type = "CONSUMER_READ"
        actor = "CONSUMER"
    else:
        reference_type = "UNKNOWN_REFERENCE"
        actor = "UNKNOWN"

    if reference_type in {"APP_RUNTIME_READ", "DASHBOARD_RUNTIME_READ"}:
        impact = "CRITICAL"
    elif reference_type in {"PRODUCER_WRITE", "CONSUMER_READ"}:
        impact = "HIGH"
    elif reference_type in {"TEST_REFERENCE", "STATE_INDEX_REFERENCE", "DYNAMIC_PATH_PATTERN"}:
        impact = "MEDIUM"
    else:
        impact = "LOW"

    confidence = "HIGH" if resolution == "STATIC" else "MEDIUM" if resolution == "STATIC_COMPUTED" else "LOW"
    return reference_type, actor, confidence, impact


def scan_dependencies(root: Path) -> list[dict]:
    rows: list[dict] = []
    commit = source_tree_commit(root)
    for source_file, path in iter_repository_text_files(root):
        if source_file.startswith("scripts/governance/"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rows.extend(classify_source_text(source_file, text, commit))
    unique = {row["reference_id"]: row for row in rows}
    return sorted(
        unique.values(),
        key=lambda row: (
            row["normalized_target"],
            row["source_file"],
            row["source_line_start"],
            row["reference_type"],
            row["reference_id"],
        ),
    )


def dependency_payload(rows: list[dict], metadata: dict | None = None) -> dict:
    fingerprint = hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": CLASSIFICATION_SCHEMA_VERSION,
        "registry_id": "a_share_swing_system_report_dependency_registry_v3",
        "repository_root": "<project_root>",
        "metadata": metadata or {},
        "record_count": len(rows),
        "registry_sha256": fingerprint,
        "summary": {
            "by_reference_type": dict(sorted(Counter(row["reference_type"] for row in rows).items())),
            "by_migration_impact": dict(sorted(Counter(row["migration_impact"] for row in rows).items())),
            "dynamic_pattern_count": sum(row["static_or_dynamic"] == "DYNAMIC" for row in rows),
            "distinct_referenced_paths": len({row["referenced_report_path"] for row in rows}),
        },
        "records": rows,
    }


def render_dependency_markdown(payload: dict, front_matter: str = "") -> str:
    summary = payload["summary"]
    rows = payload["records"]
    type_lines = "\n".join(f"- `{key}`: {value}" for key, value in summary["by_reference_type"].items())
    impact_lines = "\n".join(f"- `{key}`: {value}" for key, value in summary["by_migration_impact"].items())
    high_rows = [row for row in rows if row["migration_impact"] in {"CRITICAL", "HIGH"}]
    table_lines = [
        "| Referenced report | Source | Line | Type | Impact |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in high_rows[:250]:
        table_lines.append(
            f"| `{row['referenced_report_path']}` | `{row['source_file']}` | {row['source_line']} | "
            f"`{row['reference_type']}` | `{row['migration_impact']}` |"
        )
    if not high_rows:
        table_lines.append("| - | - | - | - | - |")
    return f"""{front_matter}# Report Dependency Summary

本文件由 `scripts/governance/build_report_dependency_registry.py` 生成。扫描只读取可识别的静态/动态路径表达式；动态模式不会被伪造成具体文件依赖。

## Summary

- Registry records: {payload['record_count']}
- Distinct referenced paths/patterns: {summary['distinct_referenced_paths']}
- Dynamic patterns: {summary['dynamic_pattern_count']}
- Registry SHA-256: `{payload['registry_sha256']}`

### Reference types

{type_lines}

### Migration impact

{impact_lines}

## Critical and high-impact references

{chr(10).join(table_lines)}

完整逐行 Registry 见同业务日期的 CSV/JSON 机器产物。
"""


def git_report_dates(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    result = subprocess.run(
        ["git", "log", "--format=@@@%aI", "--name-only", "--", "reports"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    current_date = ""
    created: dict[str, str] = {}
    modified: dict[str, str] = {}
    for raw in result.stdout.splitlines():
        if raw.startswith("@@@"):
            current_date = raw[3:]
            continue
        path = raw.strip()
        if not current_date or not path.startswith("reports/"):
            continue
        modified.setdefault(path, current_date)
        created[path] = current_date[:10]
    return created, modified


def iter_report_paths(root: Path) -> list[Path]:
    report_dir = root / "reports"
    return sorted(
        (
            path
            for path in report_dir.rglob("*")
            if path.is_file() and not is_control_report_path(relative_path(root, path))
        ),
        key=lambda path: relative_path(root, path),
    )


def extract_business_date(path: Path) -> str:
    matches = DATE_RE.findall(path.stem)
    if len(set(matches)) == 1:
        return matches[0]
    month_matches = MONTH_RE.findall(path.stem)
    if not matches and len(set(month_matches)) == 1:
        return month_matches[0]

    if path.suffix.lower() == ".json" and path.stat().st_size <= 5_000_000:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, dict):
            for key in ("business_date", "as_of_date", "trade_date", "data_date", "calculation_date"):
                value = payload.get(key)
                if isinstance(value, str) and DATE_RE.fullmatch(value[:10]):
                    return value[:10]

    if path.suffix.lower() in {".md", ".txt"} and path.stat().st_size <= 2_000_000:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:100]
        except OSError:
            lines = []
        for line in lines:
            match = BUSINESS_DATE_LINE_RE.search(line)
            if match:
                return match.group(1)
    return "UNKNOWN"


def is_current_alias(path: str) -> bool:
    name = Path(path).name
    return name.startswith(("latest_", "current_")) or "_latest." in name or name in STABLE_ALIAS_NAMES


def classify_role(path: str, dependency_rows: list[dict]) -> str:
    name = Path(path).name.lower()
    stem = Path(path).stem.lower()
    if path.startswith("reports/archive/"):
        return "ARCHIVED_ARTIFACT"
    if path in RUNTIME_LOCKED_PATHS:
        return "RUNTIME_INPUT" if name != "dashboard_data.json" else "GENERATED_SNAPSHOT"
    if is_current_alias(path):
        return "CURRENT_ALIAS"
    if DATE_RE.search(stem):
        if "weekly" in stem or stem.startswith(("weekly_review_", "trading_weekly_", "project_weekly_")):
            return "DATED_WEEKLY"
        if "monthly" in stem:
            return "DATED_MONTHLY"
        if "daily" in stem or stem.startswith(("daily_signal_", "open_check_", "midday_check_")):
            return "DATED_DAILY"
    if TERMINAL_MONTH_RE.search(stem) and "monthly" in stem:
        return "DATED_MONTHLY"
    if any(token in stem for token in ("catalog", "registry", "governance", "permission", "project_context", "phase_decision")):
        return "GOVERNANCE_ARTIFACT"
    if any(token in stem for token in ("validation", "check", "readiness", "freshness", "preflight")):
        return "VALIDATION_ARTIFACT"
    if any(token in stem for token in ("audit", "diagnostic", "diagnosis")):
        return "AUDIT_ARTIFACT"
    if any(token in stem for token in ("snapshot", "dashboard_data", "status")) and path.endswith(".json"):
        return "GENERATED_SNAPSHOT"
    research_tokens = (
        "analysis",
        "backtest",
        "benchmark",
        "exposure",
        "factor",
        "model",
        "regime",
        "research",
        "risk_profile",
        "style_fit",
        "universe",
    )
    if any(token in stem for token in research_tokens):
        return "RESEARCH_ARTIFACT"
    if any(
        row["reference_type"]
        in {"APP_RUNTIME_READ", "DASHBOARD_RUNTIME_READ", "CONSUMER_READ", "FILE_COPY_SOURCE", "FILE_MOVE_SOURCE"}
        and row["direction"] in {"CONSUMER", "READ", "MOVE_SOURCE"}
        and row["confidence"] in {"HIGH", "MEDIUM"}
        for row in dependency_rows
    ):
        return "RUNTIME_INPUT"
    return "UNKNOWN"


def classify_cadence(path: str, role: str) -> str:
    name = Path(path).stem.lower()
    if role == "DATED_DAILY" or "daily" in name or name.startswith(("open_check", "midday_check", "afternoon_open")):
        return "DAILY"
    if role == "DATED_WEEKLY" or "weekly" in name:
        return "WEEKLY"
    if role == "DATED_MONTHLY" or "monthly" in name:
        return "MONTHLY"
    if role in {"CURRENT_ALIAS", "RUNTIME_INPUT", "GENERATED_SNAPSHOT"}:
        return "CONTINUOUS"
    if role != "UNKNOWN":
        return "AD_HOC"
    return "UNKNOWN"


def classify_topic(path: str) -> str:
    stem = Path(path).stem.lower()
    rules = (
        ("TUSHARE_DATA_FOUNDATION", ("tushare", "data_source", "data_update", "data_coverage", "data_health")),
        ("PAPER_EXECUTION", ("paper_execution", "paper_trade", "paper_portfolio", "paper_performance")),
        ("REPORTS_GOVERNANCE", ("report_catalog", "report_dependency", "report_taxonomy", "archive_candidate", "file_classification")),
        ("PROJECT_GOVERNANCE", ("project_context", "project_structure", "project_checkpoint", "governance", "permission")),
        ("EXPOSURE", ("exposure", "portfolio_exposure", "benchmark_redundancy")),
        ("REGIME_STYLE", ("regime", "style_fit", "style_regime")),
        ("UNIVERSE", ("universe", "etf_expansion")),
        ("APP_DASHBOARD", ("app_", "dashboard", "frontend", "ui_")),
        ("SIGNALS_RANKING", ("signal", "ranking", "sell_", "buy_")),
        ("RESEARCH", ("research", "backtest", "factor", "model")),
    )
    for topic, tokens in rules:
        if any(token in stem for token in tokens):
            return topic
    return "UNKNOWN"


def naming_compliance(path: str, role: str, current_alias: bool) -> str:
    stem = Path(path).stem
    if current_alias or role in {"RUNTIME_INPUT", "GENERATED_SNAPSHOT"}:
        return "LEGACY_STABLE_ALIAS"
    if role == "ARCHIVED_ARTIFACT":
        base_without_date = re.sub(r"_20\d{2}-\d{2}(?:-\d{2})?$", "", stem)
        snake = bool(SNAKE_RE.fullmatch(base_without_date))
        has_terminal_date = bool(TERMINAL_DATE_RE.search(stem) or TERMINAL_MONTH_RE.search(stem))
        return "COMPLIANT" if snake and has_terminal_date else "NON_COMPLIANT"
    base_without_date = re.sub(r"_20\d{2}-\d{2}(?:-\d{2})?$", "", stem)
    snake = bool(SNAKE_RE.fullmatch(base_without_date))
    if role == "DATED_MONTHLY":
        return "COMPLIANT" if snake and bool(TERMINAL_MONTH_RE.search(stem)) else "NON_COMPLIANT"
    if role in {"DATED_DAILY", "DATED_WEEKLY", "RESEARCH_ARTIFACT", "AUDIT_ARTIFACT", "VALIDATION_ARTIFACT"}:
        return "COMPLIANT" if snake and bool(TERMINAL_DATE_RE.search(stem)) else "NON_COMPLIANT"
    return "NOT_APPLICABLE" if snake else "NON_COMPLIANT"


TRUSTED_DYNAMIC_PATTERN_KINDS = {
    "DATE_TEMPLATE": r"20\d{2}(?:-\d{2}-\d{2}|\d{4})",
    "MONTH_TEMPLATE": r"20\d{2}-\d{2}",
    "MONTH_COMPACT_TEMPLATE": r"20\d{4}",
    "TIMESTAMP_TEMPLATE": r"20\d{2}(?:-?\d{2}){2}[T_-]?\d{2}(?::?\d{2}){1,2}",
    "RUN_ID_TEMPLATE": r"[A-Za-z0-9][A-Za-z0-9._-]{2,63}",
}


def _valid_temporal_token(kind: str, value: str) -> bool:
    formats = {
        "DATE_TEMPLATE": ("%Y-%m-%d", "%Y%m%d"),
        "MONTH_TEMPLATE": ("%Y-%m",),
        "MONTH_COMPACT_TEMPLATE": ("%Y%m",),
    }.get(kind)
    if formats is None:
        return True
    for format_string in formats:
        try:
            datetime.strptime(value, format_string)
            return True
        except ValueError:
            continue
    return False


def dynamic_producer_matches_path(row: dict, report_path: str) -> bool:
    """Narrowly match a trusted structured producer pattern to one report path."""

    if row.get("reference_type") != "PRODUCER_WRITE":
        return False
    if row.get("consumer_or_producer") != "PRODUCER" or row.get("static_or_dynamic") != "DYNAMIC":
        return False
    pattern = row.get("dynamic_path_pattern", "")
    kind = row.get("dynamic_pattern_kind", "")
    if not pattern or "<DYNAMIC>" in pattern or kind not in TRUSTED_DYNAMIC_PATTERN_KINDS:
        return False
    token = {
        "DATE_TEMPLATE": "<DATE>",
        "MONTH_TEMPLATE": "<MONTH>",
        "MONTH_COMPACT_TEMPLATE": "<MONTH>",
        "TIMESTAMP_TEMPLATE": "<TIMESTAMP>",
        "RUN_ID_TEMPLATE": "<RUN_ID>",
    }[kind]
    if pattern.count(token) != 1:
        return False
    expression = re.escape(pattern).replace(
        re.escape(token), f"(?P<dynamic_value>{TRUSTED_DYNAMIC_PATTERN_KINDS[kind]})"
    )
    match = re.fullmatch(expression, report_path)
    return bool(match and _valid_temporal_token(kind, match.group("dynamic_value")))


ARCHIVE_BLOCK_REASON_PRIORITY = (
    "ACTIVE_STATIC_PRODUCER",
    "ACTIVE_DYNAMIC_PRODUCER",
    "RUNTIME_CONSUMER",
    "CURRENT_ALIAS",
    "STATE_OR_GOVERNANCE_LOCKED",
    "ACTIVE_AUDIT_ARTIFACT",
    "RETENTION_BLOCKED",
    "UNKNOWN_ROLE",
    "ALREADY_ARCHIVED_LOCATION",
    "NEEDS_DATE_NORMALIZATION",
    "RETENTION_REVIEW_REQUIRED",
    "NO_ACTIVE_DEPENDENCY",
)


RULE_DEFINITIONS = {
    "ACTIVE_STATIC_PRODUCER": {"namespace": "DEPENDENCY", "evidence_type": "STATIC_PRODUCER_REFERENCE", "rule_id": "active_static_producer", "rule_version": "v1", "evaluated_field": "dependency_safety"},
    "ACTIVE_DYNAMIC_PRODUCER": {"namespace": "DEPENDENCY", "evidence_type": "DYNAMIC_PRODUCER_REFERENCE", "rule_id": "active_dynamic_producer", "rule_version": "v1", "evaluated_field": "matched_dynamic_producer_ids"},
    "RUNTIME_CONSUMER": {"namespace": "STATE_AUTHORITY", "evidence_type": "RUNTIME_CONSUMER_RULE", "rule_id": "runtime_consumer", "rule_version": "v1", "evaluated_field": "runtime_locked"},
    "CURRENT_ALIAS": {"namespace": "STATE_AUTHORITY", "evidence_type": "ALIAS_RULE", "rule_id": "current_alias", "rule_version": "v1", "evaluated_field": "current_alias"},
    "STATE_OR_GOVERNANCE_LOCKED": {"namespace": "STATE_AUTHORITY", "evidence_type": "CONTROL_ARTIFACT_RULE", "rule_id": "state_or_governance_locked", "rule_version": "v1", "evaluated_field": "role"},
    "ACTIVE_AUDIT_ARTIFACT": {"namespace": "REPORT_ROLE", "evidence_type": "CLASSIFICATION_RULE", "rule_id": "active_audit_artifact", "rule_version": "v1", "evaluated_field": "role"},
    "RETENTION_BLOCKED": {"namespace": "RETENTION", "evidence_type": "RETENTION_RULE", "rule_id": "retention_blocked", "rule_version": "v1", "evaluated_field": "retention_status"},
    "UNKNOWN_ROLE": {"namespace": "REPORT_ROLE", "evidence_type": "CLASSIFICATION_RULE", "rule_id": "unknown_role", "rule_version": "v1", "evaluated_field": "role"},
    "ALREADY_ARCHIVED_LOCATION": {"namespace": "LOCATION", "evidence_type": "LOCATION_RULE", "rule_id": "already_archived_location", "rule_version": "v1", "evaluated_field": "location_status"},
    "NEEDS_DATE_NORMALIZATION": {"namespace": "NAMING", "evidence_type": "NAMING_RULE", "rule_id": "needs_date_normalization", "rule_version": "v1", "evaluated_field": "naming_status"},
    "RETENTION_REVIEW_REQUIRED": {"namespace": "RETENTION", "evidence_type": "RETENTION_RULE", "rule_id": "retention_review_required", "rule_version": "v1", "evaluated_field": "retention_status"},
    "NO_ACTIVE_DEPENDENCY": {"namespace": "GOVERNANCE_RULE", "evidence_type": "ELIGIBILITY_RULE", "rule_id": "no_active_dependency", "rule_version": "v1", "evaluated_field": "dependency_safety"},
}


def governance_evidence_id(report_id: str, reason: str, source_record_id: str = "") -> str:
    definition = RULE_DEFINITIONS[reason]
    identity = {
        "report_id": report_id,
        "reason": reason,
        "source_record_id": source_record_id,
        "rule_id": definition["rule_id"],
        "rule_version": definition["rule_version"],
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    namespace = "DEPENDENCY" if source_record_id else definition["namespace"]
    return f"evidence_{namespace.lower()}_{digest}"


def _rule_evidence_id(report_id: str, reason: str) -> str:
    return governance_evidence_id(report_id, reason)


def _dependency_evidence_ids(report_id: str, reason: str, rows: Sequence[dict]) -> list[str]:
    return sorted(
        governance_evidence_id(report_id, reason, row["reference_id"])
        for row in rows
    )


def _retention_status(role: str, current_alias: bool, runtime_locked: bool) -> str:
    if role in {"GOVERNANCE_ARTIFACT", "VALIDATION_ARTIFACT"}:
        return "PERMANENT"
    if current_alias or runtime_locked or role in {"RUNTIME_INPUT", "CURRENT_ALIAS", "ARCHIVED_ARTIFACT"}:
        return "PROJECT_LIFETIME"
    if role in {"DATED_DAILY", "DATED_WEEKLY", "DATED_MONTHLY"}:
        return "ROLLING_WINDOW"
    return "MANUAL_REVIEW"


def _normalized_naming_status(role: str, current_alias: bool, naming: str) -> str:
    if current_alias:
        return "LEGACY_STABLE_ALIAS"
    if role in {"DATED_DAILY", "DATED_WEEKLY", "DATED_MONTHLY"} and naming == "COMPLIANT":
        return "COMPLIANT_DATED"
    if role == "ARCHIVED_ARTIFACT":
        return "NEEDS_DATE_NORMALIZATION" if naming == "NON_COMPLIANT" else "NOT_APPLICABLE"
    if role in {"RUNTIME_INPUT", "GENERATED_SNAPSHOT"}:
        return "NOT_APPLICABLE"
    if role == "UNKNOWN":
        return "UNKNOWN"
    if naming == "NON_COMPLIANT":
        return "NEEDS_DATE_NORMALIZATION"
    return "NOT_APPLICABLE"


def determine_migration_eligibility(
    *,
    location_status: str,
    runtime_locked: bool,
    current_alias: bool,
    active_generator: bool,
    active_consumer: bool,
    dependency_safety: str,
    role: str,
    retention_status: str,
    naming_status: str,
) -> str:
    if location_status == "ALREADY_ARCHIVED":
        return "MIGRATION_NOT_APPLICABLE_ALREADY_ARCHIVED"
    if location_status == "GOVERNANCE_CONTROL_LOCATION":
        return "MIGRATION_NOT_APPLICABLE_CONTROL_ARTIFACT"
    if runtime_locked or current_alias:
        return "MIGRATION_BLOCKED_RUNTIME"
    if active_generator or active_consumer:
        return "MIGRATION_BLOCKED_ACTIVE_DEPENDENCY"
    if dependency_safety == "UNKNOWN_DEPENDENCY" or role == "UNKNOWN":
        return "MIGRATION_BLOCKED_UNKNOWN"
    if retention_status in {"PERMANENT", "UNTIL_MIGRATION_VALIDATED", "TEMPORARY_AUDIT"}:
        return "MIGRATION_BLOCKED_RETENTION"
    if naming_status == "NEEDS_DATE_NORMALIZATION":
        return "SAFE_TO_MIGRATE_RENAME_REQUIRED"
    return "SAFE_TO_MIGRATE"


def build_catalog_records(
    root: Path,
    dependency_rows: list[dict],
    archive_roots: Sequence[str] = DEFAULT_ARCHIVE_ROOTS,
) -> list[dict]:
    archive_roots = normalize_archive_roots(archive_roots)
    by_report: dict[str, list[dict]] = defaultdict(list)
    dynamic_producers: list[dict] = []
    for row in dependency_rows:
        if row["static_or_dynamic"] == "STATIC":
            by_report[row["referenced_report_path"]].append(row)
        elif row.get("reference_type") == "PRODUCER_WRITE" and row.get("consumer_or_producer") == "PRODUCER":
            dynamic_producers.append(row)
    created_dates, modified_dates = git_report_dates(root)
    records: list[dict] = []
    for path in iter_report_paths(root):
        current_path = relative_path(root, path)
        static_dependencies = by_report.get(current_path, [])
        matched_dynamic_producers = [
            row for row in dynamic_producers if dynamic_producer_matches_path(row, current_path)
        ]
        dependencies = [*static_dependencies, *matched_dynamic_producers]
        producers = sorted({row["source_file"] for row in dependencies if row["consumer_or_producer"] == "PRODUCER"})
        consumers = sorted({row["source_file"] for row in dependencies if row["consumer_or_producer"] == "CONSUMER"})
        role = classify_role(current_path, dependencies)
        current_alias = is_current_alias(current_path)
        location_status = classify_location_status(
            current_path,
            archive_roots,
            is_symlink=path.is_symlink(),
        )
        runtime_locked = current_path in RUNTIME_LOCKED_PATHS or any(
            row["reference_type"]
            in {"APP_RUNTIME_READ", "DASHBOARD_RUNTIME_READ", "CONSUMER_READ", "FILE_COPY_SOURCE", "FILE_MOVE_SOURCE"}
            and row["direction"] in {"CONSUMER", "READ", "MOVE_SOURCE"}
            and row["confidence"] in {"HIGH", "MEDIUM"}
            and row["source_file"].startswith(("app/", "dashboard/", "scripts/", "src/"))
            for row in dependencies
        )
        dated_artifact = role in {"DATED_DAILY", "DATED_WEEKLY", "DATED_MONTHLY"}
        active_static_producer = any(
            row["consumer_or_producer"] == "PRODUCER" for row in static_dependencies
        )
        active_dynamic_producer = bool(matched_dynamic_producers)
        active_generator = active_static_producer or active_dynamic_producer
        runtime_consumer_rows = [
            row
            for row in dependencies
            if row["reference_type"]
            in {"APP_RUNTIME_READ", "DASHBOARD_RUNTIME_READ", "CONSUMER_READ", "FILE_COPY_SOURCE", "FILE_MOVE_SOURCE"}
            and row["direction"] in {"CONSUMER", "READ", "MOVE_SOURCE"}
            and row["confidence"] in {"HIGH", "MEDIUM"}
        ]
        active_consumer = bool(runtime_consumer_rows)
        business_date = extract_business_date(path)
        topic = classify_topic(current_path)
        naming = naming_compliance(current_path, role, current_alias)
        normalized_naming = _normalized_naming_status(role, current_alias, naming)
        retention_status = _retention_status(role, current_alias, runtime_locked)
        if runtime_locked:
            dependency_safety = "RUNTIME_LOCKED"
        elif active_generator:
            dependency_safety = "ACTIVE_PRODUCER"
        elif active_consumer:
            dependency_safety = "ACTIVE_CONSUMER"
        elif any(row["reference_type"] == "UNKNOWN_REFERENCE" for row in dependencies):
            dependency_safety = "UNKNOWN_DEPENDENCY"
        else:
            dependency_safety = "NO_ACTIVE_DEPENDENCY"

        report_id = stable_report_id(current_path)
        evidence_by_reason: dict[str, list[str]] = {}
        if active_static_producer:
            evidence_by_reason["ACTIVE_STATIC_PRODUCER"] = _dependency_evidence_ids(
                report_id,
                "ACTIVE_STATIC_PRODUCER",
                [row for row in static_dependencies if row["consumer_or_producer"] == "PRODUCER"],
            )
        if active_dynamic_producer:
            evidence_by_reason["ACTIVE_DYNAMIC_PRODUCER"] = _dependency_evidence_ids(
                report_id,
                "ACTIVE_DYNAMIC_PRODUCER",
                matched_dynamic_producers,
            )
        if runtime_locked or active_consumer:
            ids = _dependency_evidence_ids(
                report_id,
                "RUNTIME_CONSUMER",
                runtime_consumer_rows,
            )
            evidence_by_reason["RUNTIME_CONSUMER"] = ids or [
                _rule_evidence_id(report_id, "RUNTIME_CONSUMER")
            ]
        if current_alias:
            evidence_by_reason["CURRENT_ALIAS"] = [_rule_evidence_id(report_id, "CURRENT_ALIAS")]
        if role in {"GOVERNANCE_ARTIFACT", "VALIDATION_ARTIFACT"}:
            evidence_by_reason["STATE_OR_GOVERNANCE_LOCKED"] = [
                _rule_evidence_id(report_id, "STATE_OR_GOVERNANCE_LOCKED")
            ]
        if role == "AUDIT_ARTIFACT" and (active_generator or active_consumer):
            evidence_by_reason["ACTIVE_AUDIT_ARTIFACT"] = [
                _rule_evidence_id(report_id, "ACTIVE_AUDIT_ARTIFACT")
            ]
        if retention_status in {"PERMANENT", "PROJECT_LIFETIME", "UNTIL_MIGRATION_VALIDATED", "TEMPORARY_AUDIT"}:
            evidence_by_reason["RETENTION_BLOCKED"] = [
                _rule_evidence_id(report_id, "RETENTION_BLOCKED")
            ]
        if role == "UNKNOWN":
            evidence_by_reason["UNKNOWN_ROLE"] = [_rule_evidence_id(report_id, "UNKNOWN_ROLE")]
        if location_status == "ALREADY_ARCHIVED":
            evidence_by_reason["ALREADY_ARCHIVED_LOCATION"] = [
                _rule_evidence_id(report_id, "ALREADY_ARCHIVED_LOCATION")
            ]
        if normalized_naming == "NEEDS_DATE_NORMALIZATION":
            evidence_by_reason["NEEDS_DATE_NORMALIZATION"] = [
                _rule_evidence_id(report_id, "NEEDS_DATE_NORMALIZATION")
            ]
        if dependency_safety == "NO_ACTIVE_DEPENDENCY":
            evidence_by_reason["NO_ACTIVE_DEPENDENCY"] = [
                _rule_evidence_id(report_id, "NO_ACTIVE_DEPENDENCY")
            ]
        if retention_status in {"ROLLING_WINDOW", "MANUAL_REVIEW"}:
            evidence_by_reason["RETENTION_REVIEW_REQUIRED"] = [
                _rule_evidence_id(report_id, "RETENTION_REVIEW_REQUIRED")
            ]
        archive_block_reasons = [
            reason for reason in ARCHIVE_BLOCK_REASON_PRIORITY if reason in evidence_by_reason
        ]
        primary_archive_block_reason = archive_block_reasons[0] if archive_block_reasons else "NONE"
        archive_block_evidence_ids = sorted(
            {item for items in evidence_by_reason.values() for item in items}
        )

        migration_eligibility = determine_migration_eligibility(
            location_status=location_status,
            runtime_locked=runtime_locked,
            current_alias=current_alias,
            active_generator=active_generator,
            active_consumer=active_consumer,
            dependency_safety=dependency_safety,
            role=role,
            retention_status=retention_status,
            naming_status=normalized_naming,
        )

        if location_status == "ALREADY_ARCHIVED":
            deletion_eligibility = "NOT_DELETION_CANDIDATE"
        elif active_generator or active_consumer or runtime_locked or current_alias or role == "UNKNOWN":
            deletion_eligibility = "DELETION_BLOCKED"
        elif retention_status in {"ROLLING_WINDOW", "MANUAL_REVIEW"}:
            deletion_eligibility = "DELETION_REVIEW_REQUIRED"
        else:
            deletion_eligibility = "NOT_DELETION_CANDIDATE"

        # Deprecated compatibility fields. Phase A no longer uses a single
        # archive flag as either migration or deletion authorization.
        archive_candidate = False
        archive_block_reason = primary_archive_block_reason
        if runtime_locked:
            migration_risk = "RUNTIME_LOCKED"
        elif len(dependencies) >= 10:
            migration_risk = "HIGH_DEPENDENCY"
        elif active_generator or (dependencies and current_alias):
            migration_risk = "ACTIVE_REFERENCED"
        elif dependencies:
            migration_risk = "MEDIUM_DEPENDENCY"
        elif archive_candidate:
            migration_risk = "LOW_RISK_ARCHIVE_CANDIDATE"
        else:
            migration_risk = "UNKNOWN_REQUIRES_REVIEW"
        known_metadata = sum(
            (
                role != "UNKNOWN",
                topic != "UNKNOWN",
                business_date != "UNKNOWN" or not dated_artifact,
                bool(producers or consumers),
            )
        )
        metadata_compliance = "COMPLETE" if known_metadata == 4 else "PARTIAL" if known_metadata >= 2 else "MISSING"
        confidence = "HIGH" if role != "UNKNOWN" and dependencies else "MEDIUM" if role != "UNKNOWN" else "LOW"
        status = (
            "ARCHIVED"
            if role == "ARCHIVED_ARTIFACT"
            else "ACTIVE"
            if current_alias or runtime_locked
            else "HISTORICAL"
            if dated_artifact
            else "UNKNOWN"
        )
        notes: list[str] = []
        if runtime_locked:
            notes.append("Keep the current path stable until a registry-backed compatibility layer exists.")
        if archive_candidate:
            notes.append("Candidate only; Phase A performs no move or rename.")
        if active_dynamic_producer:
            notes.append("Archive blocked by a trusted active dynamic Producer pattern.")
        if business_date == "UNKNOWN":
            notes.append("Business date was not inferred from filesystem timestamps.")
        records.append(
            {
                "report_id": report_id,
                "current_path": current_path,
                "filename": path.name,
                "extension": path.suffix.lower() or "[no_ext]",
                "role": role,
                "cadence": classify_cadence(current_path, role),
                "topic": topic,
                "status": status,
                "location_status": location_status,
                "business_date": business_date,
                "created_date": created_dates.get(current_path, "UNKNOWN"),
                "modified_at": modified_dates.get(current_path, "UNKNOWN"),
                "producer_candidates": producers,
                "consumer_candidates": consumers,
                "reference_count": len(dependencies),
                "matched_dynamic_producer_count": len(matched_dynamic_producers),
                "matched_dynamic_producer_ids": sorted(
                    {row["reference_id"] for row in matched_dynamic_producers}
                ),
                "dynamic_producer_match_confidence": (
                    "HIGH"
                    if matched_dynamic_producers
                    and all(row["confidence"] == "HIGH" for row in matched_dynamic_producers)
                    else "MEDIUM"
                    if matched_dynamic_producers
                    and all(row["confidence"] in {"HIGH", "MEDIUM"} for row in matched_dynamic_producers)
                    else "LOW"
                    if matched_dynamic_producers
                    else "NONE"
                ),
                "active_generator": active_generator,
                "producer_match_type": (
                    "BOTH"
                    if active_static_producer and active_dynamic_producer
                    else "DYNAMIC_PATTERN"
                    if active_dynamic_producer
                    else "STATIC_EXACT"
                    if active_static_producer
                    else "NONE"
                ),
                "archive_block_reason": archive_block_reason,
                "archive_block_reasons": archive_block_reasons,
                "primary_archive_block_reason": primary_archive_block_reason,
                "archive_block_evidence_ids": archive_block_evidence_ids,
                "archive_block_evidence": evidence_by_reason,
                "dependency_safety": dependency_safety,
                "naming_status": normalized_naming,
                "retention_status": retention_status,
                "migration_eligibility": migration_eligibility,
                "deletion_eligibility": deletion_eligibility,
                "runtime_locked": runtime_locked,
                "current_alias": current_alias,
                "dated_artifact": dated_artifact,
                "archive_candidate": archive_candidate,
                "migration_risk": migration_risk,
                "naming_compliance": naming,
                "metadata_compliance": metadata_compliance,
                "confidence": confidence,
                "notes": " ".join(notes),
            }
        )
    return sorted(records, key=lambda row: row["current_path"])


def catalog_payload(
    records: list[dict], metadata: dict | None = None, control_plane_exclusions: list[str] | None = None
) -> dict:
    fingerprint = hashlib.sha256(
        json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": CLASSIFICATION_SCHEMA_VERSION,
        "catalog_id": "a_share_swing_system_report_catalog_v3",
        "repository_root": "<project_root>",
        "metadata": metadata or {},
        "control_plane_exclusions": sorted(control_plane_exclusions or CONTROL_REPORT_PATHS),
        "record_count": len(records),
        "catalog_sha256": fingerprint,
        "summary": {
            "by_role": dict(sorted(Counter(row["role"] for row in records).items())),
            "by_location_status": dict(
                sorted(Counter(row["location_status"] for row in records).items())
            ),
            "by_migration_risk": dict(sorted(Counter(row["migration_risk"] for row in records).items())),
            "by_dependency_safety": dict(
                sorted(Counter(row["dependency_safety"] for row in records).items())
            ),
            "by_naming_status": dict(
                sorted(Counter(row["naming_status"] for row in records).items())
            ),
            "by_retention_status": dict(
                sorted(Counter(row["retention_status"] for row in records).items())
            ),
            "by_migration_eligibility": dict(
                sorted(Counter(row["migration_eligibility"] for row in records).items())
            ),
            "by_deletion_eligibility": dict(
                sorted(Counter(row["deletion_eligibility"] for row in records).items())
            ),
            "by_archive_block_reason": dict(
                sorted(
                    Counter(
                        reason
                        for row in records
                        for reason in row["archive_block_reasons"]
                    ).items()
                )
            ),
            "runtime_locked_count": sum(row["runtime_locked"] for row in records),
            "current_alias_count": sum(row["current_alias"] for row in records),
            "dated_artifact_count": sum(row["dated_artifact"] for row in records),
            "archive_candidate_count": sum(row["archive_candidate"] for row in records),
            "safe_to_delete_after_authorization_count": sum(
                row["deletion_eligibility"] == "SAFE_TO_DELETE_AFTER_AUTHORIZATION"
                for row in records
            ),
            "active_generator_count": sum(row["active_generator"] for row in records),
            "dynamic_producer_matched_report_count": sum(
                row["matched_dynamic_producer_count"] > 0 for row in records
            ),
            "unknown_role_count": sum(row["role"] == "UNKNOWN" for row in records),
            "already_archived_count": sum(
                row["location_status"] == "ALREADY_ARCHIVED" for row in records
            ),
            "phase_b_candidate_count": sum(
                row["migration_eligibility"]
                in {"SAFE_TO_MIGRATE", "SAFE_TO_MIGRATE_RENAME_REQUIRED"}
                for row in records
            ),
        },
        "phase_b_candidate_paths": [
            row["current_path"]
            for row in records
            if row["migration_eligibility"]
            in {"SAFE_TO_MIGRATE", "SAFE_TO_MIGRATE_RENAME_REQUIRED"}
        ],
        "records": records,
    }


def _markdown_value(value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, list):
        return ", ".join(value) if value else "-"
    return str(value) if value not in (None, "") else "-"


def render_catalog_markdown(payload: dict, front_matter: str = "") -> str:
    summary = payload["summary"]
    role_lines = "\n".join(f"- `{key}`: {value}" for key, value in summary["by_role"].items())
    risk_lines = "\n".join(f"- `{key}`: {value}" for key, value in summary["by_migration_risk"].items())
    location_lines = "\n".join(
        f"- `{key}`: {value}" for key, value in summary["by_location_status"].items()
    )
    migration_lines = "\n".join(
        f"- `{key}`: {value}" for key, value in summary["by_migration_eligibility"].items()
    )
    deletion_lines = "\n".join(
        f"- `{key}`: {value}" for key, value in summary["by_deletion_eligibility"].items()
    )
    reason_lines = "\n".join(
        f"- `{key}`: {value}" for key, value in summary["by_archive_block_reason"].items()
    )
    table = [
        "| Path | Role | Location | Dependency safety | Naming | Retention | Migration | Deletion | Reasons |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["records"]:
        table.append(
            f"| `{row['current_path']}` | `{row['role']}` | `{row['location_status']}` | `{row['dependency_safety']}` | "
            f"`{row['naming_status']}` | `{row['retention_status']}` | "
            f"`{row['migration_eligibility']}` | `{row['deletion_eligibility']}` | "
            f"{_markdown_value(row['archive_block_reasons'])} |"
        )
    return f"""{front_matter}# Report Catalog

本文件由 `scripts/governance/build_report_catalog.py` 生成。Catalog 是只读治理索引，不授权移动、重命名或删除报告。

为避免自引用导致每次运行增加记录，Phase A 自身的 Catalog、Dependency Registry 和 summary 输出明确列为 control-plane exclusions；其他 `reports/**` 文件均进入 inventory。

## Summary

- Catalog records: {payload['record_count']}
- Runtime locked: {summary['runtime_locked_count']}
- Current aliases: {summary['current_alias_count']}
- Dated artifacts: {summary['dated_artifact_count']}
- Deprecated Archive Candidate flag true: {summary['archive_candidate_count']}
- Safe-to-delete-after-authorization: {summary['safe_to_delete_after_authorization_count']}
- Unknown roles requiring review: {summary['unknown_role_count']}
- Already archived: {summary['already_archived_count']}
- Phase B candidates: {summary['phase_b_candidate_count']}
- Catalog SHA-256: `{payload['catalog_sha256']}`

### Roles

{role_lines}

### Migration risks

{risk_lines}

### Location status

{location_lines}

### Migration eligibility

{migration_lines}

### Deletion eligibility

{deletion_lines}

### Classification reasons

{reason_lines}

## Inventory

{chr(10).join(table)}
"""
