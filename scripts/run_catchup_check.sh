#!/bin/bash
set -u

TASK_NAME="catchup_check"
PROJECT_ROOT="/Users/dayin/Code/a-share-swing-system"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/catchup_check.log"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT" || exit 1

ARGS=()
if [ "$#" -gt 0 ]; then
  ARGS=("$@")
elif [ "${AUTOMATION_CATCHUP_REAL:-0}" != "1" ]; then
  ARGS=("--dry-run")
fi
ARGS_TEXT="${ARGS[*]-}"

{
  echo "============================================================"
  echo "[$(timestamp)] $TASK_NAME started"
  echo "============================================================"
  echo "current working directory: $(pwd)"
  echo "python path: $PYTHON_BIN"
  echo "running command: $PYTHON_BIN src/automation_scheduler.py --mode catchup $ARGS_TEXT"
} >> "$LOG_FILE" 2>&1

STATUS=0
if [ "${#ARGS[@]}" -gt 0 ]; then
  "$PYTHON_BIN" src/automation_scheduler.py --mode catchup "${ARGS[@]}" >> "$LOG_FILE" 2>&1 || STATUS=$?
else
  "$PYTHON_BIN" src/automation_scheduler.py --mode catchup >> "$LOG_FILE" 2>&1 || STATUS=$?
fi

{
  echo "[$(timestamp)] $TASK_NAME finished: $([ "$STATUS" -eq 0 ] && echo success || echo failed)"
  echo
} >> "$LOG_FILE" 2>&1

exit "$STATUS"
