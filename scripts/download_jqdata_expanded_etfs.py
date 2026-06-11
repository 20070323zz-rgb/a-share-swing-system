"""Download resolved ETF expansion candidates from JQData into staging.

This script is read-only toward JQData and writes only
``data/staging/jqdata_expanded/``. It does not write to ``data/etf_daily/``
and does not modify strategy logic.
"""

from __future__ import annotations

import argparse
import os
import re
from datetime import date
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = PROJECT_ROOT / "data" / "staging" / "etf_candidates" / "resolved_etf_expansion_candidates.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "staging" / "jqdata_expanded"
FIELDS = ["open", "high", "low", "close", "volume", "money"]
MAX_ESTIMATED_API_CALLS = 50000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download resolved expanded ETF JQData daily bars into staging.")
    parser.add_argument("--all-resolved", action="store_true", help="Download all status=resolved ETFs in resolved CSV.")
    parser.add_argument("--all-candidates", action="store_true", help="Backward-compatible alias for --all-resolved.")
    parser.add_argument("--symbols", nargs="+", default=None, help="Specific symbols or JQData codes to download.")
    parser.add_argument("--candidates", default=str(DEFAULT_CANDIDATES), help="Resolved candidate CSV path.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output staging directory.")
    parser.add_argument("--start", default="2020-01-01", help="Start date, YYYY-MM-DD.")
    parser.add_argument("--end", default=date.today().isoformat(), help="End date, YYYY-MM-DD.")
    parser.add_argument("--force", action="store_true", help="Redownload even when a non-empty staging CSV already exists.")
    parser.add_argument("--max-symbols", type=int, default=None, help="Optional cap for trial accounts.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = resolve_path(args.output_dir)
    targets = select_targets(args)
    selected_count = len(targets)
    targets = [target for target in targets if args.force or not has_existing_nonempty_csv(output_dir, target["jq_code"])]
    skipped_existing = selected_count - len(targets)
    if args.max_symbols:
        targets = targets[: args.max_symbols]

    estimated_api_calls = len(targets)
    print(f"selected_resolved_symbols: {selected_count}")
    print(f"skipped_existing_nonempty: {skipped_existing}")
    print(f"planned_symbols: {estimated_api_calls}")
    print(f"estimated_api_calls: {estimated_api_calls}")
    if estimated_api_calls > MAX_ESTIMATED_API_CALLS:
        print(f"estimated_api_calls exceeds safety limit {MAX_ESTIMATED_API_CALLS}; stopped before download.")
        return
    if not targets:
        print("No resolved candidate symbols selected or all staging files already exist. Nothing downloaded.")
        return

    user = os.getenv("JQDATA_USER")
    password = os.getenv("JQDATA_PASSWORD")
    if not user or not password:
        print("JQData credentials missing: set JQDATA_USER and JQDATA_PASSWORD in your local terminal.")
        print("No password was read, printed, or stored. No staging files were written.")
        return

    try:
        import jqdatasdk as jq
    except ImportError:
        print("jqdatasdk is not installed in this Python environment.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    jq.auth(user, password)

    success = 0
    failed = 0
    for target in targets:
        jq_code = target["jq_code"]
        output_path = output_dir / f"{jq_code}.csv"
        try:
            df = jq.get_price(
                jq_code,
                start_date=args.start,
                end_date=args.end,
                frequency="daily",
                fields=FIELDS,
                skip_paused=False,
                fq="pre",
                panel=False,
            )
            out = normalize_price_frame(df)
            if out.empty:
                raise ValueError("empty JQData response")
            out.to_csv(output_path, index=False)
            success += 1
            print(f"{relative(output_path)} downloaded rows={len(out)}")
        except Exception as exc:
            failed += 1
            print(f"{jq_code} failed: {exc}")

    print(f"jqdata expanded staging download finished: success {success}, failed {failed}, skipped_existing {skipped_existing}")
    print(f"output_dir: {relative(output_dir)}")


def select_targets(args: argparse.Namespace) -> list[dict]:
    df = read_resolved_candidates(args)
    if args.symbols:
        wanted = set()
        for value in args.symbols:
            text = str(value).strip()
            if text:
                wanted.add(text)
            wanted.update(extract_codes(text))
        rows = []
        for _, row in df.iterrows():
            jq_code = str(row.get("resolved_jq_code", ""))
            base_code = jq_code.split(".")[0]
            original_code = str(row.get("original_code", ""))
            if base_code in wanted or jq_code in wanted or original_code in wanted:
                if row.get("status", "") == "resolved" and is_jq_code(jq_code):
                    rows.append({"jq_code": jq_code, "original_code": original_code})
        return dedupe_targets(rows)

    if not (args.all_resolved or args.all_candidates):
        return []

    rows = []
    for _, row in df[df.get("status", "") == "resolved"].iterrows():
        jq_code = str(row.get("resolved_jq_code", ""))
        if is_jq_code(jq_code):
            rows.append({"jq_code": jq_code, "original_code": str(row.get("original_code", ""))})
    return dedupe_targets(rows)


def read_resolved_candidates(args: argparse.Namespace) -> pd.DataFrame:
    path = resolve_path(args.candidates)
    if not path.exists():
        print(f"candidate file not found: {relative(path)}")
        return pd.DataFrame(columns=["resolved_jq_code", "original_code", "status"])
    df = pd.read_csv(path, dtype=str).fillna("")
    if "resolved_jq_code" not in df.columns:
        df["resolved_jq_code"] = df.get("code", pd.Series(dtype=str)).map(
            lambda code: to_jq_symbol(str(code)) if is_six_digit_code(str(code)) else ""
        )
        df["original_code"] = df.get("code", "")
        df["status"] = df["resolved_jq_code"].map(lambda value: "resolved" if value else "unresolved")
    return df


def dedupe_targets(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique = []
    for row in rows:
        jq_code = row["jq_code"]
        if jq_code and jq_code not in seen:
            unique.append(row)
            seen.add(jq_code)
    return unique


def has_existing_nonempty_csv(output_dir: Path, jq_code: str) -> bool:
    path = output_dir / f"{jq_code}.csv"
    return path.exists() and path.stat().st_size > 0


def normalize_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", *FIELDS])
    out = df.reset_index()
    if "time" in out.columns:
        out = out.rename(columns={"time": "date"})
    elif "index" in out.columns:
        out = out.rename(columns={"index": "date"})
    if "date" not in out.columns:
        out.insert(0, "date", df.index)
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for field in FIELDS:
        if field not in out.columns:
            out[field] = pd.NA
    out = out[["date", *FIELDS]].dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
    return out


def extract_codes(value: str) -> list[str]:
    return re.findall(r"(?<!\d)(\d{6})(?!\d)", str(value))


def is_six_digit_code(value: str) -> bool:
    return bool(re.fullmatch(r"\d{6}", str(value)))


def is_jq_code(value: str) -> bool:
    return bool(re.fullmatch(r"\d{6}\.(XSHG|XSHE)", str(value)))


def to_jq_symbol(code: str) -> str:
    exchange = "XSHG" if code.startswith(("5", "6")) else "XSHE"
    return f"{code}.{exchange}"


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
