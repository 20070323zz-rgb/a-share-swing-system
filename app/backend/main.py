"""FastAPI entry point for the Phase 3B dynamic control room."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .readers import (
    PROJECT_ROOT,
    app_env_snapshot,
    app_task_status,
    dashboard_data,
    data_health_snapshot,
    execution_safety_snapshot,
    log_tail,
    portfolio_snapshot,
    research_snapshot,
    signals_snapshot,
    status_snapshot,
)
from .schemas import RunTaskRequest
from .safe_tasks import SAFE_TASKS
from .task_runner import read_status, start_task


FRONTEND_DIST = PROJECT_ROOT / "app" / "frontend" / "dist"
REPORTS_DIR = PROJECT_ROOT / "reports"
APP_VERSION_FILE = PROJECT_ROOT / "APP_VERSION"
APP_VERSION = APP_VERSION_FILE.read_text(encoding="utf-8").strip() if APP_VERSION_FILE.exists() else "0.2.0-local"

app = FastAPI(
    title="A-share ETF Paper Trading Control Room",
    version=APP_VERSION,
    description="Local-only FastAPI backend for the ETF paper-trading research system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/status")
def api_status() -> dict:
    return status_snapshot()


@app.get("/api/dashboard-data")
def api_dashboard_data() -> dict:
    data = dashboard_data()
    if isinstance(data, dict):
        data.setdefault("app_ready_snapshot_version", APP_VERSION)
    return data


@app.get("/api/portfolio")
def api_portfolio() -> dict:
    return portfolio_snapshot()


@app.get("/api/signals")
def api_signals() -> dict:
    return signals_snapshot()


@app.get("/api/data-health")
def api_data_health() -> dict:
    return data_health_snapshot()


@app.get("/api/app-env")
def api_app_env() -> dict:
    return app_env_snapshot()


@app.get("/api/safety")
def api_safety() -> dict:
    return execution_safety_snapshot()


@app.get("/api/research")
def api_research() -> dict:
    return research_snapshot()


@app.get("/api/logs")
def api_logs(name: str = Query("daily_close.log")) -> dict:
    return log_tail(name)


@app.get("/api/tasks")
def api_tasks() -> dict:
    return {
        "tasks": [
            {
                "task_name": task.name,
                "description": task.description,
                "safe_note": task.safe_note,
                "modifies_paper_positions": task.modifies_paper_positions,
                "real_trade": task.real_trade,
            }
            for task in SAFE_TASKS.values()
        ],
        "forbidden": ["real_buy", "real_sell", "broker_login", "read_real_account", "sync_real_position"],
    }


@app.get("/api/tasks/status")
def api_task_status() -> dict:
    status = read_status()
    if not status.get("latest_task") and app_task_status().get("latest_task"):
        return app_task_status()
    return status


@app.post("/api/tasks/run")
def api_run_task(payload: RunTaskRequest) -> dict:
    return start_task(payload.task_name, payload.target_business_date)


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

if REPORTS_DIR.exists():
    app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str) -> Any:
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "React frontend has not been built yet.",
        "next_step": "cd app/frontend && npm install && npm run build",
        "api_docs": "/docs",
    }
