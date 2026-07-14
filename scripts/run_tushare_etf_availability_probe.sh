#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$PROJECT_ROOT/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  PYTHON="$(command -v python3)"
fi

mkdir -p "$PROJECT_ROOT/logs"
cd "$PROJECT_ROOT"
"$PYTHON" scripts/run_tushare_etf_availability_probe.py --source scheduled --reconcile-missed
