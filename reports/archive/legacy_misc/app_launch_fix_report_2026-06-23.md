# 量化研究控制台 App 启动修复报告

生成时间：2026-06-23 23:44

## 结论

`量化研究控制台.app` 双击无法打开的根因不是 `.venv` 缺失，也不是 FastAPI / Uvicorn 未安装，而是 macOS `open .app` 通过 LaunchServices 启动时，进程以 `x86_64` 架构运行；项目 `.venv` 中的 `pydantic_core` 是 `arm64` 原生 wheel，导致 FastAPI 导入链路报错：

```text
mach-o file, but is an incompatible architecture (have 'arm64', need 'x86_64')
```

修复后，项目内 `.app` 和桌面 `.app` 均已验证可以打开。

## 复现过程

已执行：

```bash
bash scripts/diagnose_app_launch.sh
"dist/量化研究控制台.app/Contents/MacOS/launch"
open "dist/量化研究控制台.app"
cat logs/app_launch_status.json
tail -n 120 logs/app_server.log
lsof -i :8000
```

发现：

- 直接运行 `Contents/MacOS/launch` 可以启动。
- `open "dist/量化研究控制台.app"` 失败。
- 失败点在 `scripts/run_app.sh` 的 FastAPI / Uvicorn 依赖检查。
- 详细日志显示 `pydantic_core` 架构不兼容：`have arm64, need x86_64`。

## 修复内容

### `scripts/run_app.sh`

新增：

- 清理 `__PYVENV_LAUNCHER__`。
- 清理 `PYTHONHOME`。
- 如果检测到当前进程为 `x86_64` 且系统支持 `arm64`，自动用 `arch -arm64 /bin/bash` 重新启动自身。
- 依赖检查失败时写入 `logs/app_dependency_check.log`，便于排查真实原因。

### `scripts/create_app_shortcut.sh`

新增：

- `Info.plist` 写入 `LSArchitecturePriority = arm64, x86_64`。
- `.app/Contents/MacOS/launch` 显式使用 `arch -arm64 /bin/bash scripts/run_app.sh`。
- 保留 fallback：如果系统不支持 arm64，则使用普通 `/bin/bash`。

### `.app` 重新生成

已运行：

```bash
bash scripts/create_app_shortcut.sh
```

生成：

- `dist/量化研究控制台.app`
- `dist/量化研究控制台.app/Contents/MacOS/launch`
- `dist/量化研究控制台.app/Contents/Info.plist`
- `dist/量化研究控制台.app/Contents/Resources/app_icon.icns`

### 桌面副本同步

已同步：

```bash
~/Desktop/量化研究控制台.app
```

并移除 quarantine 标记、补可执行权限。

## 验证结果

### 项目内 App

已运行：

```bash
open "dist/量化研究控制台.app"
```

结果：

- `logs/app_launch_status.json` 显示 `running`
- 8000 端口有 Python 进程监听
- 浏览器自动访问 `http://127.0.0.1:8000`
- `/api/status` 可返回 JSON

### 桌面 App

已运行：

```bash
open ~/Desktop/量化研究控制台.app
```

结果：

- 已识别本项目 App 正在运行
- 不重复启动服务
- 自动打开浏览器
- `logs/app_launch_status.json` 显示 `already_running`

### fallback `.command`

仍保留：

- `打开量化研究控制台.command`
- `A-Share Swing App.command`

两者仍可执行。

## 当前启动状态

- 服务地址：`http://127.0.0.1:8000`
- 8000 端口：正常监听
- 启动状态：`already_running`
- 项目内 `.app`：可打开
- 桌面 `.app`：可打开
- 浏览器：可自动打开

## 验证命令

已通过：

```bash
bash scripts/diagnose_app_launch.sh
python3 -m py_compile dashboard/build_dashboard.py app/backend/readers.py app/backend/main.py app/backend/safe_tasks.py
bash -n scripts/run_app.sh
bash -n scripts/create_app_shortcut.sh
bash -n scripts/diagnose_app_launch.sh
bash -n scripts/fix_app_launch_permissions.sh
npm run build
python3 dashboard/build_dashboard.py
```

## 安全边界

本轮未修改：

- `data/paper_trades.csv`
- `data/paper_positions.csv`
- `src/paper_trade_engine.py`

本轮未执行：

- 未接券商 API
- 未真实下单
- 未读取真实账户
- 未读取券商 App
- 未读取或暴露 `.env` / token / 密码
- 未修改模型规则
- 未把 shadow 模型接入执行层

## 当前关键文件指纹

- `data/paper_trades.csv`：`3f0e777e5f7e441d2ab9349cf5ed8f58194f07b96dabc866fa5ed8187e072e31`
- `data/paper_positions.csv`：`998ad526c0218669b7e2b2eb64f7ad3952cd89be904f4b535fb3e2792217118f`
- `src/paper_trade_engine.py`：`b51f30fc60777d6cb53ccf8bacc460d05082e55fa5b94f2d35a8bc7abddb9d2d`

## 后续使用

推荐直接双击：

```text
~/Desktop/量化研究控制台.app
```

或项目内：

```text
/Users/dayin/Code/a-share-swing-system/dist/量化研究控制台.app
```

如果仍打不开，运行：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/diagnose_app_launch.sh
```
