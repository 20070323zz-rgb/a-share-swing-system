from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
TESTS = Path(__file__).resolve().parent
for path in (SRC, SCRIPTS, TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

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
    GatePaths,
)
import run_paper_execution_guarded as wrapper  # noqa: E402
from paper_gate_test_utils import (  # noqa: E402
    TARGET_DATE,
    build_gate_fixture,
    write_ranking,
    write_sell_review,
    write_signals,
    write_update_status,
    write_watchlist,
)


class GuardedExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        build_gate_fixture(self.root)
        self.paths = GatePaths.from_root(self.root)
        self.target = date.fromisoformat(TARGET_DATE)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_pass_dry_run_invokes_engine_without_touching_protected_files(self) -> None:
        calls: list[tuple] = []

        def fake_invoker(project_root: Path, mode: str, force: bool, execution_date: date) -> dict:
            calls.append((project_root, mode, force, execution_date))
            return {
                "exit_code": 0,
                "stdout": "paper_trade_engine status: dry_run",
                "stderr": "",
                "command": ["python", "src/paper_trade_engine.py", "--dry-run"],
            }

        trades_before = self.paths.trades_file.read_bytes()
        positions_before = self.paths.positions_file.read_bytes()
        payload, exit_code = wrapper.run_guarded_execution(
            paths=self.paths,
            execution_date=self.target,
            mode="dry_run",
            engine_invoker=fake_invoker,
        )
        self.assertEqual(0, exit_code)
        self.assertEqual(PASS, payload["gate_status"])
        self.assertTrue(payload["engine_invoked"])
        self.assertEqual(1, len(calls))
        self.assertEqual("dry_run", calls[0][1])
        self.assertEqual(trades_before, self.paths.trades_file.read_bytes())
        self.assertEqual(positions_before, self.paths.positions_file.read_bytes())
        self.assertTrue(self.paths.preflight_json.exists())
        self.assertTrue(self.paths.preflight_md.exists())
        self.assertEqual(1, len(self.paths.audit_jsonl.read_text(encoding="utf-8").splitlines()))

    def test_every_blocked_status_skips_engine(self) -> None:
        cases = [
            (BLOCKED_STALE_MARKET_DATA, lambda: write_update_status(self.root, latest="2026-07-09")),
            (BLOCKED_UPDATE_FAILURE, lambda: write_update_status(self.root, failed=1)),
            (BLOCKED_PENDING_DATA, lambda: write_update_status(self.root, pending=1)),
            (BLOCKED_INCOMPLETE_COVERAGE, lambda: write_watchlist(self.root, ["510300", "510500", "512100"])),
            (BLOCKED_STALE_SIGNAL, lambda: (write_signals(self.root, "2026-07-09"), write_sell_review(self.root, "2026-07-09"))),
            (BLOCKED_STALE_RANKING, lambda: write_ranking(self.root, "2026-07-09", "510500")),
            (BLOCKED_MISSING_SYMBOL_BAR, lambda: write_ranking(self.root, TARGET_DATE, "512100")),
            (BLOCKED_INVALID_INPUT, lambda: self.paths.data_update_status.unlink()),
        ]
        for expected_status, mutate in cases:
            with self.subTest(expected_status=expected_status):
                self.temp.cleanup()
                self.temp = tempfile.TemporaryDirectory()
                self.root = Path(self.temp.name)
                build_gate_fixture(self.root)
                self.paths = GatePaths.from_root(self.root)
                mutate()
                calls = []
                payload, exit_code = wrapper.run_guarded_execution(
                    paths=self.paths,
                    execution_date=self.target,
                    mode="dry_run",
                    engine_invoker=lambda *args: calls.append(args) or {"exit_code": 0},
                )
                self.assertEqual(expected_status, payload["gate_status"])
                self.assertNotEqual(0, exit_code)
                self.assertFalse(payload["engine_invoked"])
                self.assertEqual([], calls)

    def test_default_invoker_targets_existing_engine_cli(self) -> None:
        completed = type("Completed", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()
        with patch.object(wrapper.subprocess, "run", return_value=completed) as run:
            result = wrapper._invoke_existing_engine(self.root, "dry_run", False, date.today())
        command = run.call_args.args[0]
        self.assertEqual(str(self.root / "src" / "paper_trade_engine.py"), command[1])
        self.assertEqual("--dry-run", command[2])
        self.assertEqual(0, result["exit_code"])


if __name__ == "__main__":
    unittest.main()
