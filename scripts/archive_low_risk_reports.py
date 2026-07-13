"""Archive low-risk historical reports.

This script only moves report files from reports/ to reports/archive/.
It keeps latest/current reports and known dashboard/App/weekly dependencies in
place. It does not touch data, positions, trades, strategy code, or credentials.
"""

from __future__ import annotations

import csv
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "reports"
ARCHIVE_DIR = REPORT_DIR / "archive"
SCAN_DIRS = ["src", "scripts", "dashboard", "app/backend", "app/frontend/src"]

ARCHIVE_SUBDIRS = {
    "daily": ARCHIVE_DIR / "daily",
    "weekly": ARCHIVE_DIR / "weekly",
    "chatgpt_packets": ARCHIVE_DIR / "chatgpt_packets",
    "research_phases": ARCHIVE_DIR / "research_phases",
    "audit_history": ARCHIVE_DIR / "audit_history",
    "legacy_misc": ARCHIVE_DIR / "legacy_misc",
}

FORBIDDEN_NAMES = {
    "dashboard_data.json",
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
    "model_data_maturity_analysis.json",
    "model_data_maturity_analysis.md",
    "shadow_observation_weekly.json",
    "shadow_observation_weekly.md",
    "shadow_observation_weekly.csv",
}
CURRENT_PREFIXES = ("latest_",)
CURRENT_SUFFIXES = ("_latest.md", "_latest.json", "_latest.csv")
DATE_RE = re.compile(r"20\d{2}[-_]?\d{2}[-_]?\d{2}")
CHATGPT_DATED_RE = re.compile(r"^chatgpt_weekly_analysis_packet_20\d{2}-\d{2}-\d{2}\.(md|json)$")
DAILY_DATED_RE = re.compile(r"^(daily_signal|daily_report|daily_summary|daily_update)_20\d{2}-\d{2}-\d{2}\.(md|json|csv)$")
WEEKLY_DATED_RE = re.compile(r"^weekly_(review|report|summary)_20\d{2}-\d{2}-\d{2}\.(md|json|csv)$")
COMPACT_DATE_RE = re.compile(r"20\d{6}")


@dataclass
class Candidate:
    path: str
    target_path: str
    category: str
    reason: str
    dependency_count: int
    is_latest: bool
    is_dashboard_dependency: bool
    is_app_dependency: bool
    move_allowed: bool
    move_decision: str


def rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def read_json(path: Path) -> dict:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_file_classification() -> dict[str, dict]:
    path = REPORT_DIR / "file_classification_plan.csv"
    if not path.exists():
        return {}
    rows: dict[str, dict] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows[row["path"]] = row
    return rows


def code_text_by_domain() -> dict[str, str]:
    buckets = {"all": "", "dashboard": "", "app": "", "weekly": ""}
    for directory in SCAN_DIRS:
        root = PROJECT_ROOT / directory
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "node_modules" in path.parts or "__pycache__" in path.parts:
                continue
            if path.suffix.lower() not in {".py", ".sh", ".jsx", ".js", ".ts", ".tsx", ".html", ".css", ".md"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            relative = rel(path)
            buckets["all"] += "\n" + text
            if relative.startswith("dashboard/"):
                buckets["dashboard"] += "\n" + text
            if relative.startswith("app/"):
                buckets["app"] += "\n" + text
            if relative == "scripts/run_weekly_review.sh":
                buckets["weekly"] += "\n" + text
    return buckets


def is_latest_or_current(name: str) -> bool:
    return name.startswith(CURRENT_PREFIXES) or name.endswith(CURRENT_SUFFIXES) or name in FORBIDDEN_NAMES


def target_for(path: Path) -> tuple[str, Path, str]:
    name = path.name
    if CHATGPT_DATED_RE.match(name) or name.startswith("chatgpt_") and DATE_RE.search(name):
        return "CHATGPT_DATED", ARCHIVE_SUBDIRS["chatgpt_packets"] / name, "历史日期版 ChatGPT / Main 分析包。"
    if DAILY_DATED_RE.match(name) or name.startswith("daily_") and DATE_RE.search(name):
        return "DAILY_DATED", ARCHIVE_SUBDIRS["daily"] / name, "历史日期版 daily 报告。"
    if WEEKLY_DATED_RE.match(name) or name.startswith("weekly_") and DATE_RE.search(name):
        return "WEEKLY_DATED", ARCHIVE_SUBDIRS["weekly"] / name, "历史日期版 weekly 报告。"
    if DATE_RE.search(name) or COMPACT_DATE_RE.search(name):
        return "DATED_MISC", ARCHIVE_SUBDIRS["legacy_misc"] / name, "带日期的历史报告或修复记录。"
    phase_prefixes = ("phase1_", "phase2", "phase3", "phase4", "app_upgrade_", "app_release_", "app_polish_")
    if name.startswith(phase_prefixes):
        return "RESEARCH_PHASE", ARCHIVE_SUBDIRS["research_phases"] / name, "旧阶段研究/发布报告。"
    return "NOT_CANDIDATE", path, "不是本轮低风险归档候选。"


def report_root_files() -> list[Path]:
    return sorted(
        [path for path in REPORT_DIR.iterdir() if path.is_file() and path.name != ".gitkeep"],
        key=lambda p: p.name,
    )


def build_candidates() -> list[Candidate]:
    classification = read_file_classification()
    text = code_text_by_domain()
    candidates: list[Candidate] = []
    for path in report_root_files():
        relative = rel(path)
        name = path.name
        category, target, base_reason = target_for(path)
        is_latest = is_latest_or_current(name)
        class_row = classification.get(relative, {})
        dependency_count = int(float(class_row.get("dependency_count") or 0))
        referenced = relative in text["all"] or name in text["all"]
        dashboard_dep = relative in text["dashboard"] or name in text["dashboard"]
        app_dep = relative in text["app"] or name in text["app"]
        weekly_dep = relative in text["weekly"] or name in text["weekly"]
        if is_latest:
            decision = "KEEP_IN_PLACE"
            allowed = False
            reason = "latest/current 或明确禁止移动的活跃报告。"
        elif category == "NOT_CANDIDATE":
            decision = "UNKNOWN_KEEP"
            allowed = False
            reason = base_reason
        elif dependency_count or referenced or dashboard_dep or app_dep or weekly_dep:
            decision = "KEEP_IN_PLACE"
            allowed = False
            reason = f"{base_reason} 但扫描到代码或看板/App/weekly 引用，保留原位。"
        else:
            decision = "MOVE_TO_ARCHIVE"
            allowed = True
            reason = base_reason
        candidates.append(
            Candidate(
                path=relative,
                target_path=rel(target) if target.is_relative_to(PROJECT_ROOT) else str(target),
                category=category,
                reason=reason,
                dependency_count=dependency_count,
                is_latest=is_latest,
                is_dashboard_dependency=dashboard_dep,
                is_app_dependency=app_dep,
                move_allowed=allowed,
                move_decision=decision,
            )
        )
    return candidates


def manifest(name: str, moved: list[Candidate] | None = None) -> dict:
    report_files = report_root_files()
    archive_files = [path for path in ARCHIVE_DIR.rglob("*") if path.is_file()] if ARCHIVE_DIR.exists() else []
    moved = moved or []
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reports_root_file_count": len(report_files),
        "archive_file_count": len(archive_files),
        "moved_count": len(moved),
        "moved_files": [item.__dict__ for item in moved],
        "latest_retained": {
            name: (REPORT_DIR / name).exists()
            for name in [
                "dashboard_data.json",
                "latest_brief.md",
                "latest_paper_portfolio.md",
                "chatgpt_weekly_analysis_packet_latest.md",
                "chatgpt_weekly_analysis_packet_latest.json",
            ]
        },
    }


def write_manifest_md(path: Path, payload: dict, title: str) -> None:
    moved_lines = "\n".join(
        f"- `{item['path']}` -> `{item['target_path']}`：{item['reason']}"
        for item in payload.get("moved_files", [])
    ) or "- 本 manifest 阶段尚未移动文件。"
    latest_lines = "\n".join(
        f"- `{key}`: {'exists' if value else 'missing'}"
        for key, value in payload.get("latest_retained", {}).items()
    )
    path.write_text(
        f"""# {title}

生成时间：{payload['generated_at']}

## 统计

- reports 根目录文件数：{payload['reports_root_file_count']}
- archive 文件数：{payload['archive_file_count']}
- 本轮移动文件数：{payload['moved_count']}

## latest/current 保留检查

{latest_lines}

## 移动记录

{moved_lines}
""",
        encoding="utf-8",
    )


def write_candidate_reports(candidates: list[Candidate]) -> None:
    rows = [item.__dict__ for item in candidates]
    fields = [
        "path",
        "target_path",
        "category",
        "reason",
        "dependency_count",
        "is_latest",
        "is_dashboard_dependency",
        "is_app_dependency",
        "move_allowed",
        "move_decision",
    ]
    write_csv(REPORT_DIR / "archive_candidate_list.csv", rows, fields)
    write_json(
        REPORT_DIR / "archive_candidate_list.json",
        {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(rows),
            "move_to_archive": sum(1 for row in rows if row["move_decision"] == "MOVE_TO_ARCHIVE"),
            "keep_in_place": sum(1 for row in rows if row["move_decision"] == "KEEP_IN_PLACE"),
            "unknown_keep": sum(1 for row in rows if row["move_decision"] == "UNKNOWN_KEEP"),
            "rows": rows,
        },
    )
    move_lines = "\n".join(f"- `{item.path}` -> `{item.target_path}`：{item.reason}" for item in candidates if item.move_allowed) or "- 暂无。"
    keep_lines = "\n".join(f"- `{item.path}`：{item.reason}" for item in candidates if item.move_decision != "MOVE_TO_ARCHIVE")[:20000]
    (REPORT_DIR / "archive_candidate_list.md").write_text(
        f"""# Archive Candidate List

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

> 本清单只针对 `reports/` 根目录文件；latest/current、dashboard/App/weekly 依赖文件保留原位。

## 统计

- 候选总数：{len(candidates)}
- MOVE_TO_ARCHIVE：{sum(1 for item in candidates if item.move_decision == 'MOVE_TO_ARCHIVE')}
- KEEP_IN_PLACE：{sum(1 for item in candidates if item.move_decision == 'KEEP_IN_PLACE')}
- UNKNOWN_KEEP：{sum(1 for item in candidates if item.move_decision == 'UNKNOWN_KEEP')}

## 本轮允许移动

{move_lines}

## 保留原位或待复核样例

{keep_lines or '- 暂无。'}
""",
        encoding="utf-8",
    )


def move_candidates(candidates: list[Candidate]) -> list[Candidate]:
    moved: list[Candidate] = []
    for item in candidates:
        if not item.move_allowed:
            continue
        source = PROJECT_ROOT / item.path
        target = PROJECT_ROOT / item.target_path
        if not source.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            suffix = source.suffix
            stem = source.stem
            counter = 1
            while target.exists():
                target = target.parent / f"{stem}__dup{counter}{suffix}"
                counter += 1
        shutil.move(str(source), str(target))
        item.target_path = rel(target)
        moved.append(item)
    return moved


def append_index_notes(moved: list[Candidate]) -> None:
    archive_note = f"""

## 历史报告归档说明

最近一次低风险归档时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

- 历史报告目录：`reports/archive/`
- daily 历史报告：`reports/archive/daily/`
- weekly 历史报告：`reports/archive/weekly/`
- ChatGPT/Main 历史分析包：`reports/archive/chatgpt_packets/`
- 旧阶段研究/发布报告：`reports/archive/research_phases/`
- 其他日期版历史记录：`reports/archive/legacy_misc/`
- latest/current 活跃报告仍保留在 `reports/` 根目录。
- 本轮归档移动文件数：{len(moved)}
"""
    for path in [PROJECT_ROOT / "PROJECT_INDEX.md", PROJECT_ROOT / "docs" / "project_file_map.md", REPORT_DIR / "report_index.md"]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        marker = "## 历史报告归档说明"
        if marker in text:
            text = text.split(marker)[0].rstrip() + "\n"
        path.write_text(text.rstrip() + archive_note, encoding="utf-8")


def refresh_report_index() -> None:
    rows = []
    for path in report_root_files():
        rows.append(
            {
                "path": rel(path),
                "suffix": path.suffix.lower() or "[no_ext]",
                "size_bytes": path.stat().st_size,
            }
        )
    archive_files = sorted([path for path in ARCHIVE_DIR.rglob("*") if path.is_file()]) if ARCHIVE_DIR.exists() else []
    write_json(
        REPORT_DIR / "report_index.json",
        {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "reports_root_file_count": len(rows),
            "archive_file_count": len(archive_files),
            "rows": rows,
            "archive_rows": [{"path": rel(path), "size_bytes": path.stat().st_size} for path in archive_files],
        },
    )
    latest = [
        "dashboard_data.json",
        "latest_brief.md",
        "latest_paper_portfolio.md",
        "latest_data_health.md",
        "latest_data_coverage.md",
        "buy_signal_ranking.md",
        "sell_signal_review.md",
        "chatgpt_weekly_analysis_packet_latest.md",
        "chatgpt_weekly_analysis_packet_latest.json",
    ]
    latest_lines = "\n".join(f"- `{name}`" for name in latest if (REPORT_DIR / name).exists())
    archive_lines = "\n".join(f"- `{rel(path)}`" for path in archive_files[:120]) or "- 暂无。"
    suffix_counts: dict[str, int] = {}
    for row in rows:
        suffix_counts[row["suffix"]] = suffix_counts.get(row["suffix"], 0) + 1
    suffix_lines = "\n".join(f"- `{key}`: {value}" for key, value in sorted(suffix_counts.items()))
    (REPORT_DIR / "report_index.md").write_text(
        f"""# Report Index

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 摘要

- reports 根目录文件数：{len(rows)}
- archive 文件数：{len(archive_files)}

## 根目录文件类型统计

{suffix_lines}

## 活跃 latest/current 报告

{latest_lines}

## 历史报告归档位置

- `reports/archive/daily/`
- `reports/archive/weekly/`
- `reports/archive/chatgpt_packets/`
- `reports/archive/research_phases/`
- `reports/archive/audit_history/`
- `reports/archive/legacy_misc/`

## 已归档文件样例

{archive_lines}
""",
        encoding="utf-8",
    )


def main() -> None:
    if "--refresh-index-only" in sys.argv:
        refresh_report_index()
        print("Report index refreshed.")
        return
    for directory in ARCHIVE_SUBDIRS.values():
        directory.mkdir(parents=True, exist_ok=True)
    before = manifest("before")
    write_json(REPORT_DIR / "archive_manifest_before.json", before)
    write_manifest_md(REPORT_DIR / "archive_manifest_before.md", before, "Archive Manifest Before")
    candidates = build_candidates()
    write_candidate_reports(candidates)
    moved = move_candidates(candidates)
    append_index_notes(moved)
    refresh_report_index()
    after = manifest("after", moved)
    write_json(REPORT_DIR / "archive_manifest_after.json", after)
    write_manifest_md(REPORT_DIR / "archive_manifest_after.md", after, "Archive Manifest After")
    print(f"Archive candidates: {len(candidates)}")
    print(f"Moved to archive: {len(moved)}")


if __name__ == "__main__":
    main()
