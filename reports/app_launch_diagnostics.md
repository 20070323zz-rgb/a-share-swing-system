# App 启动诊断报告

- 检查时间：2026-06-23 23:44:13
- 总体状态：OK
- 端口状态：project_app
- Gatekeeper：clear
- 推荐动作：可以双击 dist/量化研究控制台.app 或打开 http://127.0.0.1:8000。

## 检查结果

| 状态 | 项目 | 详情 |
| --- | --- | --- |
| OK | .app 包装器 | /Users/dayin/Code/a-share-swing-system/dist/量化研究控制台.app |
| OK | .app 启动文件 | 可执行：/Users/dayin/Code/a-share-swing-system/dist/量化研究控制台.app/Contents/MacOS/launch |
| OK | Info.plist | /Users/dayin/Code/a-share-swing-system/dist/量化研究控制台.app/Contents/Info.plist |
| OK | App 图标资源 | /Users/dayin/Code/a-share-swing-system/dist/量化研究控制台.app/Contents/Resources/app_icon.icns |
| OK | run_app.sh | 可执行：/Users/dayin/Code/a-share-swing-system/scripts/run_app.sh |
| OK | 中文 .command 启动器 | 可执行：/Users/dayin/Code/a-share-swing-system/打开量化研究控制台.command |
| OK | 英文 .command 启动器 | 可执行：/Users/dayin/Code/a-share-swing-system/A-Share Swing App.command |
| OK | .venv 虚拟环境 | /Users/dayin/Code/a-share-swing-system/.venv |
| OK | .venv Python | 可执行：/Users/dayin/Code/a-share-swing-system/.venv/bin/python |
| OK | 前端构建产物 | /Users/dayin/Code/a-share-swing-system/app/frontend/dist/index.html |
| OK | FastAPI / Uvicorn | 依赖可导入 |
| OK | App 后端导入 | app.backend.main 可导入 |
| OK | 日志文件 | 可写：/Users/dayin/Code/a-share-swing-system/logs/app_server.log |
| OK | 8000 端口 | 本项目 App 已在运行：http://127.0.0.1:8000 |
| OK | macOS Gatekeeper | 未发现明显拦截信息 |

## 常见原因

1. .app 包装器缺失或被移动。
2. 启动文件没有执行权限。
3. macOS 首次打开拦截，需要右键打开。
4. .venv 或 FastAPI/Uvicorn 依赖缺失。
5. 8000 端口被其他程序占用。
6. 前端 dist 尚未构建。

## 安全边界

- 未接券商 API。
- 未真实下单。
- 未读取真实账户。
- 未输出 token / 密码 / 密钥。
