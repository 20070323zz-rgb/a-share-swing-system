# Phase 3A FastAPI + React/Vite 动态 App 控制台报告

生成时间：2026-06-16 12:24

## 目标

本轮新增动态 App 控制台，作为现有静态 `dashboard/index.html` 的上层交互入口。静态 dashboard 保留为 fallback。

## 新增能力

- FastAPI 后端 API
- React/Vite 前端
- 本机浏览器访问：`http://127.0.0.1:8000`
- 局域网访问模式：`bash scripts/run_app.sh --lan`
- 白名单快捷任务
- 任务状态：`reports/app_task_status.json`
- 任务日志：`logs/app_tasks/`

## 白名单任务

- `health_check`
- `update_daily_data`
- `backfill_recent_data`
- `run_daily_close_dryrun`
- `run_paper_engine_dryrun`
- `run_strategy_preview`
- `run_strategy_tracking`
- `build_dashboard`
- `refresh_all_reports`

## 禁止能力

- 不接券商 API
- 不真实下单
- 不读取真实账户
- 不保存密码/token
- 不提供真实交易按钮
- 不允许任意命令执行
- 不做公网部署

## 验证记录

- `python3 -m py_compile app/backend/main.py app/backend/task_runner.py app/backend/safe_tasks.py app/backend/readers.py app/backend/schemas.py dashboard/build_dashboard.py`：通过
- `bash -n scripts/run_app.sh`：通过
- `python3 dashboard/build_dashboard.py`：通过，`reports/dashboard_data.json` 已更新到 `phase3a_fastapi_react_app_v1`
- FastAPI 后端启动：通过，地址 `http://127.0.0.1:8000`
- API 验证：
  - `/api/status`：通过
  - `/api/dashboard-data`：通过
  - `/api/data-health`：通过
  - `/api/portfolio`：通过
  - `/api/signals`：通过
  - `/api/research`：通过
  - `/api/tasks/status`：通过
  - `/api/logs?name=app_tasks.log`：通过
- 白名单任务验证：
  - `build_dashboard`：success
  - `run_daily_close_dryrun`：success
- `run_daily_close_dryrun` 后文件哈希：
  - `data/paper_trades.csv`：`938db28ea3bf98b79297759838a5777907e9402dd2a3472970d43ce1b3bf8d5b`
  - `data/paper_positions.csv`：`f6d0b95fcb6531c84db805d66643dd99a13987a72dcf0180ce272c50dfd83901`
- 浏览器加载验证：通过，页面标题、状态卡、快捷按钮、持仓、信号模块均正常显示。

## 依赖说明

当前执行环境没有系统 `npm`，因此未能执行 `npm install && npm run build`。本轮已提供完整 React/Vite 源码，并补充 `app/frontend/dist/` 本地 fallback 产物；在用户本机安装 Node.js/npm 后，`bash scripts/run_app.sh` 会自动安装前端依赖并执行标准 Vite 构建。

## 安全结论

本轮没有新增真实交易能力，没有券商 API，没有真实账户读取，没有任意命令执行。快捷按钮只能触发后端白名单任务。
