#!/bin/bash
set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1
APP_BUNDLE="$PROJECT_ROOT/dist/量化研究控制台.app"
APP_EXEC_DIR="$APP_BUNDLE/Contents/MacOS"
RUN_APP="$PROJECT_ROOT/scripts/run_app.sh"
CREATE_APP="$PROJECT_ROOT/scripts/create_app_shortcut.sh"
COMMAND_CN="$PROJECT_ROOT/打开量化研究控制台.command"
COMMAND_LEGACY="$PROJECT_ROOT/A-Share Swing App.command"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/app_server.log"
STATUS_JSON="$LOG_DIR/app_launch_status.json"

echo "量化研究控制台启动权限修复"
echo "项目路径：$PROJECT_ROOT"
echo

mkdir -p "$LOG_DIR"
touch "$LOG_FILE" 2>/dev/null || true

fix_exec() {
  local path="$1"
  local label="$2"
  if [ -e "$path" ]; then
    chmod +x "$path" 2>/dev/null && echo "✅ $label 已设为可执行：$path" || echo "⚠️ $label 权限设置失败：$path"
  else
    echo "⚠️ $label 不存在：$path"
  fi
}

fix_exec "$RUN_APP" "run_app.sh"
fix_exec "$CREATE_APP" "create_app_shortcut.sh"
fix_exec "$COMMAND_CN" "中文启动器"
fix_exec "$COMMAND_LEGACY" "英文启动器"

if [ ! -d "$APP_BUNDLE" ]; then
  echo "⚠️ 未找到 .app 包装器，尝试重新生成。"
  if [ -x "$CREATE_APP" ]; then
    bash "$CREATE_APP"
  else
    echo "❌ 无法重新生成：缺少 scripts/create_app_shortcut.sh"
  fi
fi

if [ -d "$APP_EXEC_DIR" ]; then
  find "$APP_EXEC_DIR" -maxdepth 1 -type f -exec chmod +x {} \; 2>/dev/null
  echo "✅ .app 启动文件权限已检查：$APP_EXEC_DIR"
else
  echo "⚠️ .app 启动目录不存在：$APP_EXEC_DIR"
fi

if [ -w "$LOG_DIR" ] && touch "$LOG_FILE" 2>/dev/null; then
  echo "✅ 日志目录和 app_server.log 可写"
else
  echo "❌ 日志目录或 app_server.log 不可写：$LOG_FILE"
fi

if command -v xattr >/dev/null 2>&1 && [ -d "$APP_BUNDLE" ]; then
  if xattr "$APP_BUNDLE" 2>/dev/null | grep -q "com.apple.quarantine"; then
    echo "⚠️ 检测到 macOS quarantine 标记。已保留系统安全策略；建议右键 App 选择“打开”。"
  else
    echo "✅ 未发现明显 Gatekeeper quarantine 标记"
  fi
fi

cat > "$STATUS_JSON" <<JSON
{
  "started_at": "$(date '+%Y-%m-%d %H:%M:%S')",
  "project_dir": "$PROJECT_ROOT",
  "app_version": "$(cat "$PROJECT_ROOT/APP_VERSION" 2>/dev/null || echo "0.1.0-local")",
  "port": 8000,
  "status": "permissions_checked",
  "error_summary": "",
  "log_path": "logs/app_server.log",
  "safe_note": "只修复本地启动权限；不接券商；不真实交易；不读取 token。"
}
JSON

echo
echo "修复完成。建议继续运行：bash scripts/diagnose_app_launch.sh"
