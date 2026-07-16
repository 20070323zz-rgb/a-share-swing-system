#!/usr/bin/env python3
"""App-facing Tushare-primary ETF candidate updater."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from data_sources.tushare.app_update import SUCCESS_CODES, run_tushare_primary_update  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tushare-primary ETF daily candidate updater")
    parser.add_argument("--trade-date", required=True, help="expected Tushare fund_daily trade date")
    parser.add_argument("--config", default="configs/tushare_primary_app_update.yaml")
    parser.add_argument("--status-json", default="reports/data_update_status.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = _resolve(args.config)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    result = run_tushare_primary_update(PROJECT_ROOT, config, args.trade_date)
    status_path = _resolve(args.status_json)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = status_path.with_name(f".{status_path.name}.tmp")
    temp_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp_path, status_path)
    print(json.dumps({
        "provider": result.get("provider"),
        "result_code": result.get("result_code"),
        "business_date": result.get("business_date"),
        "updated_count": result.get("updated_count", 0),
        "ssot_manifest_hash": result.get("ssot_manifest_hash", ""),
        "processed_symbols": result.get("processed_symbols", 0),
        "promotion_enabled": result.get("promotion_enabled", False),
        "ssot_changed": result.get("ssot_changed", False),
    }, ensure_ascii=False))
    return 0 if result.get("result_code") in SUCCESS_CODES else 2


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
