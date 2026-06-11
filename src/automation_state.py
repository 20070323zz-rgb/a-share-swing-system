"""State file helper for launchd automation.

This module only records local scheduler status. It does not connect to broker
APIs, place orders, or read account credentials.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

import pandas as pd

from config import DATA_DIR


STATE_FILE = DATA_DIR / "automation_state.json"
VALID_STATUSES = {"pending", "success", "failed", "missed", "missed_after_close", "skipped"}
VALID_SOURCES = {"launchd", "manual", "catchup", "scheduler", "test", "unknown"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="自动化节点状态记录工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    mark = sub.add_parser("mark", help="记录节点状态")
    mark.add_argument("--node", required=True)
    mark.add_argument("--status", required=True, choices=sorted(VALID_STATUSES))
    mark.add_argument("--source", default="manual")
    mark.add_argument("--date")
    mark.add_argument("--error", default="")
    mark.add_argument("--note", default="")

    status = sub.add_parser("status", help="打印当前状态 JSON")
    status.add_argument("--date")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cmd == "mark":
        mark_node(
            node=args.node,
            status=args.status,
            source=args.source,
            date=args.date,
            error=args.error,
            note=args.note,
        )
    elif args.cmd == "status":
        print(json.dumps(read_state().get(_state_date(args.date), {}), ensure_ascii=False, indent=2))


def read_state() -> dict:
    if not STATE_FILE.exists() or STATE_FILE.stat().st_size == 0:
        write_state({})
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = STATE_FILE.with_suffix(".json.broken")
        STATE_FILE.replace(backup)
        return {}


def write_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=STATE_FILE.parent, delete=False) as tmp:
        json.dump(state, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(STATE_FILE)


def mark_node(
    node: str,
    status: str,
    source: str = "manual",
    date: str | None = None,
    error: str = "",
    note: str = "",
) -> dict:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    if source not in VALID_SOURCES:
        source = "unknown"
    state = read_state()
    day = _state_date(date)
    state.setdefault(day, {})
    record = {
        "status": status,
        "last_run": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
    }
    if error:
        record["error"] = str(error)[:500]
    if note:
        record["note"] = str(note)[:500]
    state[day][node] = record
    write_state(state)
    return record


def get_day_state(date: str | None = None) -> dict:
    return read_state().get(_state_date(date), {})


def is_success(node: str, date: str | None = None) -> bool:
    return get_day_state(date).get(node, {}).get("status") == "success"


def _state_date(date: str | None = None) -> str:
    return pd.to_datetime(date).strftime("%Y-%m-%d") if date else pd.Timestamp.now().strftime("%Y-%m-%d")


if __name__ == "__main__":
    main()
