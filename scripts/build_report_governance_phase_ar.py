#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.report_governance import build_phase_ar


def main() -> int:
    parser = argparse.ArgumentParser(description="Build immutable Reports Governance Phase A-R artifacts.")
    parser.add_argument("--date", required=True, help="Snapshot date in YYYY-MM-DD format")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--source-tree-commit", help="Commit whose source tree was scanned; defaults to HEAD")
    args = parser.parse_args()
    result = build_phase_ar(ROOT, args.date, args.output_root, source_tree_commit=args.source_tree_commit)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
