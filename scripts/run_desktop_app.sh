#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/Users/dayin/Code/a-share-swing-system"
TAURI_DIR="$PROJECT_ROOT/desktop/tauri"
FRONTEND_DIR="$PROJECT_ROOT/app/frontend"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"

cd "$PROJECT_ROOT"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "未找到项目 Python：$PYTHON_BIN"
  echo "请先修复项目 .venv。"
  exit 1
fi

if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import fastapi, uvicorn
PY
then
  echo "缺少 FastAPI/Uvicorn，请先运行："
  echo "$PYTHON_BIN -m pip install fastapi uvicorn"
  exit 1
fi

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "未找到 Node.js/npm。"
  echo "请先安装 Node.js，然后仍可使用浏览器版：bash scripts/run_app.sh"
  exit 1
fi

if ! command -v cargo >/dev/null 2>&1 || ! command -v rustc >/dev/null 2>&1; then
  echo "未找到 Rust/cargo，暂时无法启动 Tauri 桌面 App。"
  echo "安装 Rust："
  echo "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
  echo
  echo "浏览器版仍可使用："
  echo "bash scripts/run_app.sh"
  exit 1
fi

cd "$FRONTEND_DIR"
if [ ! -d node_modules ]; then
  echo "安装 Web App 前端依赖..."
  npm install
fi
echo "构建 Web App 前端 fallback..."
npm run build

cd "$TAURI_DIR"
if [ ! -d node_modules ]; then
  echo "安装 Tauri 桌面 App 依赖..."
  npm install
fi

echo "启动 Tauri 桌面 App..."
npm run tauri dev
