# App Polish Phase 1 启动稳定性与体验打磨报告

生成时间：2026-06-22

## 本轮目标

解决用户实际使用中最容易遇到的三个问题：

1. App 打不开。
2. 不知道为什么打不开。
3. 启动状态、日志和修复动作不够直观。

本轮只做本地 App 启动稳定性、诊断、权限修复、日志状态和轻量 UI polish；没有新增模型，没有新增交易逻辑，没有接券商，没有真实下单。

## 新增脚本

### `scripts/diagnose_app_launch.sh`

一键启动诊断，检查：

- `.app` 包装器是否存在。
- `.app/Contents/MacOS/launch` 是否存在且可执行。
- `Info.plist` 是否存在。
- 图标资源是否存在。
- `scripts/run_app.sh` 是否存在且可执行。
- `.command` fallback 是否可执行。
- `.venv` / Python / FastAPI / Uvicorn 是否可用。
- 前端 dist 是否存在。
- 8000 端口是否空闲、被本项目占用或被其他程序占用。
- 日志是否可写。
- macOS Gatekeeper 是否可能拦截。

输出：

- `reports/app_launch_diagnostics.md`
- `reports/app_launch_diagnostics.json`

### `scripts/fix_app_launch_permissions.sh`

一键修复启动权限，执行：

- 给 `scripts/run_app.sh` 加执行权限。
- 给 `.command` 启动器加执行权限。
- 给 `.app/Contents/MacOS/*` 加执行权限。
- 检查 `logs/app_server.log` 可写。
- 如果 `.app` 缺失，调用 `scripts/create_app_shortcut.sh` 重新生成。

输出：

- `logs/app_launch_status.json`

## 启动脚本增强

已增强 `scripts/run_app.sh`：

- 启动前输出中文状态。
- 检查环境、端口、前端构建、后端启动。
- 如果端口已被本项目 App 占用，直接提示访问 `http://127.0.0.1:8000`。
- 如果端口被其他程序占用，不强杀进程，只给出提示。
- 每次启动/失败/已运行都会写入 `logs/app_launch_status.json`。

## 本轮发现的真实问题

首次诊断时发现：

- `dist/量化研究控制台.app` 缺失。
- `.app/Contents/MacOS/launch` 缺失。
- `Info.plist` 缺失。
- `.icns` 图标缺失。
- 8000 端口已有本项目 App 正在运行。

修复后复诊：

- `.app` 包装器存在。
- 启动文件可执行。
- `Info.plist` 存在。
- 图标资源存在。
- 前端构建产物存在。
- FastAPI / Uvicorn 可导入。
- 后端可导入。
- 日志可写。
- 8000 端口为本项目 App。
- Gatekeeper 未发现明显拦截。

最终诊断状态：`OK`

## App 内同步

已更新：

- `app/backend/readers.py`
- `app/backend/safe_tasks.py`
- `app/frontend/src/pages/SettingsSafety.jsx`
- `app/frontend/src/components/TaskPanel.jsx`
- `app/frontend/src/App.jsx`

新增 App 内展示：

- 启动与诊断页签。
- 最近启动状态。
- 最近启动时间。
- 最近错误摘要。
- 8000 端口状态。
- Gatekeeper 状态。
- 诊断检查表。
- 一键诊断任务。
- 一键修复权限任务。

## UI Polish

轻量优化：

- 新增全局顶部状态栏：`本地研究系统 · v0.1.0-local · 执行禁用 · 未接券商`。
- 点击版本号可进入设置与安全。
- SegmentedControl 选中态更清楚。
- 表格容器横向滚动更稳定。
- 任务按钮和诊断区更像 App 操作，而不是开发后台。
- 日志和报告卡片视觉更克制。
- 移动端顶部状态条自动收敛。

## 常见打不开原因

1. `.app` 包装器缺失或被移动。
2. 启动脚本没有执行权限。
3. macOS 首次打开拦截，需要右键打开。
4. `.venv` 缺失或 Python 依赖缺失。
5. 前端 dist 未构建。
6. 8000 端口被其他程序占用。
7. 日志目录不可写。

## 验证

已通过：

- `python3 -m py_compile dashboard/build_dashboard.py app/backend/readers.py app/backend/main.py app/backend/safe_tasks.py`
- `bash -n scripts/run_app.sh`
- `bash -n scripts/diagnose_app_launch.sh`
- `bash -n scripts/fix_app_launch_permissions.sh`
- `bash scripts/diagnose_app_launch.sh`
- `bash scripts/fix_app_launch_permissions.sh`
- `python3 dashboard/build_dashboard.py`
- `npm run build`
- `bash scripts/check_app_release.sh`

## 关键文件指纹

- `data/paper_trades.csv`：`e3c43a6aee418666fb19460a7bb7ddeb846ced2220b8ab4030bda0d373666425`
- `data/paper_positions.csv`：`1ea405dc2e7bd7eaf1a98bd5b519f45fa1882c8657b66a84e083bee6654ff734`
- `src/paper_trade_engine.py`：`b51f30fc60777d6cb53ccf8bacc460d05082e55fa5b94f2d35a8bc7abddb9d2d`

## 安全边界

- 未接券商 API。
- 未真实下单。
- 未读取真实账户。
- 未读取券商 App。
- 未修改 `src/paper_trade_engine.py`。
- 未修改模型规则。
- 未修改 `data/paper_trades.csv`。
- 未修改 `data/paper_positions.csv`。
- 未显示 token / 密码 / 密钥。
- 未把 shadow 模型接入正式模拟盘。

结论：App Polish Phase 1 已完成，当前本地启动链路可诊断、可修复、可审计，L2 安全边界保持不变。

## 2026-06-23 复验记录

用户再次提交同一阶段要求后，已重新执行启动链路复验：

- `.app` 包装器存在：`dist/量化研究控制台.app`
- `.app/Contents/MacOS/launch` 可执行
- `Info.plist` 存在
- `.icns` 图标存在
- `scripts/run_app.sh` 可执行
- `打开量化研究控制台.command` 可执行
- `A-Share Swing App.command` 可执行
- `.venv` 和 `.venv/bin/python` 存在
- FastAPI / Uvicorn 可导入
- `app.backend.main` 可导入
- 前端构建产物存在
- `logs/app_server.log` 可写
- 8000 端口为本项目 App
- macOS Gatekeeper 未发现明显拦截

复验结果：

- `reports/app_launch_diagnostics.json`：`OK`
- `logs/app_launch_status.json`：`permissions_checked`
- `reports/dashboard_data.json` 已同步启动诊断状态
- `npm run build` 通过
- `bash scripts/check_app_release.sh` 通过

当前建议：

- 可以双击 `dist/量化研究控制台.app`
- 或直接打开 `http://127.0.0.1:8000`

本次复验未修改 `src/paper_trade_engine.py`，未接券商 API，未真实下单。
