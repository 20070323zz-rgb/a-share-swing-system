#!/bin/bash
PROJECT_ROOT="/Users/dayin/Code/a-share-swing-system"
cd "$PROJECT_ROOT" || {
  echo "无法进入项目目录：$PROJECT_ROOT"
  echo "请确认项目仍在该路径，或从项目根目录重新生成启动器。"
  read -r -p "按回车关闭窗口..."
  exit 1
}

echo "正在启动 A 股 ETF 量化研究控制台..."
echo "版本：v$(cat APP_VERSION 2>/dev/null || echo 0.1.0-local)"
echo "项目目录：$PROJECT_ROOT"
echo "安全边界：研究和模拟盘展示；不接券商 API；不真实下单。"
echo

bash scripts/run_app.sh
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
  echo
  echo "App 启动失败，退出码：$STATUS"
  echo "你可以先运行环境检查：bash scripts/check_app_env.sh"
  echo "详细日志：logs/app_server.log"
  read -r -p "按回车关闭窗口..."
fi
exit "$STATUS"
