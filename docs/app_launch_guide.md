# App 启动指南

本项目的动态 App 是本地量化研究控制台，用于查看模拟盘、研究报告、影子模型观察和安全白名单任务。

安全边界始终不变：

- 不接券商 API
- 不真实下单
- 不读取真实账户
- 不显示或保存 token / 密码
- 不提供真实交易按钮

## 推荐方式：双击本地 App 包装器

先在项目根目录生成本地 App：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/create_app_shortcut.sh
```

生成后双击：

```text
dist/量化研究控制台.app
```

它会调用项目内的 `scripts/run_app.sh`，自动启动本地服务并打开浏览器。这个 `.app` 只是本地启动包装器，不包含账号、密码、token，也不接券商。

## 方式二：双击中文启动器

在 Finder 中打开项目目录：

```text
/Users/dayin/Code/a-share-swing-system
```

双击：

```text
打开量化研究控制台.command
```

启动器会自动：

1. 进入项目根目录；
2. 使用项目 `.venv`；
3. 检查 FastAPI / Uvicorn；
4. 检查前端页面是否已构建；
5. 必要时构建前端；
6. 启动本地 App；
7. 自动打开浏览器访问 `http://127.0.0.1:8000`；
8. 将日志写入 `logs/app_server.log`。

## macOS 提示无法打开怎么办

如果 macOS 提示“无法打开”或“来自身份不明开发者”：

1. 在 Finder 中右键点击 `打开量化研究控制台.command`；
2. 选择“打开”；
3. 在弹窗中再次选择“打开”。

这是 macOS 对脚本文件的安全提示，不代表 App 会接触真实交易。

## 打不开怎么办

按这个顺序排查：

1. 先在 Finder 中右键点击 `dist/量化研究控制台.app`，选择“打开”。
2. 如果仍打不开，运行启动诊断：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/diagnose_app_launch.sh
```

3. 如果诊断提示权限或 `.app` 缺失，运行：

```bash
bash scripts/fix_app_launch_permissions.sh
```

4. 如果提示 8000 端口被占用，先确认是否已经有本项目 App 在运行。若已运行，直接打开：

```text
http://127.0.0.1:8000
```

5. 如果还是失败，查看：

```text
logs/app_server.log
logs/app_launch_status.json
reports/app_launch_diagnostics.md
```

诊断和修复脚本都只处理本地启动环境，不接券商，不真实交易，不读取 token。

## 放到桌面

推荐把 `dist/量化研究控制台.app` 拖到桌面。以后双击桌面上的 App 图标即可启动。

如果还没有生成 `.app`，也可以把 `打开量化研究控制台.command` 拖到桌面。

如果你想保留项目目录里的原文件，可以按住 `Option + Command` 拖动，创建替身。

## 固定到 Dock

生成 `dist/量化研究控制台.app` 后，可以把它拖到 Dock。它本质上仍然是本地启动器，关闭终端后后端服务会停止。

`.command` 文件不能像普通 `.app` 那样完美固定到 Dock，只建议作为 fallback。

## 更换图标

本项目自带本地自绘图标：

```text
assets/app_icon.svg
assets/app_icon.png
```

如果 macOS 没有显示自定义图标，可以先继续使用 `.app` 或 `.command` 启动，不影响功能。后续可以手动替换图标，但不要使用券商 logo、Apple 官方素材或受版权保护图标。

## 如何关闭 App

启动后会出现一个终端窗口。保持窗口打开，App 就会继续运行。

关闭方式：

1. 在终端窗口按 `Control + C`；
2. 或直接关闭该终端窗口。

关闭后，浏览器页面会失去后端连接。

## 查看日志

启动日志：

```text
logs/app_server.log
```

任务日志：

```text
logs/app_tasks/
```

App 页面里的“任务与日志”也可以查看部分只读日志。

## 如果打不开，先检查这些

先运行环境检查：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/check_app_env.sh
```

常见原因：

- `.venv` 不存在或损坏；
- `fastapi` / `uvicorn` 未安装；
- `npm` 不存在且前端页面还没有构建；
- 8000 端口被其他程序占用；
- 项目目录被移动。

## 局域网访问

只建议在可信 Wi-Fi 下使用：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/run_app.sh --lan
```

同一 Wi-Fi 下的手机或平板访问：

```text
http://<你的Mac局域网IP>:8000
```

本项目不做公网部署。
