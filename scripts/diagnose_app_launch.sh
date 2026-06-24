#!/bin/bash
set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1
REPORT_DIR="$PROJECT_ROOT/reports"
LOG_DIR="$PROJECT_ROOT/logs"
APP_BUNDLE="$PROJECT_ROOT/dist/量化研究控制台.app"
APP_EXEC="$APP_BUNDLE/Contents/MacOS/launch"
INFO_PLIST="$APP_BUNDLE/Contents/Info.plist"
ICON_ICNS="$APP_BUNDLE/Contents/Resources/app_icon.icns"
RUN_APP="$PROJECT_ROOT/scripts/run_app.sh"
COMMAND_CN="$PROJECT_ROOT/打开量化研究控制台.command"
COMMAND_LEGACY="$PROJECT_ROOT/A-Share Swing App.command"
VENV_PY="$PROJECT_ROOT/.venv/bin/python"
PY_BIN="$VENV_PY"
if [ ! -x "$PY_BIN" ]; then
  PY_BIN="$(command -v python3 || true)"
fi
DIST_INDEX="$PROJECT_ROOT/app/frontend/dist/index.html"
LOG_FILE="$LOG_DIR/app_server.log"
STATUS_JSON="$REPORT_DIR/app_launch_diagnostics.json"
STATUS_MD="$REPORT_DIR/app_launch_diagnostics.md"
PORT=8000

mkdir -p "$REPORT_DIR" "$LOG_DIR"

ITEMS_FILE="$(mktemp)"
SUMMARY_FILE="$(mktemp)"

add_item() {
  local status="$1"
  local key="$2"
  local label="$3"
  local detail="$4"
  printf '%s\t%s\t%s\t%s\n' "$status" "$key" "$label" "$detail" >> "$ITEMS_FILE"
  case "$status" in
    OK) echo "✅ ${label}：${detail}" ;;
    CAUTION) echo "⚠️ ${label}：${detail}" ;;
    ERROR) echo "❌ ${label}：${detail}" ;;
  esac
}

check_file() {
  local key="$1"
  local label="$2"
  local path="$3"
  if [ -e "$path" ]; then
    add_item OK "$key" "$label" "$path"
  else
    add_item ERROR "$key" "$label" "缺失：$path"
  fi
}

check_exec() {
  local key="$1"
  local label="$2"
  local path="$3"
  if [ -x "$path" ]; then
    add_item OK "$key" "$label" "可执行：$path"
  elif [ -e "$path" ]; then
    add_item CAUTION "$key" "$label" "存在但不可执行：$path"
  else
    add_item ERROR "$key" "$label" "缺失：$path"
  fi
}

echo "量化研究控制台启动诊断"
echo "项目路径：$PROJECT_ROOT"
echo

check_file "app_bundle" ".app 包装器" "$APP_BUNDLE"
check_exec "app_executable" ".app 启动文件" "$APP_EXEC"
check_file "info_plist" "Info.plist" "$INFO_PLIST"
check_file "icon_icns" "App 图标资源" "$ICON_ICNS"
check_exec "run_app" "run_app.sh" "$RUN_APP"
check_exec "command_launcher" "中文 .command 启动器" "$COMMAND_CN"
check_exec "legacy_launcher" "英文 .command 启动器" "$COMMAND_LEGACY"
check_file "venv_dir" ".venv 虚拟环境" "$PROJECT_ROOT/.venv"
check_exec "venv_python" ".venv Python" "$VENV_PY"
check_file "frontend_dist" "前端构建产物" "$DIST_INDEX"

if [ -x "$VENV_PY" ]; then
  if "$VENV_PY" - <<'PY' >/dev/null 2>&1
import fastapi
import uvicorn
PY
  then
    add_item OK "python_deps" "FastAPI / Uvicorn" "依赖可导入"
  else
    add_item ERROR "python_deps" "FastAPI / Uvicorn" "依赖缺失，建议执行 .venv/bin/pip install fastapi uvicorn"
  fi

  if "$VENV_PY" - <<'PY' >/dev/null 2>&1
import importlib
importlib.import_module("app.backend.main")
PY
  then
    add_item OK "backend_import" "App 后端导入" "app.backend.main 可导入"
  else
    add_item ERROR "backend_import" "App 后端导入" "导入失败，请查看 Python 报错或运行 py_compile"
  fi
else
  add_item ERROR "python_deps" "FastAPI / Uvicorn" "无法检查，.venv Python 不可执行"
  add_item ERROR "backend_import" "App 后端导入" "无法检查，.venv Python 不可执行"
fi

if [ -d "$LOG_DIR" ] && [ -w "$LOG_DIR" ]; then
  touch "$LOG_FILE" 2>/dev/null
  if [ -w "$LOG_FILE" ]; then
    add_item OK "log_writable" "日志文件" "可写：$LOG_FILE"
  else
    add_item ERROR "log_writable" "日志文件" "不可写：$LOG_FILE"
  fi
else
  add_item ERROR "log_writable" "日志目录" "不可写：$LOG_DIR"
fi

PORT_STATUS="free"
PORT_DETAIL="8000 端口空闲"
if command -v lsof >/dev/null 2>&1; then
  PIDS="$(lsof -nP -iTCP:$PORT -sTCP:LISTEN -t 2>/dev/null | sort -u || true)"
  if [ -n "$PIDS" ]; then
    if [ -x "$VENV_PY" ] && "$VENV_PY" - <<PY >/dev/null 2>&1
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
      PORT_STATUS="project_app"
      PORT_DETAIL="本项目 App 已在运行：http://127.0.0.1:$PORT"
      add_item OK "port_8000" "8000 端口" "$PORT_DETAIL"
    else
      PORT_STATUS="occupied_other"
      PORT_DETAIL="被其他程序占用：$PIDS"
      add_item ERROR "port_8000" "8000 端口" "$PORT_DETAIL"
    fi
  else
    add_item OK "port_8000" "8000 端口" "$PORT_DETAIL"
  fi
else
  PORT_STATUS="unknown"
  PORT_DETAIL="系统无 lsof，无法检查端口"
  add_item CAUTION "port_8000" "8000 端口" "$PORT_DETAIL"
fi

GATEKEEPER_STATUS="not_checked"
GATEKEEPER_DETAIL="未发现明显拦截信息"
if command -v xattr >/dev/null 2>&1 && [ -e "$APP_BUNDLE" ]; then
  if xattr "$APP_BUNDLE" 2>/dev/null | grep -q "com.apple.quarantine"; then
    GATEKEEPER_STATUS="quarantined"
    GATEKEEPER_DETAIL="macOS 可能拦截。建议右键 App 选择“打开”。"
    add_item CAUTION "gatekeeper" "macOS Gatekeeper" "$GATEKEEPER_DETAIL"
  else
    GATEKEEPER_STATUS="clear"
    add_item OK "gatekeeper" "macOS Gatekeeper" "$GATEKEEPER_DETAIL"
  fi
else
  add_item CAUTION "gatekeeper" "macOS Gatekeeper" "无法检查；如打不开请右键选择“打开”"
fi

ERROR_COUNT="$(awk -F '\t' '$1=="ERROR"{c++} END{print c+0}' "$ITEMS_FILE")"
CAUTION_COUNT="$(awk -F '\t' '$1=="CAUTION"{c++} END{print c+0}' "$ITEMS_FILE")"
if [ "$ERROR_COUNT" -gt 0 ]; then
  OVERALL="ERROR"
elif [ "$CAUTION_COUNT" -gt 0 ]; then
  OVERALL="CAUTION"
else
  OVERALL="OK"
fi

RECOMMENDATION="可以双击 dist/量化研究控制台.app 或打开 http://127.0.0.1:8000。"
if grep -q $'\tapp_bundle\t' "$ITEMS_FILE" && awk -F '\t' '$2=="app_bundle" && $1=="ERROR"{found=1} END{exit found?0:1}' "$ITEMS_FILE"; then
  RECOMMENDATION="缺少 .app 包装器。建议运行：bash scripts/fix_app_launch_permissions.sh"
elif [ "$PORT_STATUS" = "occupied_other" ]; then
  RECOMMENDATION="8000 端口被其他程序占用。请关闭占用程序，或确认是否已有旧服务未退出。"
elif [ "$GATEKEEPER_STATUS" = "quarantined" ]; then
  RECOMMENDATION="macOS 可能拦截首次打开。请在 Finder 中右键 dist/量化研究控制台.app，选择“打开”。"
elif [ "$CAUTION_COUNT" -gt 0 ]; then
  RECOMMENDATION="存在轻微注意项。可先运行：bash scripts/fix_app_launch_permissions.sh"
fi

if [ -z "$PY_BIN" ]; then
  echo "❌ 无法生成 JSON：未找到 Python。"
else
  "$PY_BIN" - "$ITEMS_FILE" "$STATUS_JSON" "$OVERALL" "$PORT_STATUS" "$GATEKEEPER_STATUS" "$RECOMMENDATION" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

items_file, out_file, overall, port_status, gatekeeper_status, recommendation = sys.argv[1:7]
items = []
for line in Path(items_file).read_text(encoding="utf-8").splitlines():
    status, key, label, detail = line.split("\t", 3)
    items.append({"status": status, "key": key, "label": label, "detail": detail})
payload = {
    "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "overall_status": overall,
    "port_status": port_status,
    "gatekeeper_status": gatekeeper_status,
    "recommendation": recommendation,
    "items": items,
    "safety": {
        "broker_api": False,
        "real_trade": False,
        "real_account": False,
        "token_printed": False,
    },
}
Path(out_file).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
fi

{
  echo "# App 启动诊断报告"
  echo
  echo "- 检查时间：$(date '+%Y-%m-%d %H:%M:%S')"
  echo "- 总体状态：$OVERALL"
  echo "- 端口状态：$PORT_STATUS"
  echo "- Gatekeeper：$GATEKEEPER_STATUS"
  echo "- 推荐动作：$RECOMMENDATION"
  echo
  echo "## 检查结果"
  echo
  echo "| 状态 | 项目 | 详情 |"
  echo "| --- | --- | --- |"
  awk -F '\t' '{print "| " $1 " | " $3 " | " $4 " |"}' "$ITEMS_FILE"
  echo
  echo "## 常见原因"
  echo
  echo "1. .app 包装器缺失或被移动。"
  echo "2. 启动文件没有执行权限。"
  echo "3. macOS 首次打开拦截，需要右键打开。"
  echo "4. .venv 或 FastAPI/Uvicorn 依赖缺失。"
  echo "5. 8000 端口被其他程序占用。"
  echo "6. 前端 dist 尚未构建。"
  echo
  echo "## 安全边界"
  echo
  echo "- 未接券商 API。"
  echo "- 未真实下单。"
  echo "- 未读取真实账户。"
  echo "- 未输出 token / 密码 / 密钥。"
} > "$STATUS_MD"

rm -f "$ITEMS_FILE" "$SUMMARY_FILE"

echo
echo "诊断完成：$OVERALL"
echo "建议：$RECOMMENDATION"
echo "报告：$STATUS_MD"
echo "JSON：$STATUS_JSON"

[ "$OVERALL" = "ERROR" ] && exit 1
exit 0
