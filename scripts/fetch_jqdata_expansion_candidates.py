"""Fetch JQData ETF/security candidates into staging.

Credentials are read only from environment variables:
JQDATA_USER and JQDATA_PASSWORD. The script never prints or stores passwords.
It writes only data/staging/etf_candidates/jqdata_etf_candidates.csv.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "staging" / "etf_candidates" / "jqdata_etf_candidates.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch JQData ETF candidate list into staging.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output CSV path.")
    parser.add_argument("--include-all-funds", action="store_true", help="Keep all exchange funds, not just ETF-like names.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    user = os.getenv("JQDATA_USER")
    password = os.getenv("JQDATA_PASSWORD")
    if not user or not password:
        print("JQData credentials missing: set JQDATA_USER and JQDATA_PASSWORD in your local terminal.")
        print("No password was read, printed, or stored. No output was overwritten.")
        return

    try:
        import jqdatasdk as jq
    except ImportError:
        print("jqdatasdk is not installed in this Python environment.")
        return

    jq.auth(user, password)
    securities = jq.get_all_securities(types=["fund"])
    rows = []
    for jq_code, row in securities.iterrows():
        display_name = str(row.get("display_name", ""))
        name = str(row.get("name", ""))
        exchange = str(jq_code).split(".")[-1] if "." in str(jq_code) else ""
        code = str(jq_code).split(".")[0]
        is_exchange_fund = exchange in {"XSHG", "XSHE"}
        is_etf_like = "ETF" in display_name.upper() or "ETF" in name.upper() or "交易型" in display_name
        if not is_exchange_fund:
            continue
        if not args.include_all_funds and not is_etf_like:
            continue
        rows.append(
            {
                "code": code,
                "display_name": display_name,
                "name": name,
                "start_date": to_date(row.get("start_date")),
                "end_date": to_date(row.get("end_date")),
                "type": "fund",
                "exchange": exchange,
                "source": "jqdata_get_all_securities",
            }
        )

    output = resolve_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).sort_values(["exchange", "code"]).to_csv(output, index=False)
    print(f"jqdata ETF candidates fetched: {len(rows)}")
    print("estimated_api_calls: 1")
    print(f"output: {relative(output)}")


def to_date(value: object) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.strftime("%Y-%m-%d")


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()
