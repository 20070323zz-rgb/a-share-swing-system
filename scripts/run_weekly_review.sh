#!/bin/bash
set -u

PROJECT_ROOT="/Users/dayin/Documents/量化学习/a-share-swing-system"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/weekly_review.log"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT" || exit 1

{
  echo "============================================================"
  echo "weekly review started at $(date '+%Y-%m-%d %H:%M:%S')"
  echo "current working directory: $(pwd)"
  echo "python path: $PYTHON_BIN"
  echo "running command: $PYTHON_BIN src/main.py --weekly"
} >> "$LOG_FILE" 2>&1

STATUS=0
"$PYTHON_BIN" src/main.py --weekly >> "$LOG_FILE" 2>&1 || STATUS=$?

{
  if [ "$STATUS" -eq 0 ]; then
    echo "status: success"
  else
    echo "status: failed, exit code $STATUS"
  fi
  echo "weekly review finished at $(date '+%Y-%m-%d %H:%M:%S')"
} >> "$LOG_FILE" 2>&1

exit "$STATUS"
