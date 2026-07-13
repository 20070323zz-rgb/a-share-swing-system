"""Guarded entrypoint for the existing paper trade engine."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from execution.paper_freshness_gate import (  # noqa: E402
    BLOCKED_INCOMPLETE_COVERAGE,
    BLOCKED_INVALID_INPUT,
    BLOCKED_MISSING_SYMBOL_BAR,
    BLOCKED_PENDING_DATA,
    BLOCKED_STALE_MARKET_DATA,
    BLOCKED_STALE_RANKING,
    BLOCKED_STALE_SIGNAL,
    BLOCKED_UPDATE_FAILURE,
    PASS,
    SKIPPED_NON_TRADING_DAY,
    GatePaths,
    audit_historical_stale_trades,
    evaluate_freshness_gate,
    write_historical_audit_report,
    write_preflight_outputs,
)


EXIT_CODES = {
    PASS: 0,
    SKIPPED_NON_TRADING_DAY: 0,
    BLOCKED_STALE_MARKET_DATA: 20,
    BLOCKED_UPDATE_FAILURE: 21,
    BLOCKED_PENDING_DATA: 22,
    BLOCKED_INCOMPLETE_COVERAGE: 23,
    BLOCKED_STALE_SIGNAL: 24,
    BLOCKED_STALE_RANKING: 25,
    BLOCKED_MISSING_SYMBOL_BAR: 26,
    BLOCKED_INVALID_INPUT: 27,
}
ENGINE_FAILURE_EXIT_CODE = 30

EngineInvoker = Callable[[Path, str, bool, date], dict[str, Any]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Paper execution freshness gate and guarded engine wrapper")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true", help="Run the existing paper engine in execute mode only after PASS.")
    mode.add_argument("--dry-run", action="store_true", help="Run the existing paper engine in dry-run mode only after PASS.")
    mode.add_argument("--preflight-only", action="store_true", help="Evaluate and report the gate without invoking the engine.")
    parser.add_argument("--execution-date", help="Expected trade date in YYYY-MM-DD; defaults to the local date.")
    parser.add_argument("--force", action="store_true", help="Forward --force to the existing engine after a PASS.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help=argparse.SUPPRESS)
    parser.add_argument("--audit-date", help="Also append a non-destructive historical stale-trade audit for YYYY-MM-DD.")
    parser.add_argument("--audit-only", action="store_true", help="Write only the requested historical audit and exit.")
    return parser.parse_args()


def run_guarded_execution(
    *,
    paths: GatePaths,
    execution_date: date,
    mode: str,
    force: bool = False,
    engine_invoker: EngineInvoker | None = None,
) -> tuple[dict[str, Any], int]:
    payload = evaluate_freshness_gate(paths, execution_date)
    payload["engine_mode"] = mode

    if mode == "execute" and execution_date != date.today() and payload["gate_status"] == PASS:
        payload["gate_status"] = BLOCKED_INVALID_INPUT
        payload["blocking_reasons"] = [
            f"historical/future execute is forbidden: execution_date={execution_date.isoformat()}, local_date={date.today().isoformat()}"
        ]
        payload["checks"]["execute_date_is_local_date"] = False

    if payload["gate_status"] != PASS or mode == "preflight_only":
        write_preflight_outputs(payload, paths)
        return payload, EXIT_CODES.get(payload["gate_status"], 27)

    invoker = engine_invoker or _invoke_existing_engine
    engine_result = invoker(paths.project_root, mode, force, execution_date)
    payload["engine_invoked"] = True
    payload["engine_exit_code"] = int(engine_result.get("exit_code", 1))
    payload["engine_command"] = engine_result.get("command", [])
    payload["engine_stdout_tail"] = _tail(str(engine_result.get("stdout", "")))
    payload["engine_stderr_tail"] = _tail(str(engine_result.get("stderr", "")))
    write_preflight_outputs(payload, paths)
    exit_code = 0 if payload["engine_exit_code"] == 0 else ENGINE_FAILURE_EXIT_CODE
    return payload, exit_code


def _invoke_existing_engine(project_root: Path, mode: str, force: bool, execution_date: date) -> dict[str, Any]:
    if mode not in {"dry_run", "execute"}:
        raise ValueError(f"unsupported engine mode: {mode}")
    engine_file = project_root / "src" / "paper_trade_engine.py"
    mode_arg = "--execute" if mode == "execute" else "--dry-run"
    local_date = date.today()
    if mode == "dry_run" and execution_date != local_date:
        code = (
            "import json,sys;"
            f"sys.path.insert(0,{str((project_root / 'src').resolve())!r});"
            "import paper_trade_engine as engine;"
            f"engine._engine_run_date=lambda:{execution_date.isoformat()!r};"
            f"result=engine.run_engine(dry_run=True,force={bool(force)!r});"
            "print(json.dumps(result,ensure_ascii=False))"
        )
        command = [sys.executable, "-c", code]
    else:
        command = [sys.executable, str(engine_file), mode_arg]
        if force:
            command.append("--force")
    completed = subprocess.run(command, cwd=project_root, text=True, capture_output=True, check=False)
    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "command": _display_command(command, project_root),
    }


def _display_command(command: list[str], project_root: Path) -> list[str]:
    result = list(command)
    engine_path = str(project_root / "src" / "paper_trade_engine.py")
    return ["src/paper_trade_engine.py" if item == engine_path else item for item in result]


def _tail(value: str, limit: int = 3000) -> str:
    return value[-limit:]


def _parse_date(value: str | None, label: str) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"invalid {label}: {value}; expected YYYY-MM-DD") from exc


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    paths = GatePaths.from_root(project_root)

    if args.audit_only and not args.audit_date:
        raise SystemExit("--audit-only requires --audit-date")
    if args.audit_date:
        audit_date = _parse_date(args.audit_date, "audit date")
        records = audit_historical_stale_trades(paths, audit_date)
        json_path, md_path = write_historical_audit_report(records, paths, audit_date)
        print(f"historical audit rows: {len(records)}")
        print(f"historical audit JSON: {json_path}")
        print(f"historical audit Markdown: {md_path}")
        if args.audit_only:
            return

    execution_date = _parse_date(args.execution_date, "execution date")
    mode = "execute" if args.execute else "preflight_only" if args.preflight_only else "dry_run"
    payload, exit_code = run_guarded_execution(
        paths=paths,
        execution_date=execution_date,
        mode=mode,
        force=args.force,
    )
    print(json.dumps({
        "run_id": payload.get("run_id"),
        "expected_trade_date": payload.get("expected_trade_date"),
        "gate_status": payload.get("gate_status"),
        "engine_invoked": payload.get("engine_invoked"),
        "engine_exit_code": payload.get("engine_exit_code"),
        "blocking_reasons": payload.get("blocking_reasons", []),
    }, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
