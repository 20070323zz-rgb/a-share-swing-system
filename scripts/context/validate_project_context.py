#!/usr/bin/env python3
"""Read-only project context validator.

The only write side effect is the latest validation report under reports/.
It does not fix context files, run models, update snapshots, or touch trading
state.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


MAIN_PHASE_STATES = {"NOT_STARTED", "IN_PROGRESS", "BLOCKED", "COMPLETE", "ABORTED"}
BATCH_STATES = {"PENDING", "IN_PROGRESS", "COMPLETE", "BLOCKED", "SKIPPED"}
VALIDATION_STATUSES = {"VALID", "VALID_WITH_WARNINGS", "INVALID"}
REQUIRED_PROTECTED_FILES = {
    "src/paper_trade_engine.py",
    "data/paper_trades.csv",
    "data/paper_positions.csv",
}
REQUIRED_STATUS_FIELDS = [
    "project",
    "repository_root",
    "context_schema_version",
    "context_updated_at",
    "context_updated_by",
    "context_update_reason",
    "main_phase",
    "main_phase_id",
    "phase_status",
    "current_batch",
    "current_batch_id",
    "current_batch_status",
    "completed_batches",
    "pending_batches",
    "blocked_batches",
    "skipped_batches",
    "last_completed_batch",
    "resume_from",
    "required_batches",
    "final_closeout_batch",
    "current_phase_report",
    "current_phase_decision",
    "next_research_phase",
    "formal_model_changed",
    "buy_ranking_changed",
    "market_regime_changed",
    "ready_for_fit_shadow_observation",
    "ready_for_adjusted_preview_research",
    "ready_for_preview",
    "ready_for_execution",
    "research_only",
    "execution_allowed",
    "protected_files",
    "status_sources",
    "phase_transition_history",
]
BOOLEAN_READINESS_FIELDS = [
    "ready_for_fit_shadow_observation",
    "ready_for_adjusted_preview_research",
    "ready_for_preview",
    "ready_for_execution",
    "execution_allowed",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z").strip()


def read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report exact validation failure
        errors.append(f"JSON 读取失败: {path}: {exc}")
        return {}


def safe_context_path(root: Path, text: str, errors: list[str]) -> Path | None:
    if text.startswith("/") or ".." in Path(text).parts:
        errors.append(f"context path escapes repository root: {text}")
        return None
    path = (root / text).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        errors.append(f"context path outside repository root: {text}")
        return None
    return path


def parse_date(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    if len(text) >= 10:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            return None
    return None


def has_nonfinite(value: Any) -> bool:
    if isinstance(value, dict):
        return any(has_nonfinite(v) for v in value.values())
    if isinstance(value, list):
        return any(has_nonfinite(v) for v in value)
    return isinstance(value, float) and (math.isnan(value) or math.isinf(value))


def validate_manifest(root: Path, errors: list[str], warnings: list[str]) -> tuple[dict[str, Any], dict[str, bool]]:
    manifest_path = root / "docs/project_context_manifest.json"
    manifest = read_json(manifest_path, errors)
    result = {
        "manifest_valid": False,
        "required_context_files_complete": False,
        "bootstrap_read_order_valid": False,
    }
    if not manifest:
        return manifest, result

    if manifest.get("schema_version") != 1:
        errors.append("manifest schema_version must be 1")
    required_files = manifest.get("required_context_files")
    read_order = manifest.get("bootstrap_read_order")
    if not isinstance(required_files, list):
        errors.append("manifest required_context_files must be a list")
        required_files = []
    if not isinstance(read_order, list):
        errors.append("manifest bootstrap_read_order must be a list")
        read_order = []

    missing_required = []
    for item in required_files:
        if not isinstance(item, dict):
            errors.append("manifest required_context_files item must be an object")
            continue
        path_text = str(item.get("path", ""))
        path = safe_context_path(root, path_text, errors)
        if path is None:
            continue
        if item.get("required") is True and not path.exists():
            missing_required.append(path_text)

    missing_order = []
    for path_text in read_order:
        path = safe_context_path(root, str(path_text), errors)
        if path is None:
            continue
        if not path.exists():
            missing_order.append(str(path_text))

    if missing_required:
        errors.append(f"required context files missing: {missing_required}")
    if missing_order:
        errors.append(f"bootstrap_read_order references missing files: {missing_order}")

    result["required_context_files_complete"] = not missing_required
    result["bootstrap_read_order_valid"] = bool(read_order) and not missing_order
    result["manifest_valid"] = (
        manifest.get("schema_version") == 1
        and isinstance(required_files, list)
        and isinstance(read_order, list)
        and result["required_context_files_complete"]
        and result["bootstrap_read_order_valid"]
    )
    if not read_order:
        warnings.append("bootstrap_read_order is empty")
    return manifest, result


def validate_status(root: Path, errors: list[str], warnings: list[str]) -> tuple[dict[str, Any], dict[str, bool]]:
    status = read_json(root / "docs/current_phase_status.json", errors)
    result = {
        "status_schema_valid": False,
        "main_phase_state_valid": False,
        "batch_state_valid": False,
        "phase_batch_consistent": False,
    }
    if not status:
        return status, result

    if status.get("schema_version") != 2:
        errors.append("current_phase_status.schema_version must be 2")
    if status.get("context_schema_version") != 2:
        errors.append("current_phase_status.context_schema_version must be 2")
    missing = [key for key in REQUIRED_STATUS_FIELDS if key not in status]
    if missing:
        errors.append(f"current_phase_status missing fields: {missing}")
    root_value = status.get("repository_root")
    root_matches = root_value in {"<project_root>", str(root)}
    if not root_matches:
        errors.append("repository_root mismatch")

    if has_nonfinite(status):
        errors.append("current_phase_status contains NaN or Infinity")

    for field in BOOLEAN_READINESS_FIELDS + ["research_only"]:
        if field in status and not isinstance(status.get(field), bool):
            errors.append(f"{field} must be a JSON boolean")

    result["main_phase_state_valid"] = status.get("phase_status") in MAIN_PHASE_STATES
    if status.get("phase_status") == "COMPLETE":
        result["batch_state_valid"] = status.get("current_batch_status") is None
    else:
        result["batch_state_valid"] = status.get("current_batch_status") in BATCH_STATES
    if not result["main_phase_state_valid"]:
        errors.append(f"invalid phase_status: {status.get('phase_status')}")
    if not result["batch_state_valid"]:
        errors.append(f"invalid current_batch_status: {status.get('current_batch_status')}")

    context_time = parse_date(status.get("context_updated_at"))
    if context_time is None:
        errors.append("context_updated_at is not parseable")

    phase_batch_ok = validate_phase_batch_consistency(status, errors)
    result["phase_batch_consistent"] = phase_batch_ok
    result["status_schema_valid"] = (
        status.get("schema_version") == 2
        and status.get("context_schema_version") == 2
        and not missing
        and result["main_phase_state_valid"]
        and result["batch_state_valid"]
        and phase_batch_ok
        and root_matches
    )
    if status.get("phase_status") == "IN_PROGRESS" and status.get("current_batch_status") == "PENDING":
        warnings.append("current batch is pending; resume from current_batch before doing substantive work")
    return status, result


def validate_phase_batch_consistency(status: dict[str, Any], errors: list[str]) -> bool:
    completed = set(status.get("completed_batches", []))
    pending = set(status.get("pending_batches", []))
    blocked = set(status.get("blocked_batches", []))
    skipped = set(status.get("skipped_batches", []))
    current = status.get("current_batch")
    current_status = status.get("current_batch_status")
    required = set(status.get("required_batches", []))

    ok = True
    overlap_pending = completed & pending
    overlap_blocked = completed & blocked
    if overlap_pending:
        errors.append(f"completed batches also pending: {sorted(overlap_pending)}")
        ok = False
    if overlap_blocked:
        errors.append(f"completed batches also blocked: {sorted(overlap_blocked)}")
        ok = False
    if current != status.get("resume_from"):
        errors.append("current_batch must equal resume_from for current phase")
        ok = False
    if status.get("phase_status") == "COMPLETE":
        for key in ["current_batch", "current_batch_id", "current_batch_status", "resume_from"]:
            if status.get(key) is not None:
                errors.append(f"phase COMPLETE requires {key}=null")
                ok = False
        if pending:
            errors.append("phase COMPLETE requires pending_batches=[]")
            ok = False
        if blocked:
            errors.append("phase COMPLETE requires blocked_batches=[]")
            ok = False
    if current_status == "PENDING" and current not in pending:
        errors.append("current_batch_status=PENDING but current_batch is not in pending_batches")
        ok = False
    if current_status == "COMPLETE" and current not in completed:
        errors.append("current_batch_status=COMPLETE but current_batch is not in completed_batches")
        ok = False

    explained = completed | pending | blocked | skipped | {current}
    missing_required = required - explained
    if missing_required:
        errors.append(f"required batches are unexplained: {sorted(missing_required)}")
        ok = False

    if status.get("phase_status") == "COMPLETE":
        final = status.get("final_closeout_batch")
        incomplete = required - completed - skipped
        if incomplete:
            errors.append(f"phase COMPLETE but required batches incomplete: {sorted(incomplete)}")
            ok = False
        if final not in completed:
            errors.append("phase COMPLETE but final_closeout_batch is not complete")
            ok = False
    return ok


def collect_decision_paths(root: Path, status: dict[str, Any], errors: list[str]) -> list[Path]:
    paths: list[Path] = []
    sources = status.get("status_sources", {})
    if isinstance(sources, dict):
        for items in sources.values():
            if not isinstance(items, list):
                continue
            for item in items:
                if not str(item).endswith(".json"):
                    continue
                path = safe_context_path(root, str(item), errors)
                if path and path not in paths:
                    paths.append(path)
    current_decision = status.get("current_phase_decision")
    if current_decision and str(current_decision).endswith(".json"):
        path = safe_context_path(root, str(current_decision), errors)
        if path and path not in paths:
            paths.append(path)
    return paths


def validate_decisions(root: Path, status: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    paths = collect_decision_paths(root, status, errors)
    decision_sources_valid = True
    decision_state_conflict = False
    selected_candidate_match = True
    style_decision_seen = False
    regime_decision_seen = False

    for path in paths:
        if not path.exists():
            errors.append(f"decision source missing: {path.relative_to(root)}")
            decision_sources_valid = False
            continue
        data = read_json(path, errors)
        if not data:
            decision_sources_valid = False
            continue
        if has_nonfinite(data):
            errors.append(f"decision source contains nonfinite values: {path.relative_to(root)}")
            decision_sources_valid = False

        for key, value in data.items():
            if key.startswith("ready_for_") or key == "execution_allowed":
                if not isinstance(value, bool):
                    errors.append(f"decision readiness field must be boolean: {path.relative_to(root)}:{key}")
                    decision_sources_valid = False

        if "selected_candidate" in data:
            regime_decision_seen = True
            if data.get("selected_candidate") != status.get("selected_shadow_regime_candidate"):
                selected_candidate_match = False
                decision_state_conflict = True
        if "current_raw_regime" in data and data.get("current_raw_regime") != status.get("latest_known_raw_regime"):
            decision_state_conflict = True
        if "current_selected_shadow_regime" in data and data.get("current_selected_shadow_regime") != status.get("latest_known_shadow_regime"):
            decision_state_conflict = True

        if "style_fit_has_historical_support" in data or "ready_for_adjusted_preview_research" in data:
            style_decision_seen = True
            for key in [
                "ready_for_fit_shadow_observation",
                "ready_for_adjusted_preview_research",
                "ready_for_preview",
                "ready_for_execution",
                "execution_allowed",
            ]:
                if key in data and key in status and data.get(key) != status.get(key):
                    decision_state_conflict = True

    if not regime_decision_seen:
        errors.append("regime candidate authoritative decision source not found in status_sources")
        decision_sources_valid = False
    if not style_decision_seen:
        errors.append("style fit authoritative decision source not found in status_sources")
        decision_sources_valid = False

    return {
        "decision_sources_valid": decision_sources_valid,
        "decision_state_conflict": decision_state_conflict,
        "selected_candidate_match": selected_candidate_match,
        "decision_paths": [str(p.relative_to(root)) for p in paths],
    }


def validate_readiness(status: dict[str, Any], decision_state_conflict: bool, errors: list[str]) -> dict[str, bool]:
    readiness_gates_valid = True
    blocking_conflict = False

    if status.get("ready_for_execution") is False and status.get("execution_allowed") is True:
        errors.append("execution_allowed cannot be true when ready_for_execution=false")
        readiness_gates_valid = False
        blocking_conflict = True
    if status.get("research_only") is True and status.get("execution_allowed") is True:
        errors.append("research_only=true with execution_allowed=true is a blocking conflict")
        readiness_gates_valid = False
        blocking_conflict = True
    if decision_state_conflict:
        readiness_gates_valid = False
        blocking_conflict = True

    return {
        "readiness_gates_valid": readiness_gates_valid,
        "blocking_conflict": blocking_conflict,
    }


def validate_protected_files(root: Path, status: dict[str, Any], errors: list[str]) -> bool:
    protected = set(status.get("protected_files", []))
    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8") if (root / "AGENTS.md").exists() else ""
    missing_status = REQUIRED_PROTECTED_FILES - protected
    missing_agents = {item for item in REQUIRED_PROTECTED_FILES if item not in agents_text}
    if missing_status:
        errors.append(f"protected files missing from current_phase_status: {sorted(missing_status)}")
    if missing_agents:
        errors.append(f"protected files missing from AGENTS.md: {sorted(missing_agents)}")
    return not missing_status and not missing_agents


def validate_staleness(status: dict[str, Any], warnings: list[str], errors: list[str]) -> dict[str, bool]:
    latest_data = parse_date(status.get("latest_data_date"))
    latest_regime = parse_date(status.get("latest_known_regime_date"))
    regime_snapshot_stale = False
    if latest_data and latest_regime and latest_data.date() > latest_regime.date():
        regime_snapshot_stale = True
        warnings.append(
            "regime snapshot is stale; report latest known regime with date, not live current regime"
        )
    elif status.get("latest_data_date") and latest_data is None:
        errors.append("latest_data_date is not parseable")
    elif status.get("latest_known_regime_date") and latest_regime is None:
        errors.append("latest_known_regime_date is not parseable")

    flags = status.get("staleness_flags", {}) if isinstance(status.get("staleness_flags"), dict) else {}
    return {
        "regime_snapshot_stale": regime_snapshot_stale,
        "project_state_snapshot_stale": bool(flags.get("project_state_snapshot_stale", False)),
        "phase_status_stale": bool(flags.get("phase_status_stale", False)),
        "context_consistency_unknown": bool(flags.get("context_consistency_unknown", False)),
    }


def build_markdown(result: dict[str, Any]) -> str:
    warnings = result.get("warnings", [])
    errors = result.get("errors", [])
    lines = [
        "# Project Context Validation Latest",
        "",
        f"- validation_status: {result.get('validation_status')}",
        f"- validated_at: {result.get('validated_at')}",
        f"- repository_root: `{result.get('repository_root')}`",
        f"- blocking_conflict_found: {result.get('blocking_conflict_found')}",
        "",
        "## 当前恢复点",
        "",
        f"- Main Phase: {result.get('current_main_phase')}",
        f"- Current Batch: {result.get('current_batch')}",
        f"- Resume From: {result.get('resume_from')}",
        f"- Selected Shadow Regime Candidate: {result.get('selected_shadow_regime_candidate')}",
        "",
        "## Latest Known Regime Snapshot",
        "",
        f"- Date: {result.get('latest_known_regime_date')}",
        f"- RAW: {result.get('latest_known_raw_regime')}",
        f"- SHADOW: {result.get('latest_known_shadow_regime')}",
        "",
        "## Readiness Gates",
        "",
        f"- Fit Shadow Observation: {result.get('ready_for_fit_shadow_observation')}",
        f"- Adjusted Preview Research: {result.get('ready_for_adjusted_preview_research')}",
        f"- Preview: {result.get('ready_for_preview')}",
        f"- Execution: {result.get('ready_for_execution')}",
        f"- Execution Allowed: {result.get('execution_allowed')}",
        "",
        "## 检查结果",
        "",
        f"- manifest_valid: {result.get('manifest_valid')}",
        f"- required_context_files_complete: {result.get('required_context_files_complete')}",
        f"- bootstrap_read_order_valid: {result.get('bootstrap_read_order_valid')}",
        f"- status_schema_valid: {result.get('status_schema_valid')}",
        f"- phase_batch_consistent: {result.get('phase_batch_consistent')}",
        f"- decision_sources_valid: {result.get('decision_sources_valid')}",
        f"- decision_state_conflict: {result.get('decision_state_conflict')}",
        f"- readiness_gates_valid: {result.get('readiness_gates_valid')}",
        f"- protected_files_complete: {result.get('protected_files_complete')}",
        f"- regime_snapshot_stale: {result.get('regime_snapshot_stale')}",
        "",
        "## Warnings",
        "",
    ]
    lines.extend([f"- {item}" for item in warnings] or ["- 无"])
    lines.extend(["", "## Errors", ""])
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    lines.extend([
        "",
        "## 说明",
        "",
        "本验证器只读检查项目上下文。除写入 latest validation report 外，不自动修复、不运行模型、不运行交易、不更新 snapshot。",
    ])
    return "\n".join(lines) + "\n"


def run_validation(root: Path | None = None, write_report: bool = True) -> dict[str, Any]:
    root = root or repo_root()
    errors: list[str] = []
    warnings: list[str] = []

    manifest, manifest_result = validate_manifest(root, errors, warnings)
    status, status_result = validate_status(root, errors, warnings)
    decision_result = validate_decisions(root, status, errors) if status else {
        "decision_sources_valid": False,
        "decision_state_conflict": True,
        "selected_candidate_match": False,
        "decision_paths": [],
    }
    readiness_result = validate_readiness(status, decision_result["decision_state_conflict"], errors) if status else {
        "readiness_gates_valid": False,
        "blocking_conflict": True,
    }
    protected_files_complete = validate_protected_files(root, status, errors) if status else False
    staleness = validate_staleness(status, warnings, errors) if status else {
        "regime_snapshot_stale": False,
        "project_state_snapshot_stale": False,
        "phase_status_stale": False,
        "context_consistency_unknown": True,
    }

    blocking_conflict = bool(
        errors
        or readiness_result["blocking_conflict"]
        or decision_result["decision_state_conflict"]
        or not manifest_result["manifest_valid"]
        or not status_result["status_schema_valid"]
        or not protected_files_complete
    )
    if blocking_conflict:
        validation_status = "INVALID"
    elif warnings or staleness["regime_snapshot_stale"]:
        validation_status = "VALID_WITH_WARNINGS"
    else:
        validation_status = "VALID"

    result = {
        "validation_status": validation_status,
        "validated_at": now_text(),
        "repository_root": "<project_root>",
        **manifest_result,
        **status_result,
        "decision_sources_valid": decision_result["decision_sources_valid"],
        "decision_state_conflict": decision_result["decision_state_conflict"],
        "readiness_gates_valid": readiness_result["readiness_gates_valid"],
        "protected_files_complete": protected_files_complete,
        **staleness,
        "blocking_conflict_found": blocking_conflict,
        "current_main_phase": status.get("main_phase"),
        "phase_status": status.get("phase_status"),
        "current_batch": status.get("current_batch"),
        "current_batch_status": status.get("current_batch_status"),
        "resume_from": status.get("resume_from"),
        "phase_d_resume_checkpoint": status.get("phase_d_resume_checkpoint"),
        "phase_d_completed_checkpoints": status.get("phase_d_completed_checkpoints", []),
        "next_research_phase": status.get("next_research_phase"),
        "latest_data_date": status.get("latest_data_date"),
        "selected_shadow_regime_candidate": status.get("selected_shadow_regime_candidate"),
        "latest_known_regime_date": status.get("latest_known_regime_date"),
        "latest_known_raw_regime": status.get("latest_known_raw_regime"),
        "latest_known_shadow_regime": status.get("latest_known_shadow_regime"),
        "ready_for_fit_shadow_observation": status.get("ready_for_fit_shadow_observation"),
        "ready_for_adjusted_preview_research": status.get("ready_for_adjusted_preview_research"),
        "ready_for_preview": status.get("ready_for_preview"),
        "ready_for_execution": status.get("ready_for_execution"),
        "execution_allowed": status.get("execution_allowed"),
        "decision_paths": decision_result["decision_paths"],
        "bootstrap_read_order": manifest.get("bootstrap_read_order", []) if manifest else [],
        "warnings": warnings,
        "errors": errors,
    }

    if write_report:
        reports = root / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        (reports / "project_context_validation_latest.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (reports / "project_context_validation_latest.md").write_text(
            build_markdown(result),
            encoding="utf-8",
        )
    return result


def exit_code(result: dict[str, Any], strict: bool = False) -> int:
    status = result.get("validation_status")
    if status == "VALID":
        return 0
    if status == "VALID_WITH_WARNINGS":
        return 2 if strict else 1
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate project context state.")
    parser.add_argument("--json", action="store_true", help="Print JSON validation result.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failing exit code 2.")
    args = parser.parse_args()

    result = run_validation()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Project context validation: {result['validation_status']}")
        print(f"Main Phase: {result.get('current_main_phase')}")
        print(f"Current Batch: {result.get('current_batch')}")
        print(f"Resume From: {result.get('resume_from')}")
        if result.get("warnings"):
            print("Warnings:")
            for item in result["warnings"]:
                print(f"- {item}")
        if result.get("errors"):
            print("Errors:")
            for item in result["errors"]:
                print(f"- {item}")
    return exit_code(result, strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
