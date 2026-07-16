#!/usr/bin/env python3
"""Rebuild sanitized ETF availability timing reports from local manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_sources.tushare.availability_summary import build_availability_reports  # noqa: E402
from data_sources.tushare.etf_availability_probe import load_audit_config, write_universe_mapping_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/tushare_etf_availability_audit.yaml")
    args = parser.parse_args()
    config = load_audit_config(args.config)
    mapping = write_universe_mapping_report(ROOT, config)
    summary = build_availability_reports(ROOT, config)
    print(json.dumps({"mapping": mapping, "summary": summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
