# Phase 3B Dynamic App Control Room Upgrade Report

Generated at: 2026-06-17

## Scope

This upgrade turns the FastAPI + React/Vite dynamic app from a basic local dashboard into a paper-trading control room. It remains a local-only paper-trading and research interface.

## Changed Files

- `app/backend/main.py`
- `app/backend/readers.py`
- `app/backend/safe_tasks.py`
- `app/backend/schemas.py`
- `app/backend/task_runner.py`
- `app/frontend/index.html`
- `app/frontend/src/App.jsx`
- `app/frontend/src/api.js`
- `app/frontend/src/components/ActionButton.jsx`
- `app/frontend/src/components/DataHealthPanel.jsx`
- `app/frontend/src/components/LogsPanel.jsx`
- `app/frontend/src/components/PortfolioPanel.jsx`
- `app/frontend/src/components/SignalsPanel.jsx`
- `app/frontend/src/components/TaskPanel.jsx`
- `app/frontend/src/format.js`
- `app/frontend/src/pages/ControlRoom.jsx`
- `app/frontend/src/pages/DataCenter.jsx`
- `app/frontend/src/pages/Logs.jsx`
- `app/frontend/src/pages/Portfolio.jsx`
- `app/frontend/src/pages/Research.jsx`
- `app/frontend/src/pages/Signals.jsx`
- `app/frontend/src/pages/SettingsSafety.jsx`
- `app/frontend/src/styles.css`
- `dashboard/build_dashboard.py`
- `dashboard/index.html`
- `reports/dashboard_data.json`

## Backend API

App version is now `phase3b_app_control_room_upgrade_v1`.

Added or enhanced:

- `/api/status`: includes `system_status`, `today_conclusion`, data source status, paper portfolio summary, app launch info and execution safety.
- `/api/data-health`: includes daily update status, source routing, latest date, failed symbols and BaoStock call summary.
- `/api/tasks/status`: now supports task history and duration labels.
- `/api/logs?name=...`: whitelist includes latest app task log and app server log.
- `/api/app-env`: read-only environment check; does not print `.env` contents.
- `/api/safety`: reports paper-only safety switches and forbidden real-trading actions.

## Task System

Added safe whitelist tasks:

- `check_app_env`
- `check_data_source`

Task runner now keeps latest task plus up to 10 recent history rows. The frontend still cannot submit arbitrary commands.

## Frontend

Main navigation:

- Control Room
- Data Center
- Portfolio
- Signals
- Research
- Tasks & Logs
- Settings / Safety

Key UI changes:

- Dark professional control-room style.
- First screen shows system conclusion, status, latest data date, source used, paper equity, position value and risk warnings.
- Data Center shows BaoStock/JQData/fallback source routing.
- Portfolio page prioritizes decision fields: signal state, stop distance, risk tag and action suggestion.
- Signals page shows original ranking vs adjusted preview ranking, top3 changes, bonus/penalty effects and BUY ranking breakdown.
- Research page shows Phase 2B quality review and execution-layer integration recommendations.
- Tasks & Logs page shows safe task history and whitelisted logs only.
- Settings / Safety page shows all real-trading capabilities disabled.

## Dashboard Snapshot

`reports/dashboard_data.json` now uses:

```text
app_ready_snapshot_version = phase3b_app_control_room_upgrade_v1
```

Added:

- `app_control_room`
- expanded `execution_safety`
- `app_task_status.history`

Preserved:

- `data_sources`
- `dynamic_app`
- `desktop_app`
- `app_launch`
- `paper_trade_engine`
- `positions_enhanced`
- `strategy_enhancement_preview`
- `strategy_preview_tracking`

## Validation

Passed:

- Python compile for backend and dashboard builder.
- Shell syntax check for app scripts.
- `scripts/check_app_env.sh`.
- React/Vite production build.
- Local app startup at `http://127.0.0.1:8000`.
- API checks for `/api/status`, `/api/data-health`, `/api/tasks/status`, `/api/safety`, `/api/app-env`.
- Browser desktop rendering check.
- Browser mobile-width rendering check.
- No JavaScript console errors observed.
- Safe task `check_app_env` completed successfully.
- Safe task `run_daily_close_dryrun` completed successfully.

Paper file hashes were unchanged after dry-run:

- `data/paper_trades.csv`: `e3c43a6aee418666fb19460a7bb7ddeb846ced2220b8ab4030bda0d373666425`
- `data/paper_positions.csv`: `a81540633b71178ea98d0772ca43a9800daa35eeadecf34ee3d2b41464a48a31`

## Safety Boundary

Confirmed unchanged:

- No broker API.
- No real order placement.
- No real account reading.
- No password/token printing.
- No arbitrary command execution from the App.
- No real-trading buttons.
- Adjusted ranking and shadow model remain preview/research only.
- `paper_trades.csv` not modified by this upgrade validation.
- `paper_positions.csv` not modified by this upgrade validation.

