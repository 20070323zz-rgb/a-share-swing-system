#!/usr/bin/env python3
"""Read-only bootstrap helper for new Codex threads."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import validate_project_context


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    result = validate_project_context.run_validation(root=root, write_report=True)
    manifest = json.loads((root / "docs/project_context_manifest.json").read_text(encoding="utf-8"))

    print("Project Context Bootstrap")
    print()
    print("项目：")
    print(result.get("current_main_phase") and "a-share-swing-system")
    print()
    print("仓库：")
    print(result.get("repository_root"))
    print()
    print("Bootstrap Read Order:")
    for item in manifest.get("bootstrap_read_order", []):
        print(f"- {item}")
    print()
    print("Validation:")
    print(result.get("validation_status"))
    print()
    print("Main Phase:")
    print(result.get("current_main_phase"))
    print()
    print("Phase Status:")
    print(result.get("phase_status"))
    print()
    print("Current Batch:")
    print(result.get("current_batch"))
    print()
    print("Batch Status:")
    print(result.get("current_batch_status"))
    print()
    print("Resume From:")
    print(result.get("resume_from"))
    print()
    print("Internal Resume Checkpoint:")
    print(result.get("phase_d_resume_checkpoint"))
    print()
    print("Selected Shadow Regime Candidate:")
    print(result.get("selected_shadow_regime_candidate"))
    print()
    print("Latest Known Regime:")
    print(result.get("latest_known_regime_date"))
    print(f"RAW = {result.get('latest_known_raw_regime')}")
    print(f"SHADOW = {result.get('latest_known_shadow_regime')}")
    print()
    print("Readiness:")
    print(f"Fit Shadow Observation = {str(result.get('ready_for_fit_shadow_observation')).lower()}")
    print(f"Adjusted Preview Research = {str(result.get('ready_for_adjusted_preview_research')).lower()}")
    print(f"Preview = {str(result.get('ready_for_preview')).lower()}")
    print(f"Execution = {str(result.get('ready_for_execution')).lower()}")
    print(f"Execution Allowed = {str(result.get('execution_allowed')).lower()}")
    print()
    print("Next Research Phase:")
    print(result.get("next_research_phase"))
    print()
    print("Next Required Action:")
    if result.get("phase_status") == "COMPLETE":
        print("Start next research phase only after a new authorized Batch instruction")
    elif result.get("phase_d_resume_checkpoint"):
        print(f"Resume {result.get('resume_from')} at {result.get('phase_d_resume_checkpoint')}")
    else:
        print(f"Resume {result.get('resume_from')}")
    print()
    print("Warnings:")
    for item in result.get("warnings", []) or ["无"]:
        print(f"- {item}")
    if result.get("errors"):
        print()
        print("Errors:")
        for item in result["errors"]:
            print(f"- {item}")

    return validate_project_context.exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
