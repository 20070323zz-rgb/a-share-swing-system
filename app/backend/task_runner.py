"""Background runner for whitelisted app tasks."""

from __future__ import annotations

import json
import subprocess
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .readers import PROJECT_ROOT, REPORT_DIR
from .safe_tasks import (
    StableObservationUnavailableError,
    TargetDateMismatchError,
    TaskSpec,
    get_task,
    merged_env,
    resolve_backfill_target,
)


LOG_DIR = PROJECT_ROOT / "logs" / "app_tasks"
STATUS_FILE = REPORT_DIR / "app_task_status.json"
LATEST_LOG_FILE = LOG_DIR / "latest.log"
_LOCK = threading.Lock()
_RUNNING_THREAD: threading.Thread | None = None


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _duration(started_at: str | None, finished_at: str | None = None) -> tuple[int | None, str]:
    start = _parse_time(started_at)
    if start is None:
        return None, "N/A"
    finish = _parse_time(finished_at) if finished_at else datetime.now()
    if finish is None:
        return None, "N/A"
    seconds = max(0, int((finish - start).total_seconds()))
    minutes, remain = divmod(seconds, 60)
    if minutes:
        return seconds, f"{minutes}m {remain}s"
    return seconds, f"{remain}s"


def _tail(text: str, limit: int = 4000) -> str:
    return text[-limit:] if len(text) > limit else text


def read_status() -> dict[str, Any]:
    try:
        if STATUS_FILE.exists():
            payload = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
            latest = payload.get("latest_task") if isinstance(payload, dict) else None
            if isinstance(latest, dict) and latest.get("task_name") in {"backfill_etf_data", "backfill_recent_data", "update_daily_data"}:
                data_status = _task_data_update_status(str(latest.get("task_name")))
                if data_status:
                    enriched = dict(latest)
                    enriched.update(
                        {
                            "data_update_processed_symbols": data_status.get("processed_symbols", 0),
                            "data_update_up_to_date_count": data_status.get("up_to_date_count", 0),
                            "data_update_actual_api_calls": data_status.get("actual_api_calls", 0),
                            "data_update_provider": data_status.get("provider", ""),
                            "data_update_result_code": data_status.get("result_code", ""),
                            "data_update_business_date": data_status.get("business_date", ""),
                            "data_update_updated_count": data_status.get("updated_count", 0),
                            "data_update_ssot_manifest_hash": data_status.get("ssot_manifest_hash", ""),
                            "data_update_requested_end": data_status.get("requested_end", enriched.get("data_update_requested_end", "")),
                        }
                    )
                    payload = dict(payload)
                    payload["latest_task"] = enriched
            return payload
    except Exception:
        pass
    return {"running": False, "latest_task": None, "history": []}


def write_status(payload: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def start_task(task_name: str, target_business_date: str | None = None) -> dict[str, Any]:
    global _RUNNING_THREAD
    stable_observation: dict[str, str] = {}
    if task_name == "backfill_etf_data":
        try:
            stable_observation = resolve_backfill_target(target_business_date)
        except TargetDateMismatchError as exc:
            return {
                "accepted": False,
                "result_code": "TARGET_DATE_MISMATCH",
                "requested_business_date": exc.requested,
                "latest_stable_business_date": exc.latest_stable,
            }
        except StableObservationUnavailableError:
            return {"accepted": False, "result_code": "DATA_NOT_READY"}
        target_business_date = stable_observation["business_date"]
    task = get_task(task_name, target_business_date)
    if task is None:
        return {"accepted": False, "error": f"task {task_name!r} is not in the safe whitelist"}
    with _LOCK:
        current = read_status()
        if current.get("running"):
            return {"accepted": False, "error": "another safe task is already running", "status": current}
        history = current.get("history", [])
        if not isinstance(history, list):
            history = []
        task_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        latest_task = {
            "task_id": task_id,
            "task_name": task.name,
            "description": task.description,
            "safe_note": task.safe_note,
            "status": "running",
            "started_at": _now(),
            "finished_at": None,
            "exit_code": None,
            "stdout_tail": "",
            "stderr_tail": "",
            "log_path": str(LOG_DIR / f"{task_id}_{task.name}.log"),
            "modifies_paper_positions": task.modifies_paper_positions,
            "real_trade": task.real_trade,
            "duration_seconds": None,
            "duration_label": "running",
            "target_business_date": target_business_date or "",
            "stable_observation_hash": stable_observation.get("manifest_hash", ""),
        }
        write_status({"running": True, "latest_task": latest_task, "history": history[-10:]})
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        LATEST_LOG_FILE.write_text(
            f"[{_now()}] safe task queued: {task.name}\n"
            f"description: {task.description}\n"
            f"safety: {task.safe_note}\n",
            encoding="utf-8",
        )
        _RUNNING_THREAD = threading.Thread(target=_run_task, args=(task_id, task), daemon=True)
        _RUNNING_THREAD.start()
    return {"accepted": True, "task": latest_task}


def _run_task(task_id: str, task: TaskSpec) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{task_id}_{task.name}.log"
    stdout_all: list[str] = []
    stderr_all: list[str] = []
    exit_code = 0
    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"[{_now()}] safe task started: {task.name}\n")
        log.write(f"description: {task.description}\n")
        log.write(f"safety: {task.safe_note}\n\n")
        for command in task.commands:
            log.write(f"[{_now()}] running: {' '.join(command.args)}\n")
            log.flush()
            proc = subprocess.run(
                command.args,
                cwd=PROJECT_ROOT,
                env=merged_env(command.env),
                text=True,
                capture_output=True,
            )
            if proc.stdout:
                log.write(proc.stdout)
                stdout_all.append(proc.stdout)
            if proc.stderr:
                log.write(proc.stderr)
                stderr_all.append(proc.stderr)
            log.write(f"\n[{_now()}] exit_code: {proc.returncode}\n\n")
            log.flush()
            if proc.returncode != 0:
                exit_code = proc.returncode
                break
        log.write(f"[{_now()}] safe task finished: exit_code={exit_code}\n")
    try:
        LATEST_LOG_FILE.write_text(log_path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    except Exception:
        pass
    status_before_finish = read_status()
    task_before_finish = status_before_finish.get("latest_task", {})
    started_at = task_before_finish.get("started_at")
    finished_at = _now()
    duration_seconds, duration_label = _duration(started_at, finished_at)
    data_update_status = _task_data_update_status(task.name)
    final_status = "success" if exit_code == 0 else "failed"
    if exit_code == 0 and _is_data_update_warning(data_update_status):
        final_status = "warning"
    latest_task = {
        "task_id": task_id,
        "task_name": task.name,
        "description": task.description,
        "safe_note": task.safe_note,
        "status": final_status,
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_code": exit_code,
        "stdout_tail": _tail("\n".join(stdout_all)),
        "stderr_tail": _tail("\n".join(stderr_all)),
        "warning": data_update_status.get("reason", "") if _is_data_update_warning(data_update_status) else "",
        "data_update_severity": data_update_status.get("severity", ""),
        "data_update_status": data_update_status.get("status", ""),
        "data_update_latest_local_date": data_update_status.get("latest_local_date", ""),
        "data_update_requested_end": data_update_status.get("requested_end", ""),
        "data_update_added_rows": data_update_status.get("added_rows", ""),
        "data_update_processed_symbols": data_update_status.get("processed_symbols", ""),
        "data_update_up_to_date_count": data_update_status.get("up_to_date_count", ""),
        "data_update_actual_api_calls": data_update_status.get("actual_api_calls", ""),
        "data_update_provider": data_update_status.get("provider", ""),
        "data_update_result_code": data_update_status.get("result_code", ""),
        "data_update_business_date": data_update_status.get("business_date", ""),
        "data_update_updated_count": data_update_status.get("updated_count", ""),
        "data_update_ssot_manifest_hash": data_update_status.get("ssot_manifest_hash", ""),
        "log_path": str(log_path),
        "modifies_paper_positions": task.modifies_paper_positions,
        "real_trade": task.real_trade,
        "duration_seconds": duration_seconds,
        "duration_label": duration_label,
        "target_business_date": task_before_finish.get("target_business_date", ""),
        "stable_observation_hash": task_before_finish.get("stable_observation_hash", ""),
    }
    history = status_before_finish.get("history", [])
    if not isinstance(history, list):
        history = []
    history = [latest_task] + [row for row in history if row.get("task_id") != task_id]
    write_status({"running": False, "latest_task": latest_task, "history": history[:10]})


def _task_data_update_status(task_name: str) -> dict[str, Any]:
    if task_name not in {"backfill_etf_data", "backfill_recent_data", "update_daily_data"}:
        return {}
    status_path = REPORT_DIR / "data_update_status.json"
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {
        "severity": str(payload.get("severity", "") or ""),
        "status": str(payload.get("status", "") or ""),
        "reason": payload.get("reason", ""),
        "latest_local_date": payload.get("latest_local_date", ""),
        "requested_end": payload.get("requested_end", ""),
        "added_rows": payload.get("added_rows", 0),
        "processed_symbols": payload.get("processed_symbols", 0),
        "up_to_date_count": payload.get("up_to_date_count", 0),
        "actual_api_calls": payload.get("actual_api_calls", payload.get("baostock_api_calls", 0)),
        "provider": payload.get("provider", payload.get("actual_source_used", "")),
        "result_code": payload.get("result_code", ""),
        "business_date": payload.get("business_date", payload.get("requested_end", "")),
        "updated_count": payload.get("updated_count", payload.get("up_to_date_count", 0)),
        "ssot_manifest_hash": payload.get("ssot_manifest_hash", payload.get("after_manifest_hash", payload.get("before_manifest_hash", ""))),
        "stale_vs_requested": payload.get("stale_vs_requested", False),
    }


def _is_data_update_warning(payload: dict[str, Any]) -> bool:
    if not payload:
        return False
    severity = str(payload.get("severity", "") or "").upper()
    if severity in {"CAUTION", "ERROR"}:
        return True
    try:
        added_rows = int(payload.get("added_rows", 0) or 0)
    except Exception:
        added_rows = 0
    return added_rows == 0 and bool(payload.get("stale_vs_requested", False))
