from __future__ import annotations

import csv
import json
from pathlib import Path


TARGET_DATE = "2026-07-10"


def build_gate_fixture(root: Path) -> None:
    (root / "reports").mkdir(parents=True)
    (root / "data" / "etf_daily").mkdir(parents=True)
    (root / "data" / "audit").mkdir(parents=True)
    (root / "src").mkdir(parents=True)
    (root / "src" / "paper_trade_engine.py").write_text("# test placeholder\n", encoding="utf-8")
    write_update_status(root)
    write_watchlist(root, ["510300", "510500"])
    write_signals(root, TARGET_DATE)
    write_sell_review(root, TARGET_DATE)
    write_ranking(root, TARGET_DATE, "510500")
    write_positions(root)
    write_trades(root, [])
    write_bar(root, "510300", [("2026-07-09", 4.8), (TARGET_DATE, 4.9)])
    write_bar(root, "510500", [("2026-07-09", 6.1), (TARGET_DATE, 6.2)])
    (root / "reports" / "data_coverage_report.md").write_text("# Coverage\n\nValid.\n", encoding="utf-8")
    (root / "reports" / "latest_data_health.md").write_text("# Health\n\nValid.\n", encoding="utf-8")


def write_update_status(root: Path, *, latest: str = TARGET_DATE, failed: int = 0, pending: int = 0) -> None:
    payload = {"latest_data_date": latest, "failed_count": failed, "pending_count": pending}
    (root / "reports" / "data_update_status.json").write_text(json.dumps(payload), encoding="utf-8")


def write_watchlist(root: Path, symbols: list[str]) -> None:
    rows = [
        {"code": symbol, "name": symbol, "type": "ETF", "source": "auto", "enabled": "1", "role": "trade_pool"}
        for symbol in symbols
    ]
    _write_csv(root / "watchlist.csv", ["code", "name", "type", "source", "enabled", "role"], rows)


def write_signals(root: Path, signal_date: str) -> None:
    rows = [{"date": signal_date, "code": "510500", "signal": "BUY"}]
    _write_csv(root / "reports" / "signals.csv", ["date", "code", "signal"], rows)


def write_sell_review(root: Path, review_date: str) -> None:
    rows = [{"review_date": review_date, "symbol": "510300", "sell_review_status": "HOLD"}]
    _write_csv(root / "reports" / "sell_signal_review.csv", ["review_date", "symbol", "sell_review_status"], rows)


def write_ranking(root: Path, ranking_date: str, symbol: str) -> None:
    text = f"""# BUY ETF 排名报告 {ranking_date}

## Top BUY Ranking
| rank | code | name | mid | short |
| ---: | --- | --- | --- | --- |
| 1 | {symbol} | Candidate | BUY | BUY |
"""
    (root / "reports" / "buy_signal_ranking.md").write_text(text, encoding="utf-8")


def write_positions(root: Path) -> None:
    rows = [{"symbol": "510300", "quantity": "100"}]
    _write_csv(root / "data" / "paper_positions.csv", ["symbol", "quantity"], rows)


def write_trades(root: Path, rows: list[dict[str, str | int | float]]) -> None:
    fields = [
        "date",
        "trade_date",
        "symbol",
        "name",
        "action",
        "quantity",
        "price",
        "execution_price",
        "raw_close",
        "source",
        "created_at",
    ]
    _write_csv(root / "data" / "paper_trades.csv", fields, rows)


def write_bar(root: Path, symbol: str, rows: list[tuple[str, float]]) -> None:
    prefix = "sh" if symbol.startswith(("5", "6")) else "sz"
    values = [{"date": day, "close": close, "volume": 1000} for day, close in rows]
    _write_csv(root / "data" / "etf_daily" / f"{prefix}_{symbol}.csv", ["date", "close", "volume"], values)


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
