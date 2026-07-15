from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import RunContext, posix_relative, read_text_lossy, sha256_bytes, source_files, stable_id


DATE_IN_NAME = re.compile(r"20\d{2}[-_]?[01]\d[-_]?[0-3]\d")


def _keys(report_path: str) -> list[tuple[str, str]]:
    filename = Path(report_path).name
    values: list[tuple[str, str]] = [
        (report_path, "EXACT_RELATIVE_PATH"),
        (f"../{report_path}", "PARENT_RELATIVE_PATH"),
        (filename, "EXACT_BASENAME"),
    ]
    match = DATE_IN_NAME.search(filename)
    if match:
        prefix = filename[: match.start()]
        suffix = Path(filename).suffix
        if len(prefix) >= 5:
            values.append((f"{prefix}*{suffix}", "DYNAMIC_PREFIX_EXTENSION"))
    return values


def scan_backstop_references(context: RunContext, reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Independent text engine; it does not consume structured scanner output."""
    records: dict[str, dict[str, Any]] = {}
    report_keys = [(report, _keys(report["relative_path"])) for report in reports]
    for path in source_files(context):
        source_path = posix_relative(path, context.root)
        for line_number, line in enumerate(read_text_lossy(path).splitlines(), 1):
            for report, keys in report_keys:
                for search_key, match_kind in keys:
                    if match_kind == "DYNAMIC_PREFIX_EXTENSION":
                        prefix, extension = search_key.split("*", 1)
                        matched = prefix in line and extension in line
                    else:
                        matched = search_key in line
                    if not matched:
                        continue
                    excerpt = line.strip()[:500]
                    reference_id = stable_id(
                        "backstop-ref", report["report_id"], source_path, line_number, match_kind, search_key
                    )
                    records[reference_id] = {
                        "reference_id": reference_id,
                        "report_id": report["report_id"],
                        "report_path": report["relative_path"],
                        "source_path": source_path,
                        "line": line_number,
                        "excerpt": excerpt,
                        "excerpt_sha256": sha256_bytes(excerpt.encode("utf-8")),
                        "reference_kind": "BACKSTOP_TEXT_MATCH",
                        "match_kind": match_kind,
                        "direction": "REFERENCE",
                        "search_key": search_key,
                        "scanner": "BACKSTOP",
                        "scanner_version": context.config["backstop_scanner_version"],
                    }
    return [records[key] for key in sorted(records)]
