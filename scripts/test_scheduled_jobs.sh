#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/Users/dayin/Documents/量化学习/a-share-swing-system"
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

echo "Running local scheduled-job scripts..."
echo "1/3 open check"
bash scripts/run_open_check.sh
echo "2/3 daily close"
bash scripts/run_daily_close.sh
echo "3/3 weekly review"
bash scripts/run_weekly_review.sh

echo
echo "Recent script logs:"
for log in \
  "$LOG_DIR/open_check.log" \
  "$LOG_DIR/daily_close.log" \
  "$LOG_DIR/weekly_review.log"; do
  echo "============================================================"
  echo "$log"
  if [ -f "$log" ]; then
    tail -n 40 "$log"
  else
    echo "not found"
  fi
done

echo
echo "Recent launchd stdout/stderr logs, if present:"
for log in \
  "$LOG_DIR/launchd_open_check.out.log" \
  "$LOG_DIR/launchd_open_check.err.log" \
  "$LOG_DIR/launchd_daily_close.out.log" \
  "$LOG_DIR/launchd_daily_close.err.log" \
  "$LOG_DIR/launchd_weekly_review.out.log" \
  "$LOG_DIR/launchd_weekly_review.err.log"; do
  echo "============================================================"
  echo "$log"
  if [ -f "$log" ]; then
    tail -n 40 "$log"
  else
    echo "not found yet"
  fi
done

echo
echo "Local test finished. This test only runs report/data scripts and does not connect to broker APIs or place real orders."
