from __future__ import annotations

import unittest

import pandas as pd

from app.backend.readers import build_equity_curve_meta, merge_equity_curves
from dashboard.build_dashboard import _merge_equity_curve_frames


def _row(date: str, equity: float, source: str) -> dict:
    return {"date": date, "total_equity": equity, "source": source}


class EquityCurveFreshnessTests(unittest.TestCase):
    def test_reader_merge_keeps_backfill_history_and_prefers_newer_formal_rows(self) -> None:
        backfilled = [
            _row("2026-07-05", 10000.0, "backfilled"),
            _row("2026-07-06", 10015.11, "backfilled"),
        ]
        original = [
            _row("2026-07-06", 10020.0, "original"),
            _row("2026-07-10", 9989.77, "original"),
        ]

        merged = merge_equity_curves(backfilled, original)

        self.assertEqual([row["date"] for row in merged], ["2026-07-05", "2026-07-06", "2026-07-10"])
        self.assertEqual(merged[1]["total_equity"], 10020.0)
        self.assertEqual(merged[-1]["source"], "original")

    def test_reader_meta_uses_date_freshness_instead_of_row_count(self) -> None:
        backfilled = [_row("2026-07-05", 10000.0, "backfilled"), _row("2026-07-06", 10015.11, "backfilled")]
        original = [_row("2026-07-10", 9989.77, "original")]
        merged = merge_equity_curves(backfilled, original)

        meta = build_equity_curve_meta(merged, original, backfilled, "2026-07-10")

        self.assertEqual(meta["freshness_status"], "fresh")
        self.assertEqual(meta["curve_end_date"], "2026-07-10")
        self.assertEqual(meta["curve_source"], "merged_backfill_and_original")
        self.assertTrue(meta["app_uses_backfilled_curve"])

    def test_dashboard_merge_prefers_original_on_duplicate_dates(self) -> None:
        backfilled = pd.DataFrame([_row("2026-07-06", 10015.11, "backfilled")])
        original = pd.DataFrame(
            [
                _row("2026-07-06", 10020.0, "original"),
                _row("2026-07-10", 9989.77, "original"),
            ]
        )

        merged = _merge_equity_curve_frames(backfilled, original)

        self.assertEqual(merged["date"].tolist(), ["2026-07-06", "2026-07-10"])
        self.assertEqual(float(merged.iloc[0]["total_equity"]), 10020.0)
        self.assertEqual(merged.iloc[-1]["source"], "original")


if __name__ == "__main__":
    unittest.main()
