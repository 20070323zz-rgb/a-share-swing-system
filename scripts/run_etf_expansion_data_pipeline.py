"""Run the ETF expansion data pipeline as a batch process.

The pipeline stages data first, then validates and dry-runs before any formal
import. It never reads or stores passwords directly; JQData credentials are
only consumed by child scripts through environment variables.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "etf_expansion_pipeline_report.md"
IMPORT_RESULTS_CSV = PROJECT_ROOT / "reports" / "etf_expansion_import_results.csv"
DIAGNOSE_SCRIPT = PROJECT_ROOT / "scripts" / "diagnose_jqdata_units.py"
STAGING_DIR = PROJECT_ROOT / "data" / "staging" / "jqdata_expanded"
EXPANSION_CANDIDATES = PROJECT_ROOT / "data" / "etf_pool_expansion_candidates.csv"
RESOLVED_CANDIDATES = PROJECT_ROOT / "data" / "staging" / "etf_candidates" / "resolved_etf_expansion_candidates.csv"


class StepResult(dict):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ETF expansion staging, validation, dry-run and optional import pipeline.")
    parser.add_argument("--start", default="2020-01-01", help="JQData download start date.")
    parser.add_argument("--end", default=date.today().isoformat(), help="JQData download end date.")
    parser.add_argument("--force-download", action="store_true", help="Redownload existing non-empty staging files.")
    parser.add_argument("--no-import", action="store_true", help="Stop after dry-run even if dry-run succeeds.")
    parser.add_argument("--max-symbols", type=int, default=None, help="Optional download cap for trial accounts.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results: list[StepResult] = []
    imported = False
    jqdata_ready = bool(os.getenv("JQDATA_USER") and os.getenv("JQDATA_PASSWORD"))

    if jqdata_ready:
        results.append(run_step("fetch_jqdata_candidates", ["python3", "scripts/fetch_jqdata_expansion_candidates.py"]))
    else:
        results.append(skipped("fetch_jqdata_candidates", "JQData credentials not set; using existing local candidate list."))

    results.append(run_step("resolve_candidates", ["python3", "scripts/resolve_etf_expansion_candidates.py"]))

    if jqdata_ready:
        download_cmd = [
            "python3",
            "scripts/download_jqdata_expanded_etfs.py",
            "--all-resolved",
            "--start",
            args.start,
            "--end",
            args.end,
        ]
        if args.force_download:
            download_cmd.append("--force")
        if args.max_symbols:
            download_cmd += ["--max-symbols", str(args.max_symbols)]
        results.append(run_step("download_resolved_staging", download_cmd))
    else:
        results.append(skipped("download_resolved_staging", "JQData credentials not set; using existing data/staging/jqdata_expanded/ files."))

    results.append(run_step("validate_staging", ["python3", "scripts/validate_manual_csv.py", "--all-etf", "--input-dir", "data/staging/jqdata_expanded"]))

    if diagnose_supports_input_dir():
        results.append(run_step("diagnose_units", ["python3", "scripts/diagnose_jqdata_units.py", "--all-etf", "--input-dir", "data/staging/jqdata_expanded"]))
    else:
        results.append(skipped("diagnose_units", "diagnose_jqdata_units.py does not support --input-dir yet; import script handles local-overlap checks where possible."))

    dry_run = run_step(
        "dry_run_import",
        ["python3", "scripts/import_jqdata_staging.py", "--all-etf", "--input-dir", "data/staging/jqdata_expanded", "--dry-run"],
    )
    results.append(dry_run)
    dry_run_summary = read_import_results()
    dry_run_success_symbols = sorted(dry_run_summary.loc[dry_run_summary["status"].eq("dry_run_ok"), "symbol"].astype(str).unique())

    if args.no_import:
        results.append(skipped("formal_import", "--no-import was set; dry-run successes remain staging_only."))
        update_candidate_statuses(imported=False)
    elif dry_run["returncode"] == 0 and dry_run_success_symbols:
        formal = run_step(
            "formal_import",
            [
                "python3",
                "scripts/import_jqdata_staging.py",
                "--input-dir",
                "data/staging/jqdata_expanded",
                "--symbols",
                *dry_run_success_symbols,
            ],
        )
        results.append(formal)
        formal_summary = read_import_results()
        imported = formal["returncode"] == 0 and int(formal_summary["status"].eq("imported").sum()) > 0
        update_candidate_statuses(imported=imported)
    else:
        results.append(skipped("formal_import", "No dry-run successes; all files remain staging_only or failed."))
        update_candidate_statuses(imported=False)

    if imported:
        results.append(run_step("data_coverage", ["python3", "src/data_coverage.py"]))
        results.append(run_step("data_health", ["python3", "src/data_health.py"]))
        results.append(run_step("main_reports", ["python3", "src/main.py"]))
        if not main_runs_research_scripts():
            results.append(run_step("factor_analysis", ["python3", "src/factor_analysis.py"]))
            results.append(run_step("model_research", ["python3", "src/model_research.py"]))
    else:
        results.append(skipped("standard_reports", "Standard reports skipped because no formal import was completed."))

    write_report(results, imported, dry_run_success_count=len(dry_run_success_symbols))
    failed = sum(1 for result in results if result["status"] == "failed")
    print(f"ETF expansion pipeline finished: failed_steps {failed}, formal_import {'yes' if imported else 'no'}")
    print(f"report written: {relative(REPORT_PATH)}")


def run_step(name: str, cmd: list[str]) -> StepResult:
    completed = subprocess.run(cmd, cwd=PROJECT_ROOT, text=True, capture_output=True, env=os.environ.copy())
    status = "ok" if completed.returncode == 0 else "failed"
    print(f"[{status}] {name}")
    return StepResult(
        name=name,
        status=status,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def skipped(name: str, reason: str) -> StepResult:
    print(f"[skipped] {name}")
    return StepResult(name=name, status="skipped", returncode=0, stdout=reason, stderr="")


def diagnose_supports_input_dir() -> bool:
    completed = subprocess.run(["python3", str(DIAGNOSE_SCRIPT), "--help"], cwd=PROJECT_ROOT, text=True, capture_output=True)
    return "--input-dir" in completed.stdout


def read_import_results() -> pd.DataFrame:
    if not IMPORT_RESULTS_CSV.exists():
        return pd.DataFrame(columns=["symbol", "status"])
    return pd.read_csv(IMPORT_RESULTS_CSV, dtype=str).fillna("")


def update_candidate_statuses(imported: bool) -> None:
    if not EXPANSION_CANDIDATES.exists() or not RESOLVED_CANDIDATES.exists() or not IMPORT_RESULTS_CSV.exists():
        return
    candidates = pd.read_csv(EXPANSION_CANDIDATES, dtype=str).fillna("")
    resolved = pd.read_csv(RESOLVED_CANDIDATES, dtype=str).fillna("")
    results = pd.read_csv(IMPORT_RESULTS_CSV, dtype=str).fillna("")
    result_by_jq_code = {f"{row.symbol}.XSHG": row.status for row in []}
    for _, row in results.iterrows():
        symbol = str(row.get("symbol", ""))
        status = str(row.get("status", ""))
        if symbol:
            result_by_jq_code[f"{symbol}.XSHG"] = status
            result_by_jq_code[f"{symbol}.XSHE"] = status

    by_original: dict[str, set[str]] = {}
    for _, row in resolved.iterrows():
        original = str(row.get("original_code", ""))
        jq_code = str(row.get("resolved_jq_code", ""))
        status = result_by_jq_code.get(jq_code, str(row.get("status", "")))
        by_original.setdefault(original, set()).add(status)

    def candidate_status(code: str) -> str:
        statuses = by_original.get(str(code), set())
        if "imported" in statuses:
            return "imported"
        if "dry_run_ok" in statuses:
            return "staging_only" if not imported else "failed_formal_import"
        if "validation_failed" in statuses:
            return "failed_validation"
        if "failed" in statuses:
            return "failed_dry_run"
        if "resolved" in statuses:
            return "staging_only"
        return "unresolved"

    candidates["status"] = candidates["code"].map(candidate_status)
    candidates.to_csv(EXPANSION_CANDIDATES, index=False)


def main_runs_research_scripts() -> bool:
    main_path = PROJECT_ROOT / "src" / "main.py"
    if not main_path.exists():
        return False
    text = main_path.read_text(encoding="utf-8")
    return "factor_analysis" in text and "model_research" in text


def write_report(results: list[StepResult], imported: bool, dry_run_success_count: int) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    import_results = read_import_results()
    staging_total = len(list(STAGING_DIR.glob("*.csv"))) if STAGING_DIR.exists() else 0
    status_counts = import_results["status"].value_counts().to_dict() if not import_results.empty else {}
    validation_failed = int(status_counts.get("validation_failed", 0))
    dry_run_failed = int(status_counts.get("failed", 0)) + validation_failed
    lines = [
        "# ETF Expansion Pipeline Report",
        "",
        f"- Generated on: {date.today().isoformat()}",
        "- Mode: batch staging -> validate -> dry-run -> partial formal import.",
        f"- Expanded staging CSV total: {staging_total}",
        f"- Validation valid: {staging_total - validation_failed}",
        f"- Validation failed: {validation_failed}",
        f"- Dry-run success: {dry_run_success_count}",
        f"- Dry-run failed: {dry_run_failed}",
        f"- Formal import completed: {'yes' if imported else 'no'}",
        f"- Formal import count: {int(status_counts.get('imported', 0))}",
        "- BaoStock API calls: 0",
        "- Safety: no broker API, no real orders, no account/password storage, no automatic trading, no strategy or position-rule changes.",
        "- Staging rule: new data is downloaded only to `data/staging/jqdata_expanded/` before validation and dry-run.",
        "- Merge rule: formal import uses existing local rows first on duplicate dates.",
        "",
        "## Step Summary",
        "",
        "| step | status | returncode | note |",
        "| --- | --- | ---: | --- |",
    ]
    for result in results:
        note = first_line(result.get("stdout", "") or result.get("stderr", ""))
        lines.append(f"| {result['name']} | {result['status']} | {result['returncode']} | {escape_pipe(note)} |")
    lines.extend(["", "## Step Output", ""])
    for result in results:
        lines.append(f"### {result['name']}")
        lines.append("")
        lines.append(f"- Status: {result['status']}")
        lines.append(f"- Return code: {result['returncode']}")
        if result.get("stdout"):
            lines.append("")
            lines.append("```text")
            lines.append(result["stdout"][-4000:])
            lines.append("```")
        if result.get("stderr"):
            lines.append("")
            lines.append("```text")
            lines.append(result["stderr"][-4000:])
            lines.append("```")
        lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def first_line(text: str) -> str:
    return next((line for line in text.splitlines() if line.strip()), "")


def escape_pipe(text: str) -> str:
    return text.replace("|", "\\|")


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()
