"""Generate project structure and path dependency audit reports.

This is a read-only hygiene helper for project organization. It does not move
files, delete files, read secrets, change trading rules, or touch paper trades.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "reports"
DOCS_DIR = PROJECT_ROOT / "docs"

IGNORE_DIR_NAMES = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}
TREE_IGNORE_DIRS = IGNORE_DIR_NAMES | {"app/frontend/dist"}
SCAN_DIRS = ["src", "scripts", "dashboard", "app/backend", "app/frontend/src"]
DEPENDENCY_PATTERNS = [
    "reports/",
    "data/",
    "dashboard/",
    "app/",
    "paper_trades.csv",
    "paper_positions.csv",
    "dashboard_data.json",
    "chatgpt_weekly_analysis_packet_latest",
    "paper_performance_summary",
    "portfolio_exposure",
    "position_review_state",
    "profit_protection_preview",
    "high_beta_risk_watch",
    "broad_base_balance_preview",
]
LOCKED_PATHS = {
    "data/paper_trades.csv",
    "data/paper_positions.csv",
    "data/etf_daily",
    "reports/dashboard_data.json",
    "dashboard/index.html",
    "dashboard/build_dashboard.py",
    "app/backend/main.py",
    "app/backend/readers.py",
    "app/backend/safe_tasks.py",
    "src/paper_trade_engine.py",
    "watchlist.csv",
    "scripts/run_daily_close.sh",
    "scripts/run_weekly_review.sh",
    "scripts/run_app.sh",
}
LATEST_REPORT_PREFIXES = ("latest_",)
CURRENT_REPORT_NAMES = {
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
    "chatgpt_weekly_analysis_packet_latest.md",
    "chatgpt_weekly_analysis_packet_latest.json",
}


@dataclass
class ClassifiedFile:
    path: str
    category: str
    move_safety: str
    recommended_action: str
    reason: str
    dependency_count: int
    can_archive: bool
    requires_code_change: bool


def rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def is_ignored(path: Path) -> bool:
    parts = set(path.relative_to(PROJECT_ROOT).parts)
    return bool(parts & IGNORE_DIR_NAMES)


def should_skip_tree(path: Path) -> bool:
    relative = rel(path) if path != PROJECT_ROOT else ""
    if path.name in IGNORE_DIR_NAMES:
        return True
    return relative in TREE_IGNORE_DIRS


def iter_files() -> Iterable[Path]:
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if is_ignored(path):
            continue
        if path.name == ".DS_Store":
            continue
        yield path


def count_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file() and not is_ignored(path))


def build_tree_lines(max_depth: int = 2) -> list[str]:
    lines: list[str] = []

    def walk(path: Path, depth: int) -> None:
        if depth > max_depth or should_skip_tree(path):
            return
        if path == PROJECT_ROOT:
            label = "."
        else:
            label = path.name + ("/" if path.is_dir() else "")
        indent = "  " * depth
        if path != PROJECT_ROOT:
            suffix = ""
            if path.is_dir():
                suffix = f" ({count_files(path)} files)"
            lines.append(f"{indent}- {label}{suffix}")
        if path.is_dir():
            children = sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
            for child in children:
                if child.name == ".DS_Store":
                    continue
                walk(child, depth + 1)

    walk(PROJECT_ROOT, 0)
    return lines


def extension_counts(paths: Iterable[Path]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for path in paths:
        suffix = path.suffix.lower() or "[no_ext]"
        counts[suffix] += 1
    return dict(sorted(counts.items()))


def scan_dependencies() -> tuple[list[dict], dict[str, int], dict[str, int]]:
    rows: list[dict] = []
    by_path: Counter[str] = Counter()
    by_pattern: Counter[str] = Counter()
    for directory in SCAN_DIRS:
        root = PROJECT_ROOT / directory
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or is_ignored(path):
                continue
            if rel(path) == "scripts/project_hygiene_audit.py":
                continue
            if path.suffix.lower() not in {".py", ".sh", ".jsx", ".js", ".ts", ".tsx", ".html", ".css", ".md"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                for pattern in DEPENDENCY_PATTERNS:
                    if pattern in line:
                        entry = {
                            "file": rel(path),
                            "line": line_no,
                            "pattern": pattern,
                            "snippet": line.strip()[:240],
                        }
                        rows.append(entry)
                        by_path[rel(path)] += 1
                        by_pattern[pattern] += 1
    return rows, dict(by_path), dict(by_pattern)


def classify_file(path: Path, dependency_count: int) -> ClassifiedFile:
    relative = rel(path)
    name = path.name
    suffix = path.suffix.lower()
    parts = relative.split("/")
    top = parts[0]

    category = "UNKNOWN_NEEDS_REVIEW"
    move_safety = "UNKNOWN_NEEDS_REVIEW"
    action = "人工复核后再决定"
    reason = "未命中明确分类规则。"
    can_archive = False
    requires_code_change = False

    if relative in LOCKED_PATHS or any(relative.startswith(f"{locked}/") for locked in LOCKED_PATHS):
        category = "DATA_CORE" if top == "data" else "CORE_CODE"
        move_safety = "LOCKED"
        action = "保持原路径"
        reason = "被运行链路或安全边界直接依赖。"
    elif top == "src":
        research_keywords = ("research", "preview", "shadow", "backtest", "factor", "model", "alpha", "quality", "hygiene")
        if any(key in name for key in research_keywords):
            category = "RESEARCH_CODE"
        elif any(key in name for key in ("risk", "review", "valuation", "performance", "exposure")):
            category = "RESEARCH_CODE"
        else:
            category = "CORE_CODE"
        move_safety = "MOVE_ONLY_WITH_CODE_UPDATE"
        action = "先配置化 import 和路径，再考虑迁移到 src 子包"
        reason = "Python 模块可能被脚本、App 或 dashboard 直接导入。"
        requires_code_change = True
    elif top == "scripts":
        if name.startswith("run_") or name in {"install_launchd_jobs.sh", "uninstall_launchd_jobs.sh", "run_app.sh"}:
            category = "SCRIPTS_RUNTIME"
            move_safety = "DO_NOT_MOVE"
            action = "保持原路径"
            reason = "launchd、App 或用户命令可能直接调用。"
        else:
            category = "SCRIPTS_MAINTENANCE"
            move_safety = "MOVE_ONLY_WITH_CODE_UPDATE"
            action = "后续可整理到 scripts/maintenance 或 scripts/data"
            reason = "维护脚本可整理，但需要更新 README/调用路径。"
            requires_code_change = True
    elif top == "app":
        category = "APP_CODE"
        move_safety = "DO_NOT_MOVE" if "dist" not in parts else "MOVE_ONLY_WITH_CODE_UPDATE"
        action = "保持 App 现有结构"
        reason = "FastAPI/Vite/Tauri 路径依赖较多。"
        requires_code_change = "dist" not in parts
    elif top == "dashboard":
        category = "DASHBOARD_CODE"
        move_safety = "DO_NOT_MOVE"
        action = "保持 dashboard 入口稳定"
        reason = "静态看板和 App 数据快照依赖固定路径。"
    elif top == "data":
        if relative.startswith("data/etf_daily/") or name in {"paper_trades.csv", "paper_positions.csv"}:
            category = "DATA_CORE"
            move_safety = "LOCKED"
            action = "保持原路径"
            reason = "正式行情或模拟盘核心账本。"
        elif relative.startswith("data/staging/") or name.endswith("_tracking.csv") or name.startswith("paper_equity_curve"):
            category = "DATA_DERIVED"
            move_safety = "MOVE_ONLY_WITH_CODE_UPDATE"
            action = "可在后续迁移到 data/derived 或 data/paper，但先不要动"
            reason = "派生数据可能被报告和 App 读取。"
            requires_code_change = True
        else:
            category = "DATA_DERIVED"
            move_safety = "UNKNOWN_NEEDS_REVIEW"
            action = "先保留，后续按来源归档"
            reason = "数据文件需要确认是否仍被脚本使用。"
    elif top == "reports":
        if name.startswith(LATEST_REPORT_PREFIXES) or name in CURRENT_REPORT_NAMES:
            category = "REPORT_CURRENT"
            move_safety = "DO_NOT_MOVE"
            action = "保持原路径"
            reason = "latest/current 报告被 dashboard/App/周报读取。"
        elif re.search(r"20\d{2}-\d{2}-\d{2}", name) or name.startswith(("daily_signal_", "weekly_review_", "chatgpt_report_summary_", "chatgpt_analysis_packet_")):
            category = "REPORT_ARCHIVE"
            move_safety = "SAFE_TO_ARCHIVE"
            action = "Phase B 可归档到 reports/archive/"
            reason = "日期版或历史摘要，保留 latest 路径即可。"
            can_archive = True
        else:
            category = "REPORT_CURRENT"
            move_safety = "MOVE_ONLY_WITH_CODE_UPDATE" if dependency_count else "SAFE_TO_ARCHIVE"
            action = "先加入 report_index；确认无读取依赖后可分类归档"
            reason = "研究/审计报告较多，部分可能被 dashboard_links 引用。"
            can_archive = dependency_count == 0
            requires_code_change = dependency_count > 0
    elif top == "docs":
        category = "DOCS"
        move_safety = "SAFE_TO_ARCHIVE"
        action = "可按 user_guides/technical/rules 逐步整理"
        reason = "文档迁移风险较低，但 README 链接需同步。"
        can_archive = False
    elif top in {"dist", "desktop", "assets"} or name.endswith(".command"):
        category = "DIST_ASSETS"
        move_safety = "DO_NOT_MOVE"
        action = "保持 App 包装器和图标路径"
        reason = "桌面启动器和打包资源可能依赖固定路径。"
    elif top == "logs":
        category = "LOGS"
        move_safety = "SAFE_TO_ARCHIVE"
        action = "可按日期滚动归档或忽略提交"
        reason = "日志不是核心输入。"
        can_archive = True
    elif name in {".DS_Store", "=2.31.0"} or relative in {"trades.csv", "weekly_review.md"}:
        category = "TEMP_OR_LEGACY"
        move_safety = "UNKNOWN_NEEDS_REVIEW"
        action = "列入候选清理清单，确认后再处理"
        reason = "根目录疑似临时或旧版文件。"
    elif suffix in {".md", ".txt"}:
        category = "DOCS"
        move_safety = "SAFE_TO_ARCHIVE"
        action = "可整理进 docs 或保留根目录索引"
        reason = "文档类文件，迁移需更新链接。"

    if dependency_count and move_safety == "SAFE_TO_ARCHIVE":
        move_safety = "MOVE_ONLY_WITH_CODE_UPDATE"
        requires_code_change = True
        action = "存在路径引用，先改引用再移动"
        reason += " 当前扫描发现硬编码引用。"

    return ClassifiedFile(
        path=relative,
        category=category,
        move_safety=move_safety,
        recommended_action=action,
        reason=reason,
        dependency_count=dependency_count,
        can_archive=can_archive,
        requires_code_change=requires_code_change,
    )


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def bullet(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def generate_reports() -> None:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_files = list(iter_files())
    dependency_rows, dependency_by_path, dependency_by_pattern = scan_dependencies()
    classified = [classify_file(path, dependency_by_path.get(rel(path), 0)) for path in all_files]

    top_dirs = [item for item in PROJECT_ROOT.iterdir() if item.is_dir() and item.name not in IGNORE_DIR_NAMES]
    root_files = [item for item in PROJECT_ROOT.iterdir() if item.is_file() and item.name != ".DS_Store"]
    report_files = list((PROJECT_ROOT / "reports").glob("*")) if (PROJECT_ROOT / "reports").exists() else []
    report_regular_files = [path for path in report_files if path.is_file()]
    src_files = list((PROJECT_ROOT / "src").glob("*.py")) if (PROJECT_ROOT / "src").exists() else []
    scripts_files = [path for path in (PROJECT_ROOT / "scripts").iterdir() if path.is_file()] if (PROJECT_ROOT / "scripts").exists() else []
    data_files = list((PROJECT_ROOT / "data").glob("*")) if (PROJECT_ROOT / "data").exists() else []
    etf_daily_count = len(list((PROJECT_ROOT / "data" / "etf_daily").glob("*.csv")))

    classification_counts = Counter(item.category for item in classified)
    safety_counts = Counter(item.move_safety for item in classified)
    archive_candidates = [item for item in classified if item.can_archive]
    locked = [item for item in classified if item.move_safety in {"LOCKED", "DO_NOT_MOVE"}]
    temp_candidates = [item for item in classified if item.category == "TEMP_OR_LEGACY"]

    structure_payload = {
        "generated_at": generated_at,
        "project_root": str(PROJECT_ROOT),
        "tree_max_depth": 2,
        "ignored": sorted(TREE_IGNORE_DIRS),
        "top_level_directories": sorted(path.name for path in top_dirs),
        "top_level_files": sorted(path.name for path in root_files if path.name != ".env"),
        "secret_files_detected_but_not_read": [".env"] if (PROJECT_ROOT / ".env").exists() else [],
        "counts": {
            "total_files_excluding_ignored": len(all_files),
            "top_level_directories": len(top_dirs),
            "top_level_files": len(root_files),
            "reports_files": len(report_regular_files),
            "reports_md": sum(1 for path in report_regular_files if path.suffix == ".md"),
            "reports_json": sum(1 for path in report_regular_files if path.suffix == ".json"),
            "reports_csv": sum(1 for path in report_regular_files if path.suffix == ".csv"),
            "src_py_top_level": len(src_files),
            "scripts_files": len(scripts_files),
            "data_etf_daily_csv": etf_daily_count,
            "app_frontend_dist_exists": (PROJECT_ROOT / "app" / "frontend" / "dist" / "index.html").exists(),
            "dashboard_index_exists": (PROJECT_ROOT / "dashboard" / "index.html").exists(),
        },
        "file_extensions": extension_counts(all_files),
        "classification_counts": dict(classification_counts),
        "move_safety_counts": dict(safety_counts),
        "temp_or_legacy_candidates": [item.path for item in temp_candidates[:80]],
        "archive_candidates_sample": [item.path for item in archive_candidates[:80]],
    }
    write_json(REPORT_DIR / "project_structure_audit.json", structure_payload)

    tree_lines = build_tree_lines()
    structure_md = f"""# Project Structure Audit

生成时间：{generated_at}

> 本报告只做文件结构审计和整理建议；未移动、未删除、未修改交易规则。

## 摘要

- 项目根目录：`{PROJECT_ROOT}`
- 忽略目录：`{', '.join(sorted(TREE_IGNORE_DIRS))}`
- 统计文件数：{len(all_files)}
- `reports/` 文件数：{len(report_regular_files)}，其中 md {structure_payload['counts']['reports_md']}、json {structure_payload['counts']['reports_json']}、csv {structure_payload['counts']['reports_csv']}
- `src/` 顶层 Python 模块数：{len(src_files)}
- `scripts/` 顶层脚本数：{len(scripts_files)}
- `data/etf_daily/` ETF CSV 数：{etf_daily_count}
- `dashboard/index.html`：{'exists' if structure_payload['counts']['dashboard_index_exists'] else 'missing'}
- `app/frontend/dist/index.html`：{'exists' if structure_payload['counts']['app_frontend_dist_exists'] else 'missing'}

## 当前目录树摘要

```text
{chr(10).join(tree_lines)}
```

## 文件分类统计

{bullet(f"{key}: {value}" for key, value in sorted(classification_counts.items()))}

## 移动安全等级统计

{bullet(f"{key}: {value}" for key, value in sorted(safety_counts.items()))}

## 明显临时或疑似旧文件

{bullet(item.path for item in temp_candidates[:80]) or "- 暂无明确候选。"}

## 可归档候选样例

{bullet(item.path for item in archive_candidates[:80]) or "- 暂无明确候选。"}

## 安全说明

- 未读取 `.env` 内容；如存在，仅记录为 secret 文件存在。
- 未移动 `data/paper_trades.csv`、`data/paper_positions.csv`、`src/paper_trade_engine.py`。
- 未删除任何文件。
"""
    (REPORT_DIR / "project_structure_audit.md").write_text(structure_md, encoding="utf-8")

    dependency_payload = {
        "generated_at": generated_at,
        "scan_dirs": SCAN_DIRS,
        "patterns": DEPENDENCY_PATTERNS,
        "total_matches": len(dependency_rows),
        "by_pattern": dependency_by_pattern,
        "by_file": dependency_by_path,
        "matches": dependency_rows[:2000],
        "locked_paths": sorted(LOCKED_PATHS),
        "do_not_move_summary": [
            "data/paper_trades.csv",
            "data/paper_positions.csv",
            "data/etf_daily/",
            "reports/dashboard_data.json",
            "latest_* reports",
            "dashboard/index.html",
            "app/backend/main.py",
            "scripts/run_daily_close.sh",
            "scripts/run_weekly_review.sh",
        ],
    }
    write_json(REPORT_DIR / "path_dependency_audit.json", dependency_payload)
    top_dependency_files = sorted(dependency_by_path.items(), key=lambda item: item[1], reverse=True)[:40]
    dependency_md = f"""# Path Dependency Audit

生成时间：{generated_at}

> 扫描范围：`src/`、`scripts/`、`dashboard/`、`app/backend/`、`app/frontend/src/`。本报告用于判断哪些路径不能贸然移动。

## 扫描摘要

- 命中总数：{len(dependency_rows)}
- 命中文件数：{len(dependency_by_path)}
- 搜索模式：{', '.join(f'`{p}`' for p in DEPENDENCY_PATTERNS)}

## 按模式统计

{bullet(f"`{key}`: {value}" for key, value in sorted(dependency_by_pattern.items(), key=lambda item: item[1], reverse=True))}

## 路径依赖最多的文件

{bullet(f"`{path}`: {count}" for path, count in top_dependency_files)}

## 不能移动的路径

{bullet(dependency_payload['do_not_move_summary'])}

## 可以配置化后再移动的路径

- `src/` 模块：需要先整理 import 和入口脚本。
- `scripts/` 维护脚本：需要先更新 README、launchd、App safe task 白名单。
- `reports/` 研究类报告：需要先更新 `dashboard/build_dashboard.py` 的 report links 和 App readers。
- `data/` 派生文件：需要先明确是正式账本、shadow 账本还是临时 staging。

## Dashboard / App 固定读取重点

- `reports/dashboard_data.json`
- `reports/paper_performance_summary.json`
- `reports/portfolio_exposure.json`
- `reports/position_review_state.json`
- `reports/profit_protection_preview.json`
- `reports/high_beta_risk_watch.json`
- `reports/broad_base_balance_preview.json`
- `reports/chatgpt_weekly_analysis_packet_latest.json`

## Weekly Review 固定链路重点

- `scripts/run_weekly_review.sh`
- `src/main.py --weekly`
- `src/automation_nodes.py --node weekly_full_review`
- `src/holding_period_research.py`
- `src/exit_rule_research.py`
- `src/parameter_sweep.py`
- `src/persistence_breakout_shadow.py`
- `src/missed_opportunity_tracker.py`
- `src/shadow_observation_weekly.py`
- `src/trade_review.py`
- `src/chatgpt_weekly_packet.py`
- `dashboard/build_dashboard.py`
"""
    (REPORT_DIR / "path_dependency_audit.md").write_text(dependency_md, encoding="utf-8")

    classification_rows = [item.__dict__ for item in sorted(classified, key=lambda item: item.path)]
    fields = ["path", "category", "move_safety", "recommended_action", "reason", "dependency_count", "can_archive", "requires_code_change"]
    write_csv(REPORT_DIR / "file_classification_plan.csv", classification_rows, fields)
    write_json(
        REPORT_DIR / "file_classification_plan.json",
        {
            "generated_at": generated_at,
            "total_files": len(classification_rows),
            "category_counts": dict(classification_counts),
            "move_safety_counts": dict(safety_counts),
            "rows": classification_rows,
        },
    )
    classification_md = f"""# File Classification Plan

生成时间：{generated_at}

## 分类统计

{bullet(f"{key}: {value}" for key, value in sorted(classification_counts.items()))}

## 移动安全等级

{bullet(f"{key}: {value}" for key, value in sorted(safety_counts.items()))}

## LOCKED / DO_NOT_MOVE 样例

{bullet(item.path for item in locked[:120])}

## SAFE_TO_ARCHIVE 样例

{bullet(item.path for item in archive_candidates[:120]) or "- 暂无明确候选。"}

## 建议

- `CORE_CODE`、`DATA_CORE`、`SCRIPTS_RUNTIME`、`APP_CODE`、`DASHBOARD_CODE` 暂不移动。
- `REPORT_ARCHIVE` 可以作为 Phase B 低风险归档候选，但必须保留 latest/current 原路径。
- `RESEARCH_CODE` 和 `SCRIPTS_MAINTENANCE` 只有在路径配置化后再移动。
- `TEMP_OR_LEGACY` 只生成候选清单，不直接删除。
"""
    (REPORT_DIR / "file_classification_plan.md").write_text(classification_md, encoding="utf-8")

    recommended_layout = """# Recommended Project Layout

> 这是保守目标结构建议。本轮不迁移，只用于后续规划。

```text
a-share-swing-system/
  app/
  assets/
  dashboard/
  data/
    etf_daily/
    raw/
    derived/
    paper/
    staging/
  docs/
    user_guides/
    technical/
    rules/
  reports/
    latest/
    weekly/
    audit/
    research/
    preview/
    shadow/
    archive/
  scripts/
    runtime/
    maintenance/
    data/
    app/
  src/
    core/
    data/
    portfolio/
    research/
    preview/
    risk/
    reporting/
    app_support/
  dist/
  logs/
```

## 迁移成本评估

- `reports/` 分类成本最高：dashboard/App/周报都读取固定路径，必须先建立兼容层或 symlink/索引。
- `src/` 子包化成本高：大量脚本以 `python3 src/xxx.py` 方式运行。
- `scripts/` 子目录化成本中等：launchd、App safe task、README 都可能引用固定脚本名。
- `data/` 拆分成本中等偏高：核心账本和 ETF 日线不能动；派生文件可后续整理。
- `docs/` 整理成本低：主要是链接同步。

## 最低风险第一阶段

1. 保持所有核心入口原路径。
2. 新增索引文档和报告地图。
3. 在 `reports/` 中先标记归档候选，不移动 latest/current 报告。
4. 后续若移动，先让 dashboard/App 通过配置读取路径。
"""
    (REPORT_DIR / "recommended_project_layout.md").write_text(recommended_layout, encoding="utf-8")

    cleanup_roadmap = """# Project Cleanup Roadmap

## Phase A：零风险整理

- 新增 `PROJECT_INDEX.md`、`docs/project_file_map.md`、`reports/report_index.md`。
- 保持 `data/`、`reports/latest_*`、`dashboard/`、`app/`、`scripts/run_*` 原路径。
- 只生成文件地图、路径依赖审计和归档候选清单。
- 不删除、不移动、不改 import。

## Phase B：低风险归档

- 将日期版历史报告归档到 `reports/archive/`。
- 保留所有 latest/current 报告原路径。
- 每次归档前运行 dashboard build、App build、release check。
- 仅对 `SAFE_TO_ARCHIVE` 且无依赖的文件执行。

## Phase C：结构化重构

- 先做路径配置化：统一 report/data path registry。
- 再考虑 `src/` 子包化、`scripts/` 分类、`reports/` 分类目录。
- 迁移前必须有回滚清单和自动化验证。
- 不在主策略迭代和数据更新高峰期做大规模移动。

## 禁止项

- 不移动 `data/paper_trades.csv`、`data/paper_positions.csv`。
- 不移动 `data/etf_daily/`。
- 不移动 `reports/dashboard_data.json`。
- 不改 `src/paper_trade_engine.py`。
- 不删除核心文件。
"""
    (REPORT_DIR / "project_cleanup_roadmap.md").write_text(cleanup_roadmap, encoding="utf-8")

    report_index_rows = []
    for path in sorted(report_regular_files, key=lambda p: p.name):
        classified_item = next((item for item in classified if item.path == rel(path)), None)
        report_index_rows.append(
            {
                "path": rel(path),
                "suffix": path.suffix.lower() or "[no_ext]",
                "category": classified_item.category if classified_item else "",
                "move_safety": classified_item.move_safety if classified_item else "",
                "can_archive": classified_item.can_archive if classified_item else False,
                "size_bytes": path.stat().st_size,
            }
        )
    write_json(REPORT_DIR / "report_index.json", {"generated_at": generated_at, "rows": report_index_rows})
    report_index_md = f"""# Report Index

生成时间：{generated_at}

## 摘要

- 报告文件数：{len(report_index_rows)}
- Markdown：{structure_payload['counts']['reports_md']}
- JSON：{structure_payload['counts']['reports_json']}
- CSV：{structure_payload['counts']['reports_csv']}

## 关键 current/latest 报告

{bullet(path for path in sorted(CURRENT_REPORT_NAMES) if (REPORT_DIR / path).exists())}

## 归档候选样例

{bullet(row['path'] for row in report_index_rows if row['can_archive']) or "- 暂无明确候选。"}
"""
    (REPORT_DIR / "report_index.md").write_text(report_index_md, encoding="utf-8")

    project_index = f"""# A-share Swing System Project Index

生成时间：{generated_at}

## 当前阶段

项目处于 ETF 双周期模拟盘 + 研究观察层阶段。正式执行层仍保持模拟盘，不接券商 API，不真实下单。

## 核心入口

- App 后端：`app/backend/main.py`
- App 前端：`app/frontend/`
- 静态看板：`dashboard/index.html`
- 看板生成：`dashboard/build_dashboard.py`
- 每日收盘：`scripts/run_daily_close.sh`
- 每周复盘：`scripts/run_weekly_review.sh`
- 本地 App 启动：`打开量化研究控制台.command`

## 核心数据

- ETF 日线：`data/etf_daily/`
- 模拟交易流水：`data/paper_trades.csv`
- 模拟持仓：`data/paper_positions.csv`
- 看板数据：`reports/dashboard_data.json`

## 核心报告

- 每日摘要：`reports/latest_brief.md`
- 模拟盘：`reports/latest_paper_portfolio.md`
- BUY ranking：`reports/buy_signal_ranking.md`
- 卖出复核：`reports/sell_signal_review.md`
- 周报分析包：`reports/chatgpt_weekly_analysis_packet_latest.md`
- 数据健康：`reports/latest_data_health.md`
- 数据覆盖：`reports/latest_data_coverage.md`

## 不要随意移动

- `data/paper_trades.csv`
- `data/paper_positions.csv`
- `data/etf_daily/`
- `reports/dashboard_data.json`
- `dashboard/index.html`
- `app/backend/main.py`
- `scripts/run_daily_close.sh`
- `scripts/run_weekly_review.sh`
- `src/paper_trade_engine.py`

## 本轮审计报告

- `reports/project_structure_audit.md`
- `reports/path_dependency_audit.md`
- `reports/file_classification_plan.md`
- `reports/recommended_project_layout.md`
- `reports/project_cleanup_roadmap.md`
- `reports/report_index.md`
"""
    (PROJECT_ROOT / "PROJECT_INDEX.md").write_text(project_index, encoding="utf-8")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    file_map = f"""# Project File Map

生成时间：{generated_at}

## 目录职责

- `app/`：动态 App，FastAPI + React/Vite。
- `dashboard/`：静态只读看板生成和输出。
- `data/`：ETF 日线、模拟盘账本、staging 和派生跟踪数据。
- `reports/`：所有最新报告、研究报告、审计报告和历史归档候选。
- `scripts/`：运行脚本、数据维护脚本、App 启动脚本。
- `src/`：核心模型、报告、研究、风险观察和组合分析模块。
- `docs/`：用户指南、规则和技术说明。
- `dist/`、`desktop/`、`assets/`：桌面 App 包装器和图标资源。
- `logs/`：本地自动化日志。

## 文件移动原则

- 先审计，后配置化，再迁移。
- latest/current 报告先不移动。
- 模拟盘账本和正式 ETF 日线不移动。
- App / dashboard / launchd 入口不移动。
- 日期版历史报告可以作为第一批归档候选。

## 详细清单

- 结构审计：`reports/project_structure_audit.md`
- 路径依赖：`reports/path_dependency_audit.md`
- 文件分类：`reports/file_classification_plan.csv`
- 整理路线：`reports/project_cleanup_roadmap.md`
"""
    (DOCS_DIR / "project_file_map.md").write_text(file_map, encoding="utf-8")

    print("Generated project hygiene audit reports.")
    print(f"Structure: {REPORT_DIR / 'project_structure_audit.md'}")
    print(f"Dependencies: {REPORT_DIR / 'path_dependency_audit.md'}")
    print(f"Classification: {REPORT_DIR / 'file_classification_plan.csv'}")


def main() -> None:
    generate_reports()


if __name__ == "__main__":
    main()
