"""Shared models and constants for ETF availability timing evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


CRITICAL_FIELDS = ("open", "high", "low", "close")
SNAPSHOT_FIELDS = (
    "ts_code", "trade_date", "open", "high", "low", "close",
    "pre_close", "change", "pct_chg", "vol", "amount",
)


@dataclass(frozen=True)
class UniverseRecord:
    etf_code: str
    ts_code: str
    exchange: str
    universe_role: str
    file_path: str


@dataclass(frozen=True)
class AuditPaths:
    project_root: Path
    staging_root: Path
    reports_dir: Path
    status_report: Path
    timing_summary: Path
    source_comparison: Path
    universe_mapping: Path
    calendar_cache: Path
    calendar_history: Path

    @classmethod
    def from_config(cls, project_root: Path, config: dict[str, Any]) -> "AuditPaths":
        root = project_root.resolve()
        storage = config["storage"]
        return cls(
            project_root=root,
            staging_root=root / storage["root"],
            reports_dir=root / storage["reports_dir"],
            status_report=root / storage["status_report"],
            timing_summary=root / storage["timing_summary"],
            source_comparison=root / storage["source_comparison"],
            universe_mapping=root / storage["universe_mapping"],
            calendar_cache=root / config["calendar"]["cache_file"],
            calendar_history=root / config["calendar"]["history_dir"],
        )


def iso_time(value: datetime) -> str:
    return value.isoformat(timespec="seconds")
