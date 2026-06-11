#!/bin/bash
set -u

TASK_NAME="midday_check"
PROJECT_ROOT="/Users/dayin/Code/a-share-swing-system"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/midday_check.log"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

mark_state() {
  local status_text="$1"
  local error_text="${2:-}"
  local source_text="${AUTOMATION_SOURCE:-launchd}"
  "$PYTHON_BIN" src/automation_state.py mark --node "$TASK_NAME" --status "$status_text" --source "$source_text" --error "$error_text" >> "$LOG_FILE" 2>&1 || true
}

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT" || exit 1

{
  echo "============================================================"
  echo "[$(timestamp)] $TASK_NAME started"
  echo "============================================================"
  echo "current working directory: $(pwd)"
  echo "python path: $PYTHON_BIN"
} >> "$LOG_FILE" 2>&1

STATUS=0
"$PYTHON_BIN" src/automation_nodes.py --node midday_check >> "$LOG_FILE" 2>&1 || STATUS=$?
if [ "$STATUS" -eq 0 ]; then
  "$PYTHON_BIN" dashboard/build_dashboard.py >> "$LOG_FILE" 2>&1 || STATUS=$?
fi

{
  echo "[$(timestamp)] $TASK_NAME finished: $([ "$STATUS" -eq 0 ] && echo success || echo failed)"
  echo
} >> "$LOG_FILE" 2>&1

if [ "$STATUS" -eq 0 ]; then
  mark_state "success"
else
  mark_state "failed" "exit code $STATUS"
fi

exit "$STATUS"
