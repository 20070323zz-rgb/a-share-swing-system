#!/bin/bash
set -u

TASK_NAME="daily_close"
PROJECT_ROOT="/Users/dayin/Code/a-share-swing-system"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/daily_close.log"

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
  } >> "$LOG_FILE" 2>&1
}

log_failure() {
  local exit_code="$1"
  local failed_command="$2"
  local message="$3"
  {
    echo "[$(timestamp)] $TASK_NAME error"
    echo "task: $TASK_NAME"
    echo "current working directory: $(pwd)"
    echo "python path: $PYTHON_BIN"
    echo "failed command: $failed_command"
    echo "exit code: $exit_code"
    echo "message: $message"
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
DATA_STATUS=0
REPORT_STATUS=0
DASHBOARD_STATUS=0
ROLLING_STATUS=0
SYNC_STATUS=0
SELL_REVIEW_STATUS=0
PORTFOLIO_STATUS=0
ENGINE_STATUS=0
PORTFOLIO_AFTER_ENGINE_STATUS=0
CMD1=("$PYTHON_BIN" scripts/update_etf_data.py --source baostock --all-etf --skip-existing --skip-backfill --max-api-calls 50000 --end "$(date '+%Y-%m-%d')" --adjustflag 2)
if [ "${DAILY_CLOSE_DRY_RUN:-0}" = "1" ]; then
  CMD1+=("--dry-run")
fi
CMD2=("$PYTHON_BIN" src/main.py)
CMD3=("$PYTHON_BIN" src/paper_portfolio.py)
CMD4=("$PYTHON_BIN" src/sell_signal_review.py)
ENGINE_MODE="--execute"
if [ "${DAILY_CLOSE_DRY_RUN:-0}" = "1" ]; then
  ENGINE_MODE="--dry-run"
fi
CMD5=("$PYTHON_BIN" src/paper_trade_engine.py "$ENGINE_MODE")
CMD6=("$PYTHON_BIN" src/paper_portfolio.py)
CMD7=("$PYTHON_BIN" src/automation_nodes.py --node daily_rolling_backtest)
CMD8=("$PYTHON_BIN" src/automation_nodes.py --node sync_report)
CMD9=("$PYTHON_BIN" dashboard/build_dashboard.py)

echo "running command: ${CMD1[*]}" >> "$LOG_FILE" 2>&1
"${CMD1[@]}" >> "$LOG_FILE" 2>&1 || DATA_STATUS=$?

if [ "$DATA_STATUS" -ne 0 ]; then
  log_failure "$DATA_STATUS" "${CMD1[*]}" "data update failed; continuing to generate reports from local cached data"
fi

echo "running command: ${CMD2[*]}" >> "$LOG_FILE" 2>&1
"${CMD2[@]}" >> "$LOG_FILE" 2>&1 || REPORT_STATUS=$?

echo "running command: ${CMD3[*]}" >> "$LOG_FILE" 2>&1
"${CMD3[@]}" >> "$LOG_FILE" 2>&1 || PORTFOLIO_STATUS=$?

echo "running command: ${CMD4[*]}" >> "$LOG_FILE" 2>&1
"${CMD4[@]}" >> "$LOG_FILE" 2>&1 || SELL_REVIEW_STATUS=$?

echo "running command: ${CMD5[*]}" >> "$LOG_FILE" 2>&1
"${CMD5[@]}" >> "$LOG_FILE" 2>&1 || ENGINE_STATUS=$?

echo "running command: ${CMD6[*]}" >> "$LOG_FILE" 2>&1
"${CMD6[@]}" >> "$LOG_FILE" 2>&1 || PORTFOLIO_AFTER_ENGINE_STATUS=$?

echo "running command: ${CMD7[*]}" >> "$LOG_FILE" 2>&1
"${CMD7[@]}" >> "$LOG_FILE" 2>&1 || ROLLING_STATUS=$?

echo "running command: ${CMD8[*]}" >> "$LOG_FILE" 2>&1
"${CMD8[@]}" >> "$LOG_FILE" 2>&1 || SYNC_STATUS=$?

echo "running command: ${CMD9[*]}" >> "$LOG_FILE" 2>&1
"${CMD9[@]}" >> "$LOG_FILE" 2>&1 || DASHBOARD_STATUS=$?

if [ "$DASHBOARD_STATUS" -ne 0 ]; then
  log_failure "$DASHBOARD_STATUS" "${CMD9[*]}" "dashboard generation failed"
fi

if [ "$ROLLING_STATUS" -ne 0 ]; then
  log_failure "$ROLLING_STATUS" "${CMD7[*]}" "daily rolling backtest failed"
fi

if [ "$SYNC_STATUS" -ne 0 ]; then
  log_failure "$SYNC_STATUS" "${CMD8[*]}" "automation sync report failed"
fi

if [ "$SELL_REVIEW_STATUS" -ne 0 ]; then
  log_failure "$SELL_REVIEW_STATUS" "${CMD4[*]}" "sell signal review failed; continuing without trade changes"
fi

if [ "$PORTFOLIO_STATUS" -ne 0 ]; then
  log_failure "$PORTFOLIO_STATUS" "${CMD3[*]}" "paper portfolio refresh failed before paper trade engine"
fi

if [ "$ENGINE_STATUS" -ne 0 ]; then
  log_failure "$ENGINE_STATUS" "${CMD5[*]}" "paper trade engine failed; continuing without real trading"
fi

if [ "$PORTFOLIO_AFTER_ENGINE_STATUS" -ne 0 ]; then
  log_failure "$PORTFOLIO_AFTER_ENGINE_STATUS" "${CMD6[*]}" "paper portfolio refresh failed after paper trade engine"
fi

if [ "$REPORT_STATUS" -eq 0 ] && [ "$DATA_STATUS" -eq 0 ] && [ "$DASHBOARD_STATUS" -eq 0 ] && [ "$ROLLING_STATUS" -eq 0 ] && [ "$SYNC_STATUS" -eq 0 ] && [ "$SELL_REVIEW_STATUS" -eq 0 ] && [ "$PORTFOLIO_STATUS" -eq 0 ] && [ "$ENGINE_STATUS" -eq 0 ] && [ "$PORTFOLIO_AFTER_ENGINE_STATUS" -eq 0 ]; then
  mark_state "success"
  log_finish "success"
elif [ "$REPORT_STATUS" -eq 0 ]; then
  mark_state "success" "success with warning"
  log_finish "success with warning"
else
  mark_state "failed" "report exit code $REPORT_STATUS"
  log_failure "$REPORT_STATUS" "${CMD2[*]}" "daily report generation failed"
  log_finish "failed"
fi

exit "$REPORT_STATUS"
