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
MODEL_RESEARCH_STATUS=0
MARKET_STATE_STATUS=0
ETF_CLASSIFIER_STATUS=0
PORTFOLIO_EXPOSURE_STATUS=0
STRATEGY_PREVIEW_STATUS=0
STRATEGY_TRACKING_STATUS=0
PERSISTENCE_SHADOW_STATUS=0
MISSED_OPPORTUNITY_STATUS=0
TRADE_REVIEW_STATUS=0
PAPER_PERFORMANCE_STATUS=0
DATA_STATUS_JSON="reports/data_update_status.json"
SOURCE_STATUS_BACKUP=""
SOURCE_REPORT_BACKUP=""
UPDATE_STATUS_BACKUP=""
if [ "${DAILY_CLOSE_DRY_RUN:-0}" = "1" ]; then
  DATA_STATUS_JSON="reports/data_update_status.dryrun.json"
  SOURCE_STATUS_BACKUP="$(mktemp)"
  SOURCE_REPORT_BACKUP="$(mktemp)"
  UPDATE_STATUS_BACKUP="$(mktemp)"
  [ -f "reports/data_source_status.json" ] && cp "reports/data_source_status.json" "$SOURCE_STATUS_BACKUP"
  [ -f "reports/data_source_status_report.md" ] && cp "reports/data_source_status_report.md" "$SOURCE_REPORT_BACKUP"
  [ -f "reports/data_update_status.json" ] && cp "reports/data_update_status.json" "$UPDATE_STATUS_BACKUP"
  export PAPER_PORTFOLIO_READONLY=1
fi
CMD1=("$PYTHON_BIN" scripts/update_etf_data.py --source auto --primary baostock --fallback jqdata --all-etf --skip-existing --skip-backfill --max-api-calls 50000 --end "$(date '+%Y-%m-%d')" --adjustflag 2 --request-timeout 20 --login-retries 2 --login-retry-delay 3 --retries 1 --retry-delay 2 --request-interval 0.05 --relogin-every 60 --max-consecutive-failures 20 --strict-exit --status-json "$DATA_STATUS_JSON")
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
# Rollback: restore src/paper_trade_engine.py here only with Main approval.
CMD5=("$PYTHON_BIN" scripts/run_paper_execution_guarded.py "$ENGINE_MODE")
CMD6=("$PYTHON_BIN" src/paper_portfolio.py)
CMD7=("$PYTHON_BIN" src/automation_nodes.py --node daily_rolling_backtest)
CMD8=("$PYTHON_BIN" src/automation_nodes.py --node sync_report)
CMD9=("$PYTHON_BIN" src/model_research.py)
CMD10=("$PYTHON_BIN" src/market_state.py)
CMD11=("$PYTHON_BIN" src/etf_classifier.py)
CMD12=("$PYTHON_BIN" src/portfolio_exposure.py)
CMD13=("$PYTHON_BIN" src/strategy_enhancement_preview.py)
CMD14=("$PYTHON_BIN" src/strategy_preview_tracking.py)
CMD15=("$PYTHON_BIN" src/persistence_breakout_shadow.py)
CMD16=("$PYTHON_BIN" src/missed_opportunity_tracker.py)
CMD17=("$PYTHON_BIN" dashboard/build_dashboard.py)
CMD18=("$PYTHON_BIN" src/trade_review.py)
CMD19=("$PYTHON_BIN" src/paper_performance.py)

echo "running command: ${CMD1[*]}" >> "$LOG_FILE" 2>&1
"${CMD1[@]}" >> "$LOG_FILE" 2>&1 || DATA_STATUS=$?

if [ "${DAILY_CLOSE_DRY_RUN:-0}" = "1" ]; then
  [ -s "$SOURCE_STATUS_BACKUP" ] && cp "$SOURCE_STATUS_BACKUP" "reports/data_source_status.json"
  [ -s "$SOURCE_REPORT_BACKUP" ] && cp "$SOURCE_REPORT_BACKUP" "reports/data_source_status_report.md"
  [ -s "$UPDATE_STATUS_BACKUP" ] && cp "$UPDATE_STATUS_BACKUP" "reports/data_update_status.json"
  rm -f "$SOURCE_STATUS_BACKUP" "$SOURCE_REPORT_BACKUP" "$UPDATE_STATUS_BACKUP"
fi

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

echo "running command: ${CMD10[*]}" >> "$LOG_FILE" 2>&1
"${CMD10[@]}" >> "$LOG_FILE" 2>&1 || MARKET_STATE_STATUS=$?

echo "running command: ${CMD11[*]}" >> "$LOG_FILE" 2>&1
"${CMD11[@]}" >> "$LOG_FILE" 2>&1 || ETF_CLASSIFIER_STATUS=$?

echo "running command: ${CMD12[*]}" >> "$LOG_FILE" 2>&1
"${CMD12[@]}" >> "$LOG_FILE" 2>&1 || PORTFOLIO_EXPOSURE_STATUS=$?

echo "running command: ${CMD13[*]}" >> "$LOG_FILE" 2>&1
"${CMD13[@]}" >> "$LOG_FILE" 2>&1 || STRATEGY_PREVIEW_STATUS=$?

echo "running command: ${CMD14[*]}" >> "$LOG_FILE" 2>&1
"${CMD14[@]}" >> "$LOG_FILE" 2>&1 || STRATEGY_TRACKING_STATUS=$?

echo "running command: ${CMD15[*]}" >> "$LOG_FILE" 2>&1
"${CMD15[@]}" >> "$LOG_FILE" 2>&1 || PERSISTENCE_SHADOW_STATUS=$?

echo "running command: ${CMD16[*]}" >> "$LOG_FILE" 2>&1
"${CMD16[@]}" >> "$LOG_FILE" 2>&1 || MISSED_OPPORTUNITY_STATUS=$?

echo "running command: ${CMD18[*]}" >> "$LOG_FILE" 2>&1
"${CMD18[@]}" >> "$LOG_FILE" 2>&1 || TRADE_REVIEW_STATUS=$?

echo "running command: ${CMD19[*]}" >> "$LOG_FILE" 2>&1
"${CMD19[@]}" >> "$LOG_FILE" 2>&1 || PAPER_PERFORMANCE_STATUS=$?

echo "running command: ${CMD7[*]}" >> "$LOG_FILE" 2>&1
"${CMD7[@]}" >> "$LOG_FILE" 2>&1 || ROLLING_STATUS=$?

echo "running command: ${CMD8[*]}" >> "$LOG_FILE" 2>&1
"${CMD8[@]}" >> "$LOG_FILE" 2>&1 || SYNC_STATUS=$?

echo "running command: ${CMD9[*]}" >> "$LOG_FILE" 2>&1
"${CMD9[@]}" >> "$LOG_FILE" 2>&1 || MODEL_RESEARCH_STATUS=$?

echo "running command: ${CMD17[*]}" >> "$LOG_FILE" 2>&1
"${CMD17[@]}" >> "$LOG_FILE" 2>&1 || DASHBOARD_STATUS=$?

if [ "$DASHBOARD_STATUS" -ne 0 ]; then
  log_failure "$DASHBOARD_STATUS" "${CMD17[*]}" "dashboard generation failed"
fi

if [ "$ROLLING_STATUS" -ne 0 ]; then
  log_failure "$ROLLING_STATUS" "${CMD7[*]}" "daily rolling backtest failed"
fi

if [ "$SYNC_STATUS" -ne 0 ]; then
  log_failure "$SYNC_STATUS" "${CMD8[*]}" "automation sync report failed"
fi

if [ "$MODEL_RESEARCH_STATUS" -ne 0 ]; then
  log_failure "$MODEL_RESEARCH_STATUS" "${CMD9[*]}" "model research report failed; continuing with other reports"
fi

if [ "$MARKET_STATE_STATUS" -ne 0 ]; then
  log_failure "$MARKET_STATE_STATUS" "${CMD10[*]}" "market state research failed; continuing with daily close"
fi

if [ "$ETF_CLASSIFIER_STATUS" -ne 0 ]; then
  log_failure "$ETF_CLASSIFIER_STATUS" "${CMD11[*]}" "ETF classifier research failed; continuing with daily close"
fi

if [ "$PORTFOLIO_EXPOSURE_STATUS" -ne 0 ]; then
  log_failure "$PORTFOLIO_EXPOSURE_STATUS" "${CMD12[*]}" "portfolio exposure research failed; continuing with daily close"
fi

if [ "$STRATEGY_PREVIEW_STATUS" -ne 0 ]; then
  log_failure "$STRATEGY_PREVIEW_STATUS" "${CMD13[*]}" "strategy enhancement preview failed; continuing without changing paper trades"
fi

if [ "$STRATEGY_TRACKING_STATUS" -ne 0 ]; then
  log_failure "$STRATEGY_TRACKING_STATUS" "${CMD14[*]}" "strategy preview tracking failed; continuing without changing paper trades"
fi

if [ "$PERSISTENCE_SHADOW_STATUS" -ne 0 ]; then
  log_failure "$PERSISTENCE_SHADOW_STATUS" "${CMD15[*]}" "persistence breakout shadow failed; continuing without changing paper trades"
fi

if [ "$MISSED_OPPORTUNITY_STATUS" -ne 0 ]; then
  log_failure "$MISSED_OPPORTUNITY_STATUS" "${CMD16[*]}" "missed opportunity tracker failed; continuing without changing paper trades"
fi

if [ "$TRADE_REVIEW_STATUS" -ne 0 ]; then
  log_failure "$TRADE_REVIEW_STATUS" "${CMD18[*]}" "trade review failed; continuing without changing paper trades"
fi

if [ "$PAPER_PERFORMANCE_STATUS" -ne 0 ]; then
  log_failure "$PAPER_PERFORMANCE_STATUS" "${CMD19[*]}" "paper performance failed; continuing without changing paper trades"
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

if [ "$REPORT_STATUS" -eq 0 ] && [ "$DATA_STATUS" -eq 0 ] && [ "$DASHBOARD_STATUS" -eq 0 ] && [ "$ROLLING_STATUS" -eq 0 ] && [ "$SYNC_STATUS" -eq 0 ] && [ "$SELL_REVIEW_STATUS" -eq 0 ] && [ "$PORTFOLIO_STATUS" -eq 0 ] && [ "$ENGINE_STATUS" -eq 0 ] && [ "$PORTFOLIO_AFTER_ENGINE_STATUS" -eq 0 ] && [ "$MODEL_RESEARCH_STATUS" -eq 0 ] && [ "$MARKET_STATE_STATUS" -eq 0 ] && [ "$ETF_CLASSIFIER_STATUS" -eq 0 ] && [ "$PORTFOLIO_EXPOSURE_STATUS" -eq 0 ] && [ "$STRATEGY_PREVIEW_STATUS" -eq 0 ] && [ "$STRATEGY_TRACKING_STATUS" -eq 0 ] && [ "$PERSISTENCE_SHADOW_STATUS" -eq 0 ] && [ "$MISSED_OPPORTUNITY_STATUS" -eq 0 ] && [ "$TRADE_REVIEW_STATUS" -eq 0 ] && [ "$PAPER_PERFORMANCE_STATUS" -eq 0 ]; then
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
