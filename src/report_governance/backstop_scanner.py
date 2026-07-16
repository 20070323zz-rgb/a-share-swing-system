from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .common import RunContext, normalized_relative, posix_relative, read_text_lossy, sha256_bytes, source_files, stable_id


DATE_IN_NAME = re.compile(r"20\d{2}[-_]?[01]\d[-_]?[0-3]\d")
REPORT_PATH_TOKEN = re.compile(r"(?:\.\./|\./)?reports/[A-Za-z0-9_./{}%:+*-]+")
FILENAME_TOKEN = re.compile(r"(?<![A-Za-z0-9_.-])([A-Za-z0-9][A-Za-z0-9_.-]*\.[A-Za-z0-9]+)(?![A-Za-z0-9_.-])")
STEM_TOKEN = re.compile(r"(?<![A-Za-z0-9_-])([A-Za-z0-9][A-Za-z0-9_-]{3,})(?![A-Za-z0-9_-])")
QUERY_TYPES = (
    "EXACT_RELATIVE_PATH",
    "EXACT_BASENAME",
    "EXACT_STEM",
    "CONFIG_KEY_VALUE",
    "SHELL_TOKEN",
    "STRING_CONCAT",
    "DYNAMIC_PREFIX_EXTENSION",
    "PATH_CONSTRUCT",
)
CONFIG_SUFFIXES = {".cfg", ".ini", ".json", ".plist", ".toml", ".yaml", ".yml"}
CODE_SUFFIXES = {".js", ".jsx", ".py", ".sh", ".ts", ".tsx"}


def _dynamic_parts(report_path: str) -> tuple[str, str, str] | None:
    filename = Path(report_path).name
    match = DATE_IN_NAME.search(filename)
    if not match:
        return None
    prefix = filename[: match.start()]
    suffix = filename[match.end() :]
    if len(prefix.rstrip("_-")) < 4 or not suffix:
        return None
    parent = Path(report_path).parent.as_posix()
    parent_constraint = "" if parent == "reports" else parent.removeprefix("reports/") + "/"
    return parent_constraint, prefix, suffix


def _match_payload(source_path: str, line_number: int, line: str, match_kind: str) -> dict[str, Any]:
    excerpt = line.strip()[:500]
    return {
        "source_path": source_path,
        "line": line_number,
        "excerpt": excerpt,
        "excerpt_sha256": sha256_bytes(excerpt.encode("utf-8")),
        "match_kind": match_kind,
        "source_class": "DOCUMENTATION" if Path(source_path).suffix.lower() == ".md" else "ACTIVE_SOURCE",
    }


def _dedupe(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique = {
        (item["source_path"], item["line"], item["match_kind"], item["excerpt_sha256"]): item
        for item in matches
    }
    return [unique[key] for key in sorted(unique)]


def _candidate_reports(
    line: str,
    path_map: dict[str, dict[str, Any]],
    basename_map: dict[str, list[dict[str, Any]]],
    stem_map: dict[str, list[dict[str, Any]]],
) -> tuple[set[str], set[str], set[str]]:
    paths = {
        normalized_relative(token)
        for token in REPORT_PATH_TOKEN.findall(line)
        if normalized_relative(token) in path_map
    }
    basenames = {token for token in FILENAME_TOKEN.findall(line) if token in basename_map}
    stems = {token for token in STEM_TOKEN.findall(line) if token in stem_map}
    return paths, basenames, stems


def scan_backstop_references(context: RunContext, reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Independent bounded text engine; it never consumes structured results or declares safety."""
    path_map = {item["relative_path"]: item for item in reports}
    basename_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    stem_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    dynamic_specs: list[tuple[dict[str, Any], str, str, str]] = []
    for report in reports:
        basename_map[report["filename"]].append(report)
        stem_map[Path(report["filename"]).stem].append(report)
        dynamic = _dynamic_parts(report["relative_path"])
        if dynamic:
            dynamic_specs.append((report, *dynamic))

    hits: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for path in source_files(context):
        source_path = posix_relative(path, context.root)
        suffix = path.suffix.lower()
        source_text = read_text_lossy(path)
        for line_number, line in enumerate(source_text.splitlines(), 1):
            paths, basenames, stems = _candidate_reports(line, path_map, basename_map, stem_map)
            path_reports = {path_map[value]["report_id"]: path_map[value] for value in paths}
            basename_reports = {
                report["report_id"]: report for value in basenames for report in basename_map[value]
            }
            stem_reports = {report["report_id"]: report for value in stems for report in stem_map[value]}
            for report in path_reports.values():
                hits[(report["report_id"], "EXACT_RELATIVE_PATH")].append(
                    _match_payload(source_path, line_number, line, "EXACT_RELATIVE_PATH")
                )
            for report in basename_reports.values():
                hits[(report["report_id"], "EXACT_BASENAME")].append(
                    _match_payload(source_path, line_number, line, "EXACT_BASENAME")
                )
            for report in stem_reports.values():
                hits[(report["report_id"], "EXACT_STEM")].append(
                    _match_payload(source_path, line_number, line, "EXACT_STEM")
                )
            exact_reports = {**stem_reports, **basename_reports, **path_reports}
            if suffix in CONFIG_SUFFIXES and re.search(r"[:=]", line):
                for report in exact_reports.values():
                    hits[(report["report_id"], "CONFIG_KEY_VALUE")].append(
                        _match_payload(source_path, line_number, line, "CONFIG_KEY_VALUE")
                    )
            if suffix == ".sh":
                for report in exact_reports.values():
                    hits[(report["report_id"], "SHELL_TOKEN")].append(
                        _match_payload(source_path, line_number, line, "SHELL_TOKEN")
                    )
            if suffix in CODE_SUFFIXES and re.search(r"\+|`|\bf[\"']|\.format\(", line):
                compact = re.sub(r"[\s\"'`+]", "", line)
                for report in reports if "reports" in compact else []:
                    if report["relative_path"] in compact:
                        hits[(report["report_id"], "STRING_CONCAT")].append(
                            _match_payload(source_path, line_number, line, "STRING_CONCAT")
                        )
            if suffix in CODE_SUFFIXES and re.search(r"\bPath\s*\(|\.joinpath\s*\(|[\"']reports[\"']\s*/", line):
                for report in exact_reports.values():
                    hits[(report["report_id"], "PATH_CONSTRUCT")].append(
                        _match_payload(source_path, line_number, line, "PATH_CONSTRUCT")
                    )
            if re.search(r"\*|\{|\}|%|\$|\+|strftime|isoformat", line):
                for report, parent_constraint, prefix, tail in dynamic_specs:
                    parent_present = not parent_constraint or all(
                        part in source_text for part in parent_constraint.strip("/").split("/")
                    )
                    if parent_present and prefix in line and tail in line:
                        hits[(report["report_id"], "DYNAMIC_PREFIX_EXTENSION")].append(
                            _match_payload(source_path, line_number, line, "DYNAMIC_PREFIX_EXTENSION")
                        )

    records: list[dict[str, Any]] = []
    for report in reports:
        for query_type in QUERY_TYPES:
            matches = _dedupe(hits[(report["report_id"], query_type)])
            if not matches:
                result_status = "ZERO_RESULT_PROOF"
            elif query_type == "EXACT_STEM" and not any(
                match["source_class"] == "ACTIVE_SOURCE"
                for strong_type in ("EXACT_RELATIVE_PATH", "EXACT_BASENAME")
                for match in hits[(report["report_id"], strong_type)]
            ):
                result_status = "AMBIGUOUS_REFERENCE"
            else:
                result_status = "FOUND_REFERENCE"
            if query_type == "EXACT_RELATIVE_PATH":
                query_value: Any = report["relative_path"]
            elif query_type == "EXACT_BASENAME":
                query_value = report["filename"]
            elif query_type == "EXACT_STEM":
                query_value = Path(report["filename"]).stem
            elif query_type == "DYNAMIC_PREFIX_EXTENSION":
                query_value = _dynamic_parts(report["relative_path"])
            else:
                query_value = {"path": report["relative_path"], "basename": report["filename"]}
            scan_id = stable_id(
                "backstop-scan",
                report["report_id"],
                query_type,
                query_value,
                result_status,
                *(f"{item['source_path']}:{item['line']}:{item['excerpt_sha256']}" for item in matches),
            )
            records.append(
                {
                    "scan_id": scan_id,
                    "report_id": report["report_id"],
                    "report_path": report["relative_path"],
                    "query_type": query_type,
                    "query": query_value,
                    "result_status": result_status,
                    "result_count": len(matches),
                    "matches": matches,
                    "scanner": "BACKSTOP",
                    "scanner_version": context.config["backstop_scanner_version"],
                    "source_tree_commit": context.source_tree_commit,
                }
            )
    return sorted(records, key=lambda item: item["scan_id"])
