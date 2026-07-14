"""Shared deterministic helpers for Reports Governance Phase A.

The helpers in this module are inventory-only. They never move, rename, delete,
or rewrite an existing report and they do not read credentials or runtime data
outside tracked/report metadata needed for classification.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


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
    "APP_RUNTIME_READ",
    "DASHBOARD_RUNTIME_READ",
    "TEST_REFERENCE",
    "DOCUMENTATION_LINK",
    "STATE_INDEX_REFERENCE",
    "DYNAMIC_PATH_PATTERN",
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
    return path.resolve().relative_to(root.resolve()).as_posix()


def stable_report_id(current_path: str) -> str:
    digest = hashlib.sha256(current_path.encode("utf-8")).hexdigest()[:16]
    return f"report_{digest}"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


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
        if item in CONTROL_REPORT_PATHS or not _allowed_scan_path(item):
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

    found: dict[str, str] = {}
    for match in EXPLICIT_REPORT_RE.finditer(line):
        value = _clean_reference(match.group(1))
        if value != "reports/":
            found[value] = "DYNAMIC" if _is_dynamic(value) else "STATIC"

    for match in SHELL_REPORT_DIR_RE.finditer(line):
        value = _clean_reference("reports/" + match.group(1).strip("/"))
        found[value] = "DYNAMIC" if _is_dynamic(value) else "STATIC_COMPUTED"

    expression_matches = list(REPORT_DIR_SLASH_RE.finditer(line))
    expression_matches += list(REPORT_DIR_JOIN_RE.finditer(line))
    expression_matches += list(REPORT_DIR_METHOD_JOIN_RE.finditer(line))
    for match in expression_matches:
        segments = [
            value.strip("/")
            for value in QUOTED_VALUE_RE.findall(match.group("tail"))
            if value.strip("/") and value not in {"r", "w", "a", "rb", "wb", "utf-8", "reports"}
        ]
        if segments and segments[-1].endswith(REPORT_EXTENSIONS):
            value = _clean_reference("reports/" + "/".join(segments))
            found[value] = "DYNAMIC" if _is_dynamic(value) else "STATIC_COMPUTED"

    return sorted(found.items())


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
    seen: set[tuple] = set()
    for source_file, path in iter_repository_text_files(root):
        if source_file == "scripts/governance/report_governance_common.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for reference, resolution in extract_report_references(line):
                reference_type, actor, confidence, impact = classify_reference(source_file, line, resolution)
                key = (source_file, line_number, reference, reference_type, actor)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "source_file": source_file,
                        "source_line": line_number,
                        "referenced_report_path": reference,
                        "reference_type": reference_type,
                        "consumer_or_producer": actor,
                        "static_or_dynamic": "DYNAMIC" if resolution == "DYNAMIC" else "STATIC",
                        "confidence": confidence,
                        "migration_impact": impact,
                        "notes": (
                            "Dynamic pattern retained without fabricating concrete dependencies."
                            if resolution == "DYNAMIC"
                            else "Exact path reference."
                            if resolution == "STATIC"
                            else "Path reconstructed from a recognizable report-directory expression."
                        ),
                    }
                )
    return sorted(
        rows,
        key=lambda row: (
            row["referenced_report_path"],
            row["source_file"],
            row["source_line"],
            row["reference_type"],
        ),
    )


def dependency_payload(rows: list[dict]) -> dict:
    fingerprint = hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": 1,
        "registry_id": "a_share_swing_system_report_dependency_registry_v1",
        "repository_root": "<project_root>",
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


def render_dependency_markdown(payload: dict) -> str:
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
    return f"""# Report Dependency Registry

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

完整逐行 registry 见 `reports/report_dependency_registry.csv` 和 `reports/report_dependency_registry.json`。
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
            if path.is_file() and relative_path(root, path) not in CONTROL_REPORT_PATHS
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
    if any(row["reference_type"] in {"APP_RUNTIME_READ", "DASHBOARD_RUNTIME_READ"} for row in dependency_rows):
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
        return "NOT_APPLICABLE"
    base_without_date = re.sub(r"_20\d{2}-\d{2}(?:-\d{2})?$", "", stem)
    snake = bool(SNAKE_RE.fullmatch(base_without_date))
    if role == "DATED_MONTHLY":
        return "COMPLIANT" if snake and bool(TERMINAL_MONTH_RE.search(stem)) else "NON_COMPLIANT"
    if role in {"DATED_DAILY", "DATED_WEEKLY", "RESEARCH_ARTIFACT", "AUDIT_ARTIFACT", "VALIDATION_ARTIFACT"}:
        return "COMPLIANT" if snake and bool(TERMINAL_DATE_RE.search(stem)) else "NON_COMPLIANT"
    return "NOT_APPLICABLE" if snake else "NON_COMPLIANT"


def build_catalog_records(root: Path, dependency_rows: list[dict]) -> list[dict]:
    by_report: dict[str, list[dict]] = defaultdict(list)
    for row in dependency_rows:
        if row["static_or_dynamic"] == "STATIC":
            by_report[row["referenced_report_path"]].append(row)
    created_dates, modified_dates = git_report_dates(root)
    records: list[dict] = []
    for path in iter_report_paths(root):
        current_path = relative_path(root, path)
        dependencies = by_report.get(current_path, [])
        producers = sorted({row["source_file"] for row in dependencies if row["consumer_or_producer"] == "PRODUCER"})
        consumers = sorted({row["source_file"] for row in dependencies if row["consumer_or_producer"] == "CONSUMER"})
        role = classify_role(current_path, dependencies)
        current_alias = is_current_alias(current_path)
        runtime_locked = current_path in RUNTIME_LOCKED_PATHS or any(
            row["reference_type"] in {"APP_RUNTIME_READ", "DASHBOARD_RUNTIME_READ"} for row in dependencies
        )
        dated_artifact = role in {"DATED_DAILY", "DATED_WEEKLY", "DATED_MONTHLY"}
        archive_candidate = dated_artifact and not runtime_locked and not current_alias and not dependencies
        if runtime_locked:
            migration_risk = "RUNTIME_LOCKED"
        elif len(dependencies) >= 10:
            migration_risk = "HIGH_DEPENDENCY"
        elif dependencies and current_alias:
            migration_risk = "ACTIVE_REFERENCED"
        elif dependencies:
            migration_risk = "MEDIUM_DEPENDENCY"
        elif archive_candidate:
            migration_risk = "LOW_RISK_ARCHIVE_CANDIDATE"
        else:
            migration_risk = "UNKNOWN_REQUIRES_REVIEW"
        business_date = extract_business_date(path)
        topic = classify_topic(current_path)
        naming = naming_compliance(current_path, role, current_alias)
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
        if business_date == "UNKNOWN":
            notes.append("Business date was not inferred from filesystem timestamps.")
        records.append(
            {
                "report_id": stable_report_id(current_path),
                "current_path": current_path,
                "filename": path.name,
                "extension": path.suffix.lower() or "[no_ext]",
                "role": role,
                "cadence": classify_cadence(current_path, role),
                "topic": topic,
                "status": status,
                "business_date": business_date,
                "created_date": created_dates.get(current_path, "UNKNOWN"),
                "modified_at": modified_dates.get(current_path, "UNKNOWN"),
                "producer_candidates": producers,
                "consumer_candidates": consumers,
                "reference_count": len(dependencies),
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


def catalog_payload(records: list[dict]) -> dict:
    fingerprint = hashlib.sha256(
        json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": 1,
        "catalog_id": "a_share_swing_system_report_catalog_v1",
        "repository_root": "<project_root>",
        "control_plane_exclusions": sorted(CONTROL_REPORT_PATHS),
        "record_count": len(records),
        "catalog_sha256": fingerprint,
        "summary": {
            "by_role": dict(sorted(Counter(row["role"] for row in records).items())),
            "by_migration_risk": dict(sorted(Counter(row["migration_risk"] for row in records).items())),
            "runtime_locked_count": sum(row["runtime_locked"] for row in records),
            "current_alias_count": sum(row["current_alias"] for row in records),
            "dated_artifact_count": sum(row["dated_artifact"] for row in records),
            "archive_candidate_count": sum(row["archive_candidate"] for row in records),
            "unknown_role_count": sum(row["role"] == "UNKNOWN" for row in records),
        },
        "records": records,
    }


def _markdown_value(value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, list):
        return ", ".join(value) if value else "-"
    return str(value) if value not in (None, "") else "-"


def render_catalog_markdown(payload: dict) -> str:
    summary = payload["summary"]
    role_lines = "\n".join(f"- `{key}`: {value}" for key, value in summary["by_role"].items())
    risk_lines = "\n".join(f"- `{key}`: {value}" for key, value in summary["by_migration_risk"].items())
    table = [
        "| Path | Role | Cadence | Topic | Business date | References | Risk | Alias | Archive candidate |",
        "| --- | --- | --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in payload["records"]:
        table.append(
            f"| `{row['current_path']}` | `{row['role']}` | `{row['cadence']}` | `{row['topic']}` | "
            f"`{row['business_date']}` | {row['reference_count']} | `{row['migration_risk']}` | "
            f"{_markdown_value(row['current_alias'])} | {_markdown_value(row['archive_candidate'])} |"
        )
    return f"""# Report Catalog

本文件由 `scripts/governance/build_report_catalog.py` 生成。Catalog 是只读治理索引，不授权移动、重命名或删除报告。

为避免自引用导致每次运行增加记录，Phase A 自身的 Catalog、Dependency Registry 和 summary 输出明确列为 control-plane exclusions；其他 `reports/**` 文件均进入 inventory。

## Summary

- Catalog records: {payload['record_count']}
- Runtime locked: {summary['runtime_locked_count']}
- Current aliases: {summary['current_alias_count']}
- Dated artifacts: {summary['dated_artifact_count']}
- Low-risk archive candidates: {summary['archive_candidate_count']}
- Unknown roles requiring review: {summary['unknown_role_count']}
- Catalog SHA-256: `{payload['catalog_sha256']}`

### Roles

{role_lines}

### Migration risks

{risk_lines}

## Inventory

{chr(10).join(table)}
"""
