#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.report_governance.authority_merge import apply_owned_overlay


def git_json(ref: str, relative_path: str) -> dict:
    content = subprocess.check_output(["git", "show", f"{ref}:{relative_path}"], cwd=ROOT, text=True)
    return json.loads(content)


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge Phase A-R report state onto the latest PR #3 Availability authority.")
    parser.add_argument("--availability-ref", default="origin/agent/tushare-etf-availability-audit")
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--pr-url", required=True)
    args = parser.parse_args()
    authority = git_json(args.availability_ref, "docs/current_phase_status.json")
    authority_head = subprocess.check_output(["git", "rev-parse", args.availability_ref], cwd=ROOT, text=True).strip()
    report_sources = [
        "reports/reports_governance_pr4_salvage_assessment_2026-07-15.md",
        "reports/reports_governance_phase_ar_build_2026-07-15.md",
        "reports/governance/phase_ar/report_inventory_v1_2026-07-15.json",
        "reports/governance/phase_ar/active_reference_index_v1_2026-07-15.json",
        "reports/governance/phase_ar/governance_evidence_index_v1_2026-07-15.json",
        "reports/governance/phase_ar/migration_readiness_v1_2026-07-15.json",
        "reports/governance/phase_ar/candidate_full_review_v1_2026-07-15.json",
        "reports/governance/phase_ar/immutable_governance_snapshot_manifest_v1_2026-07-15.json",
        "docs/reports_governance/phase_b_end_to_end_contract.md",
    ]
    overlay = {
        "status_sources": {"reports_governance_phase_ar": report_sources},
        "reports_governance_phase_a_status": "SUPERSEDED_BY_PHASE_AR",
        "reports_governance_phase_a_pr_status": "CLOSED_SUPERSEDED_NOT_MERGED",
        "reports_governance_phase_a_pr_number": 4,
        "reports_governance_phase_ar_status": "ACTIVE",
        "reports_governance_phase_ar_branch": "agent/reports-governance-phase-a-rebuild",
        "reports_governance_phase_ar_pr_status": "DRAFT",
        "reports_governance_phase_ar_pr_number": args.pr_number,
        "reports_governance_phase_ar_pr_url": args.pr_url,
        "report_inventory_status": "IMPLEMENTED_PENDING_INDEPENDENT_QC",
        "report_inventory_record_count": 644,
        "report_active_reference_index_status": "IMPLEMENTED_PENDING_INDEPENDENT_QC",
        "report_structured_reference_count": 1961,
        "report_backstop_reference_count": 4104,
        "report_scanner_disagreement_count": 35,
        "report_known_active_regression_recall": "43_OF_43",
        "report_governance_evidence_index_status": "IMPLEMENTED_PENDING_INDEPENDENT_QC",
        "report_governance_evidence_record_count": 6946,
        "report_unresolved_evidence_id_count": 0,
        "report_migration_readiness_status": "PROVISIONAL_PENDING_INDEPENDENT_QC",
        "report_machine_provisional_candidate_count": 52,
        "report_candidate_full_review_count": 52,
        "report_candidate_full_review_pass_count": 52,
        "report_final_provisional_dry_run_candidate_count": 52,
        "report_archived_provisional_overlap_count": 0,
        "report_active_reference_provisional_overlap_count": 0,
        "report_safe_to_delete_after_authorization_count": 0,
        "report_snapshot_immutability_status": "ENFORCED",
        "report_snapshot_group_manifest_sha256": "86f1f31c6e128df6eeb4b9a259d822637c58f93f8053a2d8de8ab71bd5b33939",
        "report_phase_b_contract_status": "COMPLETE",
        "report_file_migration_status": "BLOCKED",
        "report_migration_phase_b_status": "BLOCKED",
        "report_path_registry_status": "NOT_STARTED",
        "report_deletion_status": "BLOCKED",
        "report_pr_3_authority_head": authority_head,
        "report_pr_3_authority_preservation_status": "PRESERVED",
        "report_zero_move_status": "PASS",
    }
    owned_paths = {key for key in overlay if key != "status_sources"}
    owned_paths.add("status_sources.reports_governance_phase_ar")
    merged = apply_owned_overlay(authority, overlay, owned_paths)
    path = ROOT / "docs/current_phase_status.json"
    path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Availability authority: {authority_head}")
    print(f"Updated: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
