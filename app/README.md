# A 股 ETF 动态研究控制台

这是 A 股 ETF 双周期模拟盘系统的动态 App 层，技术路线为 **FastAPI + React/Vite**。

它只服务于本地模拟盘研究和报告查看：

- 不接券商 API
- 不真实下单
- 不读取真实账户
- 不保存密码或 token
- 不提供真实买入/卖出按钮
- 不允许前端传入任意 shell 命令

## 脱离 PyCharm 启动

动态 App 不需要打开 PyCharm。启动脚本会自动定位项目根目录、使用项目 `.venv`、检查前端构建产物，并打开浏览器。

### 方式一：终端启动

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/run_app.sh
```

浏览器地址：

```text
http://127.0.0.1:8000
```

终端窗口需要保持打开；关闭终端后 App 服务会停止。

### 方式二：双击中文启动器

在 Finder 中双击项目根目录下的：

```text
打开量化研究控制台.command
```

双击后会打开终端窗口，启动 FastAPI + React/Vite App，并自动打开浏览器。如果启动失败，终端会保留错误信息。

旧启动器 `A-Share Swing App.command` 仍然保留，也可以继续使用。

如果 macOS 提示无法打开，请右键点击启动器，选择“打开”。

### 方式三：局域网启动

只建议在可信 Wi-Fi 下使用：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/run_app.sh --lan
```

手机或同一 Wi-Fi 设备访问：

```text
http://<你的Mac局域网IP>:8000
```

查看 Mac 局域网 IP：

```bash
ipconfig getifaddr en0
```

本项目不做公网部署，不提供真实交易按钮，不接券商 API，不真实下单。

## 环境检查

如果 App 无法独立启动，先运行：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/check_app_env.sh
```

检查脚本会验证 `.venv`、FastAPI、Uvicorn、npm、前端 dist、`.env`、`dashboard_data.json`、8000 端口和后端 import 状态。它不会打印 `.env` 内容。

更多图标启动说明见：

```text
docs/app_launch_guide.md
打开App说明.md
```

## 原启动方式

在项目根目录运行：

```bash
bash scripts/run_app.sh
```

本机访问：

```text
http://127.0.0.1:8000
```

如果本机暂时没有 `npm`，脚本会使用已存在的 `app/frontend/dist/` 静态产物启动。安装 Node.js/npm 后，脚本会自动执行标准 React/Vite 构建。

## 局域网访问补充

只建议在可信 Wi-Fi 下使用：

```bash
bash scripts/run_app.sh --lan
```

查看 Mac 局域网 IP：

```bash
ipconfig getifaddr en0
```

然后在同一 Wi-Fi 的设备浏览器打开：

```text
http://<你的Mac局域网IP>:8000
```

本项目不做公网部署，不做登录系统，不开放任意命令执行。

## 快捷按钮

动态 App 首页提供这些白名单任务：

- 一键补齐数据：`backfill_recent_data`
- 一键刷新报告：`refresh_all_reports`
- 一键 dry-run：`run_daily_close_dryrun`
- 一键策略预览：`run_strategy_preview`
- 一键影子跟踪：`run_strategy_tracking`
- 一键生成静态看板：`build_dashboard`

所有按钮都不会真实下单。`run_daily_close_dryrun` 不修改 `data/paper_trades.csv` 和 `data/paper_positions.csv`。

## 日志和任务状态

- 任务状态：`reports/app_task_status.json`
- 任务日志：`logs/app_tasks/`
- 静态 fallback：`dashboard/index.html`
- 看板数据：`reports/dashboard_data.json`

## 开发模式

后端：

```bash
.venv/bin/python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8000
```

前端：

```bash
cd app/frontend
npm install
npm run dev
```

开发模式下 Vite 会把 `/api` 代理到 `127.0.0.1:8000`。
