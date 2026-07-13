#!/usr/bin/env python3
"""Execute the bounded, research-only Tushare minimal staging proof."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_sources.tushare.client import TushareMinimalClient  # noqa: E402
from data_sources.tushare.probe import load_config, run_probe, select_etf_samples  # noqa: E402


def mock_factory(fixture_path: Path):
    fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))

    def factory(**kwargs):
        def transport(payload, timeout):
            table = fixtures[payload["api_name"]]
            return json.dumps({"code": 0, "msg": "", "data": table}, ensure_ascii=False).encode("utf-8")

        return TushareMinimalClient(token="mock-fixture-token", transport=transport, **kwargs)

    return factory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/tushare_minimal_proof.yaml")
    parser.add_argument("--run-id")
    parser.add_argument("--dry-run", action="store_true", help="show the bounded plan without calling Tushare")
    parser.add_argument("--mock-fixture", help="run with an explicitly labelled mock response fixture")
    args = parser.parse_args()
    config_path = ROOT / args.config
    if args.dry_run:
        config = load_config(config_path)
        etfs = select_etf_samples(ROOT, config)
        estimate = 2 + 3 + 3 + 1 + 1 + 3 + len(etfs) + 1
        print(f"dry_run=true estimated_requests={estimate}/{config['runtime']['max_api_requests']} etfs={len(etfs)}")
        return 0
    factory = mock_factory(ROOT / args.mock_fixture) if args.mock_fixture else TushareMinimalClient
    manifest = run_probe(ROOT, config_path, client_factory=factory, run_id=args.run_id)
    print(f"status={manifest['status']} requests={manifest['api_request_count']}/{manifest['api_request_limit']} run_id={manifest['run_id']}")
    return 0 if manifest["status"] in {"COMPLETE", "COMPLETE_WITH_PERMISSION_GAPS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
