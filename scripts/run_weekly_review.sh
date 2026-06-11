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
COMMAND="$PYTHON_BIN src/main.py --weekly"
"$PYTHON_BIN" src/main.py --weekly >> "$LOG_FILE" 2>&1 || STATUS=$?
if [ "$STATUS" -eq 0 ]; then
  "$PYTHON_BIN" src/automation_nodes.py --node weekly_full_review >> "$LOG_FILE" 2>&1 || STATUS=$?
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
