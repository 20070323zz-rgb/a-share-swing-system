#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

STATUS=0

ok() {
  echo "OK      $*"
}

warn() {
  echo "CAUTION $*"
}

fail() {
  echo "ERROR   $*"
  STATUS=1
}

check_file() {
  local path="$1"
  if [ -s "$path" ]; then
    ok "$path exists"
  else
    fail "$path missing or empty"
  fi
}

check_file "APP_VERSION"
check_file "RELEASE_NOTES.md"
check_file "docs/app_release_checklist.md"
check_file "docs/local_app_release_guide.md"
check_file "app/frontend/dist/index.html"
check_file "dashboard/index.html"
check_file "reports/dashboard_data.json"
check_file "reports/paper_performance_summary.md"
check_file "reports/trade_review_summary.md"

if [ -x "打开量化研究控制台.command" ]; then
  ok "打开量化研究控制台.command executable"
else
  warn "打开量化研究控制台.command is not executable; run chmod +x"
fi

if [ -x "A-Share Swing App.command" ]; then
  ok "A-Share Swing App.command executable"
else
  warn "A-Share Swing App.command is not executable; run chmod +x"
fi

if grep -RInE "Execute Trade|Place Order|Live Trading|Broker Login|real_buy|real_sell" app/frontend/src >/tmp/a_share_release_forbidden.txt 2>/dev/null; then
  cat /tmp/a_share_release_forbidden.txt
  fail "forbidden real-trading UI keywords found"
else
  ok "no forbidden real-trading UI keywords"
fi
rm -f /tmp/a_share_release_forbidden.txt

if grep -RInE "Local Paper Trading Control Room|Whitelisted tasks|Paper Portfolio|Safety Boundary|Execution Disabled|Research Only|Shadow Only|Forward Return|Evidence Level" app/frontend/src >/tmp/a_share_release_english_ui.txt 2>/dev/null; then
  cat /tmp/a_share_release_english_ui.txt
  fail "visible English UI copy should be replaced with concise Chinese"
else
  ok "main UI copy is Chinese-first"
fi
rm -f /tmp/a_share_release_english_ui.txt

if grep -RIn "backfill_etf_data" app/backend/safe_tasks.py app/frontend/src >/tmp/a_share_release_backfill_task.txt 2>/dev/null; then
  ok "backfill_etf_data safe task exists"
else
  fail "backfill_etf_data safe task missing"
fi
rm -f /tmp/a_share_release_backfill_task.txt

if grep -RIn "一键补齐 ETF 数据" app/frontend/src >/tmp/a_share_release_backfill_label.txt 2>/dev/null; then
  ok "Chinese backfill CTA exists"
else
  fail "一键补齐 ETF 数据 CTA missing"
fi
rm -f /tmp/a_share_release_backfill_label.txt

if grep -RInE "JQDATA_PASSWORD|TUSHARE_TOKEN|BAOSTOCK_PASSWORD|password[[:space:]]*[:=]|token[[:space:]]*[:=]|api[_-]?key[[:space:]]*[:=]" app/frontend/src >/tmp/a_share_release_secret.txt 2>/dev/null; then
  cat /tmp/a_share_release_secret.txt
  fail "potential hard-coded secret pattern found in frontend source"
else
  ok "no obvious hard-coded secret pattern in frontend source"
fi
rm -f /tmp/a_share_release_secret.txt

if grep -RInE ">[^<]*(NaN|undefined|null|\\[object Object\\])|title=\"[^\"]*(NaN|undefined|null|\\[object Object\\])" app/frontend/dist/index.html dashboard/index.html >/tmp/a_share_release_empty_state.txt 2>/dev/null; then
  cat /tmp/a_share_release_empty_state.txt
  fail "developer empty-state text found in built UI"
else
  ok "no NaN/undefined/null/[object Object] visible text in built UI"
fi
rm -f /tmp/a_share_release_empty_state.txt

echo "Result: $([ "$STATUS" -eq 0 ] && echo OK || echo ERROR)"
exit "$STATUS"
