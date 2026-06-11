#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/Users/dayin/Code/a-share-swing-system"
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

echo "Running local scheduled-job scripts..."
echo "1/7 open check"
AUTOMATION_SOURCE=test bash scripts/run_open_check.sh
echo "2/7 midday check"
AUTOMATION_SOURCE=test bash scripts/run_midday_check.sh
echo "3/7 afternoon open check"
AUTOMATION_SOURCE=test bash scripts/run_afternoon_open_check.sh
echo "4/7 daily close safe dry-run"
AUTOMATION_SOURCE=test DAILY_CLOSE_DRY_RUN=1 bash scripts/run_daily_close.sh
echo "5/7 weekly review"
AUTOMATION_SOURCE=test bash scripts/run_weekly_review.sh
echo "6/7 monthly model review"
AUTOMATION_SOURCE=test bash scripts/run_monthly_model_review.sh
echo "7/7 catchup check dry-run"
bash scripts/run_catchup_check.sh --dry-run

echo
echo "Recent script logs:"
for log in \
  "$LOG_DIR/open_check.log" \
  "$LOG_DIR/catchup_check.log" \
  "$LOG_DIR/midday_check.log" \
  "$LOG_DIR/afternoon_open_check.log" \
  "$LOG_DIR/daily_close.log" \
  "$LOG_DIR/weekly_review.log" \
  "$LOG_DIR/monthly_model_review.log"; do
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
  "$LOG_DIR/launchd_catchup_check.out.log" \
  "$LOG_DIR/launchd_catchup_check.err.log" \
  "$LOG_DIR/launchd_midday_check.out.log" \
  "$LOG_DIR/launchd_midday_check.err.log" \
  "$LOG_DIR/launchd_afternoon_open_check.out.log" \
  "$LOG_DIR/launchd_afternoon_open_check.err.log" \
  "$LOG_DIR/launchd_daily_close.out.log" \
  "$LOG_DIR/launchd_daily_close.err.log" \
  "$LOG_DIR/launchd_weekly_review.out.log" \
  "$LOG_DIR/launchd_weekly_review.err.log" \
  "$LOG_DIR/launchd_monthly_model_review.out.log" \
  "$LOG_DIR/launchd_monthly_model_review.err.log"; do
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
