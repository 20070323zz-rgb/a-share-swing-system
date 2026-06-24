# Phase 3C Mac 桌面 App MVP

本目录新增 Tauri 桌面外壳，用于打开现有 FastAPI + React/Vite 动态控制台。

它不是新的交易系统，也不重写原有 Web App：

- 后端仍是 `app/backend/` FastAPI；
- 前端仍是 `app/frontend/` React/Vite；
- 浏览器版仍可通过 `bash scripts/run_app.sh` 启动；
- 静态 dashboard 仍保留为 fallback；
- 桌面 App 只是本地窗口外壳。

## 安全边界

- 不接券商 API
- 不真实下单
- 不读取真实账户
- 不保存密码/token
- 不添加真实买入/卖出按钮
- 不允许任意 shell 命令执行
- 快捷按钮仍然只能调用 FastAPI `/api/tasks/run` 的白名单 `task_name`

Tauri command 只允许：

- `check_backend_status`
- `start_backend`
- `stop_backend`
- `open_project_folder`
- `open_logs_folder`

禁止：

- `run_arbitrary_command`
- `broker_login`
- `real_trade`
- `read_real_account`

## 安装 Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

安装后重新打开终端，确认：

```bash
rustc --version
cargo --version
```

## 安装 Tauri CLI

```bash
cd /Users/dayin/Code/a-share-swing-system/desktop/tauri
npm install
npm install -D @tauri-apps/cli
```

## 启动桌面 App

推荐：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/run_desktop_app.sh
```

也可以：

```bash
cd /Users/dayin/Code/a-share-swing-system/desktop/tauri
npm run tauri dev
```

## 后端启动策略

桌面 App 会检查：

```text
http://127.0.0.1:8000
```

如果后端未运行，Tauri 会尝试自动启动：

```bash
cd /Users/dayin/Code/a-share-swing-system
.venv/bin/python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8000
```

后端日志写入：

```text
logs/desktop_app/backend.out.log
logs/desktop_app/backend.err.log
logs/desktop_app/desktop_warning.log
```

如果 8000 已经运行，桌面 App 不会重复启动后端。

## 浏览器版仍可用

如果 Rust/Tauri 暂时未安装，继续使用：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/run_app.sh
```

浏览器访问：

```text
http://127.0.0.1:8000
```

## 不建议公网暴露

本项目是本地模拟盘学习系统。桌面 App 和 Web App 都只建议用于本机或可信局域网，不建议公网部署。
