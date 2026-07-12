from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

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
)
from paper_gate_test_utils import (  # noqa: E402
    TARGET_DATE,
    build_gate_fixture,
    write_bar,
    write_ranking,
    write_sell_review,
    write_signals,
    write_trades,
    write_update_status,
    write_watchlist,
)


class FreshnessGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        build_gate_fixture(self.root)
        self.paths = GatePaths.from_root(self.root)
        self.target = date.fromisoformat(TARGET_DATE)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def evaluate(self) -> dict:
        return evaluate_freshness_gate(self.paths, self.target)

    def test_complete_inputs_pass(self) -> None:
        payload = self.evaluate()
        self.assertEqual(PASS, payload["gate_status"])
        self.assertEqual(2, payload["required_symbol_count"])
        self.assertEqual(2, payload["covered_symbol_count"])

    def test_empty_but_structurally_valid_ranking_can_pass_for_sell_review(self) -> None:
        (self.root / "reports" / "buy_signal_ranking.md").write_text(
            f"# BUY ETF 排名报告 {TARGET_DATE}\n\n"
            "## Top BUY Ranking\n"
            "| rank | code | name | mid | short |\n"
            "| ---: | --- | --- | --- | --- |\n",
            encoding="utf-8",
        )
        payload = self.evaluate()
        self.assertEqual(PASS, payload["gate_status"])
        self.assertEqual(["510300"], payload["proposed_trade_symbols"])

    def test_stale_market_data_blocks(self) -> None:
        write_update_status(self.root, latest="2026-07-09")
        self.assertEqual(BLOCKED_STALE_MARKET_DATA, self.evaluate()["gate_status"])

    def test_update_failure_blocks(self) -> None:
        write_update_status(self.root, failed=1)
        self.assertEqual(BLOCKED_UPDATE_FAILURE, self.evaluate()["gate_status"])

    def test_pending_data_blocks(self) -> None:
        write_update_status(self.root, pending=2)
        self.assertEqual(BLOCKED_PENDING_DATA, self.evaluate()["gate_status"])

    def test_incomplete_formal_universe_blocks(self) -> None:
        write_watchlist(self.root, ["510300", "510500", "512100"])
        self.assertEqual(BLOCKED_INCOMPLETE_COVERAGE, self.evaluate()["gate_status"])

    def test_stale_signal_blocks(self) -> None:
        write_signals(self.root, "2026-07-09")
        write_sell_review(self.root, "2026-07-09")
        self.assertEqual(BLOCKED_STALE_SIGNAL, self.evaluate()["gate_status"])

    def test_stale_ranking_blocks(self) -> None:
        write_ranking(self.root, "2026-07-09", "510500")
        self.assertEqual(BLOCKED_STALE_RANKING, self.evaluate()["gate_status"])

    def test_missing_proposed_symbol_bar_blocks(self) -> None:
        write_ranking(self.root, TARGET_DATE, "512100")
        self.assertEqual(BLOCKED_MISSING_SYMBOL_BAR, self.evaluate()["gate_status"])

    def test_non_trading_day_skips(self) -> None:
        payload = evaluate_freshness_gate(self.paths, date.fromisoformat("2026-07-11"))
        self.assertEqual(SKIPPED_NON_TRADING_DAY, payload["gate_status"])

    def test_invalid_critical_input_blocks(self) -> None:
        self.paths.data_update_status.unlink()
        self.assertEqual(BLOCKED_INVALID_INPUT, self.evaluate()["gate_status"])

    def test_historical_stale_trade_audit_is_idempotent_and_non_destructive(self) -> None:
        rows = []
        for symbol, action, raw_close, execution_price in [
            ("512800", "SELL", 0.761, 0.760772),
            ("516510", "BUY", 1.805, 1.805541),
            ("159929", "BUY", 1.259, 1.259378),
        ]:
            rows.append({
                "date": TARGET_DATE,
                "trade_date": TARGET_DATE,
                "symbol": symbol,
                "name": symbol,
                "action": action,
                "quantity": 100,
                "price": execution_price,
                "execution_price": execution_price,
                "raw_close": raw_close,
                "source": "paper_trade_engine",
                "created_at": f"{TARGET_DATE} 16:28:05",
            })
        write_trades(self.root, rows)
        write_bar(self.root, "512800", [("2026-07-09", 0.761), (TARGET_DATE, 0.767)])
        write_bar(self.root, "516510", [("2026-07-09", 1.805), (TARGET_DATE, 1.821)])
        write_bar(self.root, "159929", [("2026-07-09", 1.259), (TARGET_DATE, 1.286)])
        before = self.paths.trades_file.read_bytes()
        first = audit_historical_stale_trades(self.paths, self.target)
        second = audit_historical_stale_trades(self.paths, self.target)
        json_path, md_path = write_historical_audit_report(second, self.paths, self.target)
        self.assertEqual(3, len(first))
        self.assertEqual(3, len(second))
        self.assertEqual(3, len(self.paths.audit_jsonl.read_text(encoding="utf-8").splitlines()))
        self.assertEqual(before, self.paths.trades_file.read_bytes())
        report_payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(3, report_payload["record_count"])
        self.assertEqual(3, len(report_payload["records"]))
        self.assertIn("non-destructive", md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
