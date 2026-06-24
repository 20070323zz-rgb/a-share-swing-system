# 动态 App 独立启动修复报告

生成时间：2026-06-17

本报告说明 FastAPI + React/Vite 动态 App 脱离 PyCharm 后的启动修复。修复只涉及本地 App 启动、环境检查、报告和看板同步；不接券商 API，不真实下单，不读取真实账户，不保存密码/token。

## 为什么离开 PyCharm 后可能打不开

PyCharm 通常会自动设置 working directory、虚拟环境解释器和环境变量。普通终端或双击启动时，如果没有显式切换到项目根目录、没有使用项目 `.venv`、前端 dist 缺失或 8000 端口被占用，就可能出现启动失败。

## 修复内容

- `scripts/run_app.sh` 现在通过脚本自身路径自动定位项目根目录，不依赖当前 shell 目录。
- 启动时强制使用项目虚拟环境：`.venv/bin/python`。
- 启动前检查 `.venv`、FastAPI、Uvicorn、前端 dist、npm 和 8000 端口。
- 如果前端 dist 不存在且 npm 可用，会自动执行 `npm install` 和 `npm run build`。
- 如果 8000 端口已有本项目 App，会直接打开浏览器访问。
- 如果 8000 端口被其他进程占用，会清晰提示，不会强杀。
- 启动日志写入 `logs/app_server.log`，终端同时显示关键信息。
- 支持局域网模式：`bash scripts/run_app.sh --lan`。
- 新增双击启动器：`A-Share Swing App.command`。
- 新增环境检查脚本：`scripts/check_app_env.sh`。
- `reports/dashboard_data.json` 新增 `app_launch` 字段。

## 如何终端启动

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/run_app.sh
```

访问地址：

```text
http://127.0.0.1:8000
```

终端窗口必须保持打开；关闭终端后 App 服务停止。

## 如何双击启动

在 Finder 中双击项目根目录下的：

```text
A-Share Swing App.command
```

双击后会打开终端窗口，启动 App，并自动打开浏览器。如果出错，终端会保留错误信息。

## 如何局域网启动

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/run_app.sh --lan
```

同一 Wi-Fi 的手机或其他设备访问：

```text
http://<你的Mac局域网IP>:8000
```

## 安全边界

- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存或打印 `.env` 内容。
- 不保存或打印密码/token。
- 不添加真实交易按钮。
- 不允许前端传入任意 shell 命令。
- 不修改 `data/paper_trades.csv`。
- 不修改 `data/paper_positions.csv`。
