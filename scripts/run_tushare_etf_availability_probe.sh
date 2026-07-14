#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON=""
CANDIDATES=(
  "${A_SHARE_AUDIT_PYTHON:-}"
  "$PROJECT_ROOT/.venv/bin/python"
  "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
  "/usr/local/bin/python3"
  "/opt/homebrew/bin/python3"
  "$(command -v python3 || true)"
)

for candidate in "${CANDIDATES[@]}"; do
  if [ -n "$candidate" ] && [ -x "$candidate" ] && "$candidate" -c "import pandas, yaml" >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done

if [ -z "$PYTHON" ]; then
  echo "No Python interpreter with pandas and yaml is available; no probe was attempted." >&2
  exit 2
fi

mkdir -p "$PROJECT_ROOT/logs"
cd "$PROJECT_ROOT"
"$PYTHON" scripts/run_tushare_etf_availability_probe.py --source scheduled --reconcile-missed
