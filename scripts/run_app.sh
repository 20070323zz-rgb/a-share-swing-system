#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
FRONTEND_DIR="$PROJECT_ROOT/app/frontend"
DIST_INDEX="$FRONTEND_DIR/dist/index.html"
HOST="127.0.0.1"
PORT="8000"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/app_server.log"
LAUNCH_STATUS_FILE="$LOG_DIR/app_launch_status.json"
APP_VERSION="$(cat "$PROJECT_ROOT/APP_VERSION" 2>/dev/null || echo "0.2.0-local")"

# macOS LaunchServices may inject this variable when a .app starts a Python
# process. It can make a virtualenv Python resolve packages incorrectly.
unset __PYVENV_LAUNCHER__
unset PYTHONHOME

# On Apple Silicon, LaunchServices may start shell scripts through Rosetta.
# The project venv contains arm64 native wheels, so relaunch this script as
# arm64 before importing compiled Python packages such as pydantic_core.
if [ "${A_SHARE_APP_ARCH_FIXED:-0}" != "1" ] && [ "$(uname -m)" = "x86_64" ] && /usr/bin/arch -arm64 /usr/bin/true >/dev/null 2>&1; then
  export A_SHARE_APP_ARCH_FIXED=1
  exec /usr/bin/arch -arm64 /bin/bash "$0" "$@"
fi

usage() {
  echo "用法：bash scripts/run_app.sh [--lan]"
  echo "  --lan  在可信局域网内开放访问，手机/同 Wi-Fi 设备可打开"
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

if [ "${1:-}" = "--lan" ]; then
  HOST="0.0.0.0"
elif [ "${1:-}" != "" ]; then
  echo "未知参数：$1"
  usage
  exit 2
fi

cd "$PROJECT_ROOT"
mkdir -p "$LOG_DIR"
if ! touch "$LOG_FILE" "$LAUNCH_STATUS_FILE" 2>/dev/null; then
  echo "[量化研究控制台][错误] 日志文件不可写：$LOG_DIR" >&2
  exit 1
fi
exec > >(tee -a "$LOG_FILE") 2>&1

LOCAL_URL="http://127.0.0.1:$PORT"
if [ "$HOST" = "0.0.0.0" ]; then
  DISPLAY_URL="$LOCAL_URL"
else
  DISPLAY_URL="http://$HOST:$PORT"
fi

info() {
  echo "[量化研究控制台] $*"
}

error() {
  echo "[量化研究控制台][错误] $*" >&2
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

json_python() {
  if [ -x "$PYTHON_BIN" ]; then
    echo "$PYTHON_BIN"
  else
    command -v python3 || true
  fi
}

write_launch_status() {
  local status_text="$1"
  local error_summary="${2:-}"
  local py_bin
  py_bin="$(json_python)"
  if [ -z "$py_bin" ]; then
    return 0
  fi
  "$py_bin" - "$LAUNCH_STATUS_FILE" "$PROJECT_ROOT" "$APP_VERSION" "$PORT" "$status_text" "$error_summary" "$LOG_FILE" <<'PY' || true
import json
import sys
from datetime import datetime
from pathlib import Path

out, project, version, port, status, error, log_path = sys.argv[1:8]
payload = {
    "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "project_dir": project,
    "app_version": version if str(version).startswith("v") else f"v{version}",
    "port": int(port),
    "status": status,
    "error_summary": error,
    "log_path": str(Path(log_path).relative_to(Path(project))) if str(log_path).startswith(str(project)) else log_path,
    "local_url": f"http://127.0.0.1:{port}",
    "safe_note": "本地研究 App；不接券商 API；不真实下单；不读取真实账户。",
}
Path(out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

port_pids() {
  if command_exists lsof; then
    lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null | sort -u || true
  fi
}

check_existing_app() {
  local pids
  pids="$(port_pids)"
  if [ -z "$pids" ]; then
    return 0
  fi

  if "$PYTHON_BIN" - <<PY >/dev/null 2>&1
import json
import urllib.request
try:
    with urllib.request.urlopen("$LOCAL_URL/api/status", timeout=2) as response:
        payload = json.loads(response.read().decode("utf-8"))
    raise SystemExit(0 if payload.get("real_trade_enabled") is False and payload.get("broker_api_enabled") is False else 1)
except Exception:
    raise SystemExit(1)
PY
  then
    write_launch_status "already_running" "研究控制台已经在运行，已直接打开浏览器。"
    info "端口 $PORT 已有本项目 App 在运行。"
    info "请直接访问：$LOCAL_URL"
    open "$LOCAL_URL" >/dev/null 2>&1 || true
    exit 0
  fi

  error "端口 $PORT 已被其他进程占用："
  for pid in $pids; do
    ps -p "$pid" -o pid=,comm=,args= 2>/dev/null || true
  done
  error "未自动结束任何进程。请关闭占用 8000 端口的程序后重试。"
  write_launch_status "error" "8000 端口被其他程序占用。"
  exit 3
}

write_launch_status "checking" "正在检查运行环境。"
info "正在检查运行环境。"
info "版本：v$APP_VERSION"
info "项目根目录：$PROJECT_ROOT"
info "启动模式：$([ "$HOST" = "0.0.0.0" ] && echo "局域网模式" || echo "本机模式")"
info "日志文件：$LOG_FILE"

if [ ! -d "$PROJECT_ROOT/.venv" ]; then
  error "未找到项目虚拟环境：$PROJECT_ROOT/.venv"
  error "请先在项目根目录创建或恢复 .venv，然后重试。"
  write_launch_status "error" ".venv 不存在。"
  exit 1
fi

if [ ! -x "$PYTHON_BIN" ]; then
  error "未找到可执行 Python：$PYTHON_BIN"
  error "请检查 .venv 是否完整。"
  write_launch_status "error" ".venv/bin/python 不可执行。"
  exit 1
fi

DEPS_CHECK_LOG="$LOG_DIR/app_dependency_check.log"
if ! "$PYTHON_BIN" - <<'PY' > "$DEPS_CHECK_LOG" 2>&1
import os
import sys
print("executable:", sys.executable)
print("prefix:", sys.prefix)
print("base_prefix:", sys.base_prefix)
print("__PYVENV_LAUNCHER__:", os.environ.get("__PYVENV_LAUNCHER__", ""))
print("PYTHONHOME:", os.environ.get("PYTHONHOME", ""))
print("sys.path:", sys.path)
import fastapi
import uvicorn
print("fastapi:", getattr(fastapi, "__version__", "unknown"))
print("uvicorn:", getattr(uvicorn, "__version__", "unknown"))
PY
then
  error "项目 .venv 缺少 fastapi 或 uvicorn。"
  error "依赖检查详情：$DEPS_CHECK_LOG"
  error "请执行：.venv/bin/pip install fastapi uvicorn"
  write_launch_status "error" "Python 依赖缺失：fastapi 或 uvicorn。"
  exit 1
fi

if [ -f "$PROJECT_ROOT/.env" ]; then
  info "检测到 .env：后端可使用本地环境配置；不会打印 .env 内容。"
else
  info "未检测到 .env：App 仍可启动，数据源账号相关功能会按未配置处理。"
fi

NEED_BUILD="0"
if [ ! -f "$DIST_INDEX" ]; then
  NEED_BUILD="1"
elif command_exists find; then
  UPDATED_SOURCE="$(find "$FRONTEND_DIR/src" "$FRONTEND_DIR/package.json" "$FRONTEND_DIR/index.html" -newer "$DIST_INDEX" -print -quit 2>/dev/null || true)"
  if [ -n "$UPDATED_SOURCE" ]; then
    NEED_BUILD="1"
  fi
fi

if [ "$NEED_BUILD" = "1" ]; then
  if command_exists npm; then
    write_launch_status "building_frontend" "前端页面需要构建。"
    info "检测到前端需要构建，开始准备 React/Vite 页面。"
    (
      cd "$FRONTEND_DIR"
      if [ ! -d node_modules ]; then
        info "首次启动需要安装前端依赖，请稍等。"
        npm install
      fi
      npm run build
    )
  else
    error "未找到 npm，且前端页面需要构建：$DIST_INDEX"
    error "请安装 Node.js/npm，或先在 PyCharm/终端执行一次前端构建。"
    write_launch_status "error" "前端未构建且未找到 npm。"
    exit 1
  fi
else
  info "前端页面已就绪，使用已有构建产物：$DIST_INDEX"
fi

info "正在检查端口。"
check_existing_app

write_launch_status "starting" "正在启动后端。"
info "本机访问：$LOCAL_URL"
if [ "$HOST" = "0.0.0.0" ]; then
  info "局域网访问：请在同一 Wi-Fi 设备打开 http://<你的Mac局域网IP>:$PORT"
fi
info "安全边界：只读看板和白名单模拟任务；不接券商 API；不真实下单。"
info "保持此终端窗口打开；关闭终端后 App 服务停止。"

(
  sleep 2
  info "正在打开浏览器：$LOCAL_URL"
  open "$LOCAL_URL" >/dev/null 2>&1 || true
) &

{
  echo
  echo "===== $(date '+%Y-%m-%d %H:%M:%S') app server start ====="
  echo "PROJECT_ROOT=$PROJECT_ROOT"
  echo "APP_VERSION=$APP_VERSION"
  echo "HOST=$HOST"
  echo "PORT=$PORT"
  echo "URL=$LOCAL_URL"
} >> "$LOG_FILE"

info "正在启动后端服务。启动完成后浏览器会打开控制台。"
write_launch_status "running" "启动完成。"
if "$PYTHON_BIN" -m uvicorn app.backend.main:app --host "$HOST" --port "$PORT" 2>&1 | tee -a "$LOG_FILE"; then
  write_launch_status "stopped" "服务已停止。"
else
  write_launch_status "error" "后端启动失败或异常退出。请查看 logs/app_server.log。"
  exit 1
fi
