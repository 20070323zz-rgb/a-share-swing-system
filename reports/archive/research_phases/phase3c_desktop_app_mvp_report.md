# Phase 3C 桌面 App MVP 报告

生成时间：2026-06-16

## 本轮目标

将当前 FastAPI + React/Vite 动态控制台增加 Mac 桌面 App 外壳。桌面 App 不重写后端、不重写前端，只负责打开当前本地控制台。

## 新增文件

- `desktop/tauri/package.json`
- `desktop/tauri/index.html`
- `desktop/tauri/src/main.js`
- `desktop/tauri/src-tauri/Cargo.toml`
- `desktop/tauri/src-tauri/tauri.conf.json`
- `desktop/tauri/src-tauri/src/main.rs`
- `desktop/README.md`
- `scripts/run_desktop_app.sh`

## 技术路线

- 桌面壳：Tauri
- 后端：现有 FastAPI
- 前端：现有 React/Vite
- 默认加载：`http://127.0.0.1:8000`

## 后端启动策略

已实现方案 A：

1. Tauri 启动时检查 `127.0.0.1:8000`；
2. 如果后端已运行，不重复启动；
3. 如果后端未运行，自动执行：
   `.venv/bin/python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8000`
4. stdout/stderr 写入 `logs/desktop_app/`；
5. App 关闭时尝试停止由 App 启动的后端进程。

## 安全边界

- 不接券商 API
- 不真实下单
- 不读取真实账户
- 不保存密码/token
- 不新增真实交易按钮
- 不允许任意 shell 命令执行
- 快捷按钮继续走 FastAPI 白名单任务
- 不修改 `paper_trades.csv`
- 不修改 `paper_positions.csv`

## 验证记录

- `python3 -m py_compile app/backend/main.py dashboard/build_dashboard.py`：通过
- `bash -n scripts/run_desktop_app.sh`：通过
- `cd desktop/tauri && npm install`：通过，Tauri CLI 依赖安装完成
- `python3 dashboard/build_dashboard.py`：通过
- `reports/dashboard_data.json`：已更新为 `phase3c_desktop_app_mvp_v1`
- `dynamic_app` / `strategy_preview_tracking` / `app_task_status` 字段：已保留
- `bash scripts/run_desktop_app.sh`：当前机器未安装 Rust/cargo，脚本已清楚提示安装 Rust，并提示继续使用浏览器版

当前环境未安装 Rust/cargo，因此本轮未实际打开 Tauri 桌面窗口。安装 Rust 后可继续运行：

```bash
cd <project_root>
bash scripts/run_desktop_app.sh
```

如果 Rust/Tauri 未安装，浏览器版继续可用：

```bash
bash scripts/run_app.sh
```
