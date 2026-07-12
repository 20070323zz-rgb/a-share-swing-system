import csv
from pathlib import Path

from scripts.download_manual_etf_history import CSV_COLUMNS, merge_existing_history


def _row(date: str, close: str) -> dict[str, str]:
    return {
        "date": date,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": "100",
        "amount": "1000",
    }


def test_narrow_refresh_extends_existing_history(tmp_path: Path) -> None:
    target = tmp_path / "510300.csv"
    with target.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows([_row("2022-01-04", "1.0"), _row("2025-12-31", "2.0")])

    merged = merge_existing_history(target, [_row("2026-07-08", "3.0")])

    assert [row["date"] for row in merged] == ["2022-01-04", "2025-12-31", "2026-07-08"]


def test_downloaded_row_wins_only_on_overlapping_date(tmp_path: Path) -> None:
    target = tmp_path / "510300.csv"
    with target.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerow(_row("2026-07-08", "1.0"))

    merged = merge_existing_history(target, [_row("2026-07-08", "1.1")])

    assert len(merged) == 1
    assert merged[0]["close"] == "1.1"
