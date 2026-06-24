"""Request/response schemas for the local dynamic app."""

from __future__ import annotations

from typing import Literal

try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover - keeps py_compile usable before deps install
    class BaseModel:  # type: ignore
        pass

    def Field(default=None, **_: object):  # type: ignore
        return default


AllowedTaskName = Literal[
    "check_app_env",
    "check_data_source",
    "health_check",
    "update_daily_data",
    "backfill_etf_data",
    "backfill_recent_data",
    "run_daily_close_dryrun",
    "run_paper_engine_dryrun",
    "run_paper_performance",
    "run_trade_review",
    "run_paper_equity_backfill",
    "create_app_shortcut",
    "diagnose_app_launch",
    "fix_app_launch_permissions",
    "run_strategy_preview",
    "run_strategy_tracking",
    "run_strategy_preview_tracking",
    "run_persistence_breakout_shadow",
    "run_missed_opportunity_tracker",
    "run_shadow_observation_weekly",
    "build_dashboard",
    "run_dashboard_build",
    "refresh_all_reports",
]


class RunTaskRequest(BaseModel):
    task_name: AllowedTaskName = Field(..., description="Whitelisted task name only.")
