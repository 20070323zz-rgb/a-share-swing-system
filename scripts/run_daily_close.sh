#!/bin/bash
set -u

PROJECT_ROOT="/Users/dayin/Documents/量化学习/a-share-swing-system"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/daily_close.log"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT" || exit 1

{
  echo "============================================================"
  echo "daily close started at $(date '+%Y-%m-%d %H:%M:%S')"
  echo "current working directory: $(pwd)"
  echo "python path: $PYTHON_BIN"
} >> "$LOG_FILE" 2>&1

DATA_STATUS=0
REPORT_STATUS=0
CMD1=("$PYTHON_BIN" scripts/update_etf_data.py --end "$(date '+%Y-%m-%d')" --adjustflag 2)
CMD2=("$PYTHON_BIN" src/main.py)

echo "running command: ${CMD1[*]}" >> "$LOG_FILE" 2>&1
"${CMD1[@]}" >> "$LOG_FILE" 2>&1 || DATA_STATUS=$?

if [ "$DATA_STATUS" -ne 0 ]; then
  echo "data update failed with exit code $DATA_STATUS; continuing to generate reports from local cached data" >> "$LOG_FILE" 2>&1
fi

echo "running command: ${CMD2[*]}" >> "$LOG_FILE" 2>&1
"${CMD2[@]}" >> "$LOG_FILE" 2>&1 || REPORT_STATUS=$?

{
  if [ "$DATA_STATUS" -eq 0 ] && [ "$REPORT_STATUS" -eq 0 ]; then
    echo "status: success"
  elif [ "$REPORT_STATUS" -eq 0 ]; then
    echo "status: success with data update warning, data exit code $DATA_STATUS"
  else
    echo "status: failed, data exit code $DATA_STATUS, report exit code $REPORT_STATUS"
  fi
  echo "daily close finished at $(date '+%Y-%m-%d %H:%M:%S')"
} >> "$LOG_FILE" 2>&1

exit "$REPORT_STATUS"
