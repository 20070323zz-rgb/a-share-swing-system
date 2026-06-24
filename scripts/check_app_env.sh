#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
FRONTEND_DIST="$PROJECT_ROOT/app/frontend/dist/index.html"
BACKEND_MAIN="$PROJECT_ROOT/app/backend/main.py"
DASHBOARD_DATA="$PROJECT_ROOT/reports/dashboard_data.json"
ENV_FILE="$PROJECT_ROOT/.env"
PORT="8000"

OK_COUNT=0
CAUTION_COUNT=0
ERROR_COUNT=0

ok() {
  OK_COUNT=$((OK_COUNT + 1))
  echo "OK      $*"
}

caution() {
  CAUTION_COUNT=$((CAUTION_COUNT + 1))
  echo "CAUTION $*"
}

error() {
  ERROR_COUNT=$((ERROR_COUNT + 1))
  echo "ERROR   $*"
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

echo "A-share Swing App environment check"
echo "Project root: $PROJECT_ROOT"
echo

if [ -d "$PROJECT_ROOT" ]; then
  ok "项目根目录存在：$PROJECT_ROOT"
else
  error "项目根目录不存在：$PROJECT_ROOT"
fi

if [ -d "$PROJECT_ROOT/.venv" ]; then
  ok ".venv 存在"
else
  error ".venv 不存在。建议在项目根目录恢复或创建虚拟环境。"
fi

if [ -x "$PYTHON_BIN" ]; then
  ok ".venv/bin/python 可执行：$PYTHON_BIN"
else
  error ".venv/bin/python 不存在或不可执行。"
fi

if [ -x "$PYTHON_BIN" ] && "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import fastapi
PY
then
  ok "fastapi 可 import"
else
  error "fastapi 不可 import。修复：.venv/bin/pip install fastapi"
fi

if [ -x "$PYTHON_BIN" ] && "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import uvicorn
PY
then
  ok "uvicorn 可 import"
else
  error "uvicorn 不可 import。修复：.venv/bin/pip install uvicorn"
fi

if command_exists npm; then
  ok "npm 可用：$(command -v npm)"
else
  caution "npm 不可用。若 app/frontend/dist 已存在仍可启动；否则需安装 Node.js/npm。"
fi

if [ -f "$FRONTEND_DIST" ]; then
  ok "前端 dist 存在：$FRONTEND_DIST"
else
  if command_exists npm; then
    caution "前端 dist 不存在。run_app.sh 会尝试 npm install && npm run build。"
  else
    error "前端 dist 不存在且 npm 不可用。修复：安装 Node.js/npm 后运行 npm build。"
  fi
fi

if [ -f "$ENV_FILE" ]; then
  ok ".env 存在；检查不打印内容"
else
  caution ".env 不存在。App 可启动，但 JQData/Tushare 等账号型数据源会按未配置处理。"
fi

if [ -f "$DASHBOARD_DATA" ]; then
  ok "dashboard_data.json 存在：$DASHBOARD_DATA"
else
  caution "dashboard_data.json 不存在。修复：.venv/bin/python dashboard/build_dashboard.py"
fi

if command_exists lsof; then
  PIDS="$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null | sort -u || true)"
  if [ -z "$PIDS" ]; then
    ok "8000 端口当前未占用"
  else
    if [ -x "$PYTHON_BIN" ] && "$PYTHON_BIN" - <<PY >/dev/null 2>&1
import json
import urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:$PORT/api/status", timeout=2) as response:
        payload = json.loads(response.read().decode("utf-8"))
    raise SystemExit(0 if payload.get("real_trade_enabled") is False and payload.get("broker_api_enabled") is False else 1)
except Exception:
    raise SystemExit(1)
PY
    then
      ok "8000 端口已被本项目 App 使用；可直接打开 http://127.0.0.1:$PORT"
    else
      caution "8000 端口已被占用。若不是本项目 App，请关闭占用程序后再启动。PIDs: $PIDS"
    fi
  fi
else
  caution "lsof 不可用，无法检查 8000 端口占用。"
fi

if [ -f "$BACKEND_MAIN" ]; then
  ok "app/backend/main.py 存在"
else
  error "app/backend/main.py 不存在"
fi

if [ -x "$PYTHON_BIN" ] && (cd "$PROJECT_ROOT" && "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import app.backend.main
PY
); then
  ok "app/backend/main.py 可 import"
else
  error "app/backend/main.py import 失败。请检查 FastAPI 依赖和项目路径。"
fi

echo
echo "Summary: OK=$OK_COUNT CAUTION=$CAUTION_COUNT ERROR=$ERROR_COUNT"
if [ "$ERROR_COUNT" -gt 0 ]; then
  echo "Result: ERROR"
  exit 1
fi
if [ "$CAUTION_COUNT" -gt 0 ]; then
  echo "Result: CAUTION"
  exit 0
fi
echo "Result: OK"
