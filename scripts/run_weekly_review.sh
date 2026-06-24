#!/bin/bash
set -u

TASK_NAME="weekly_review"
PROJECT_ROOT="/Users/dayin/Code/a-share-swing-system"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/weekly_review.log"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

mark_state() {
  local status_text="$1"
  local error_text="${2:-}"
  local source_text="${AUTOMATION_SOURCE:-launchd}"
  "$PYTHON_BIN" src/automation_state.py mark --node "$TASK_NAME" --status "$status_text" --source "$source_text" --error "$error_text" >> "$LOG_FILE" 2>&1 || true
}

log_start() {
  {
    echo "============================================================"
    echo "[$(timestamp)] $TASK_NAME started"
    echo "============================================================"
    echo "current working directory: $(pwd)"
    echo "python path: $PYTHON_BIN"
    echo "running command: $PYTHON_BIN src/main.py --weekly"
    echo "running command: $PYTHON_BIN src/automation_nodes.py --node weekly_full_review"
    echo "running command: $PYTHON_BIN src/holding_period_research.py"
    echo "running command: $PYTHON_BIN src/exit_rule_research.py"
    echo "running command: $PYTHON_BIN src/parameter_sweep.py"
    echo "running command: $PYTHON_BIN src/persistence_breakout_shadow.py"
    echo "running command: $PYTHON_BIN src/missed_opportunity_tracker.py"
    echo "running command: $PYTHON_BIN src/shadow_observation_weekly.py"
    echo "running command: $PYTHON_BIN src/trade_review.py"
  } >> "$LOG_FILE" 2>&1
}

log_failure() {
  local exit_code="$1"
  local failed_command="$2"
  {
    echo "[$(timestamp)] $TASK_NAME error"
    echo "task: $TASK_NAME"
    echo "current working directory: $(pwd)"
    echo "python path: $PYTHON_BIN"
    echo "failed command: $failed_command"
    echo "exit code: $exit_code"
    echo "message: weekly report generation failed; check the command output above"
  } >> "$LOG_FILE" 2>&1
}

log_finish() {
  local status_text="$1"
  {
    echo "[$(timestamp)] $TASK_NAME finished: $status_text"
    echo
  } >> "$LOG_FILE" 2>&1
}

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT" || exit 1

log_start
STATUS=0
PERSISTENCE_SHADOW_STATUS=0
MISSED_OPPORTUNITY_STATUS=0
SHADOW_OBSERVATION_STATUS=0
TRADE_REVIEW_STATUS=0
COMMAND="$PYTHON_BIN src/main.py --weekly"
"$PYTHON_BIN" src/main.py --weekly >> "$LOG_FILE" 2>&1 || STATUS=$?
if [ "$STATUS" -eq 0 ]; then
  "$PYTHON_BIN" src/automation_nodes.py --node weekly_full_review >> "$LOG_FILE" 2>&1 || STATUS=$?
fi
if [ "$STATUS" -eq 0 ]; then
  "$PYTHON_BIN" src/holding_period_research.py >> "$LOG_FILE" 2>&1 || STATUS=$?
fi
if [ "$STATUS" -eq 0 ]; then
  "$PYTHON_BIN" src/exit_rule_research.py >> "$LOG_FILE" 2>&1 || STATUS=$?
fi
if [ "$STATUS" -eq 0 ]; then
  "$PYTHON_BIN" src/parameter_sweep.py >> "$LOG_FILE" 2>&1 || STATUS=$?
fi
if [ "$STATUS" -eq 0 ]; then
  "$PYTHON_BIN" src/persistence_breakout_shadow.py >> "$LOG_FILE" 2>&1 || PERSISTENCE_SHADOW_STATUS=$?
  if [ "$PERSISTENCE_SHADOW_STATUS" -ne 0 ]; then
    {
      echo "[$(timestamp)] $TASK_NAME warning"
      echo "warning command: $PYTHON_BIN src/persistence_breakout_shadow.py"
      echo "exit code: $PERSISTENCE_SHADOW_STATUS"
      echo "message: persistence breakout shadow failed; continuing weekly review without changing paper trades"
    } >> "$LOG_FILE" 2>&1
  fi
fi
if [ "$STATUS" -eq 0 ]; then
  "$PYTHON_BIN" src/missed_opportunity_tracker.py >> "$LOG_FILE" 2>&1 || MISSED_OPPORTUNITY_STATUS=$?
  if [ "$MISSED_OPPORTUNITY_STATUS" -ne 0 ]; then
    {
      echo "[$(timestamp)] $TASK_NAME warning"
      echo "warning command: $PYTHON_BIN src/missed_opportunity_tracker.py"
      echo "exit code: $MISSED_OPPORTUNITY_STATUS"
      echo "message: missed opportunity tracker failed; continuing weekly review without changing paper trades"
    } >> "$LOG_FILE" 2>&1
  fi
fi
if [ "$STATUS" -eq 0 ]; then
  "$PYTHON_BIN" src/shadow_observation_weekly.py >> "$LOG_FILE" 2>&1 || SHADOW_OBSERVATION_STATUS=$?
  if [ "$SHADOW_OBSERVATION_STATUS" -ne 0 ]; then
    {
      echo "[$(timestamp)] $TASK_NAME warning"
      echo "warning command: $PYTHON_BIN src/shadow_observation_weekly.py"
      echo "exit code: $SHADOW_OBSERVATION_STATUS"
      echo "message: shadow observation weekly failed; continuing weekly review without changing paper trades"
    } >> "$LOG_FILE" 2>&1
  fi
fi
if [ "$STATUS" -eq 0 ]; then
  "$PYTHON_BIN" src/trade_review.py >> "$LOG_FILE" 2>&1 || TRADE_REVIEW_STATUS=$?
  if [ "$TRADE_REVIEW_STATUS" -ne 0 ]; then
    {
      echo "[$(timestamp)] $TASK_NAME warning"
      echo "warning command: $PYTHON_BIN src/trade_review.py"
      echo "exit code: $TRADE_REVIEW_STATUS"
      echo "message: trade review failed; continuing weekly review without changing paper trades"
    } >> "$LOG_FILE" 2>&1
  fi
fi
if [ "$STATUS" -eq 0 ]; then
  "$PYTHON_BIN" src/automation_nodes.py --node sync_report >> "$LOG_FILE" 2>&1 || STATUS=$?
fi
if [ "$STATUS" -eq 0 ]; then
  "$PYTHON_BIN" dashboard/build_dashboard.py >> "$LOG_FILE" 2>&1 || STATUS=$?
fi

if [ "$STATUS" -eq 0 ]; then
  mark_state "success"
  log_finish "success"
else
  mark_state "failed" "exit code $STATUS"
  log_failure "$STATUS" "$COMMAND"
  log_finish "failed"
fi

exit "$STATUS"
