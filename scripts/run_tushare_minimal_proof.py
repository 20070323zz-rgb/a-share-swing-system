#!/usr/bin/env python3
"""Execute the bounded, research-only Tushare minimal staging proof."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_sources.tushare.probe import load_config, run_probe, select_etf_samples  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/tushare_minimal_proof.yaml")
    parser.add_argument("--evidence-mode", required=True, choices=("real", "mock"))
    parser.add_argument("--run-id")
    parser.add_argument("--dry-run", action="store_true", help="show the bounded plan without calling Tushare")
    parser.add_argument("--mock-fixture", help="run with an explicitly labelled mock response fixture")
    args = parser.parse_args()
    config_path = ROOT / args.config
    if args.evidence_mode == "mock" and not args.mock_fixture and not args.dry_run:
        parser.error("mock evidence mode requires --mock-fixture")
    if args.evidence_mode == "real" and args.mock_fixture:
        parser.error("real evidence mode rejects --mock-fixture")
    if args.dry_run:
        config = load_config(config_path)
        etfs = select_etf_samples(ROOT, config)
        estimate = 2 + 3 + 3 + 1 + 1 + 3 + len(etfs) + 1
        count_label = "estimated_real_api_calls" if args.evidence_mode == "real" else "estimated_mock_calls"
        print(f"dry_run=true evidence_mode={args.evidence_mode} {count_label}={estimate}/{config['runtime']['max_api_requests']} etfs={len(etfs)}")
        return 0
    fixtures = json.loads((ROOT / args.mock_fixture).read_text(encoding="utf-8")) if args.mock_fixture else None
    manifest = run_probe(
        ROOT,
        config_path,
        evidence_mode=args.evidence_mode,
        mock_responses=fixtures,
        run_id=args.run_id,
    )
    print(
        f"status={manifest['status']} evidence_mode={manifest['evidence_mode']} "
        f"real_api_call_count={manifest['real_api_call_count']} mock_call_count={manifest['mock_call_count']} "
        f"run_id={manifest['run_id']}"
    )
    return 0 if manifest["status"] in {"REAL_PROOF_COMPLETE", "MOCK_VALIDATION_PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
