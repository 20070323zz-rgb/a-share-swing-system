# 打开 App 说明

最像普通 App 的方式：

1. 打开项目目录：`/Users/dayin/Code/a-share-swing-system`
2. 双击：`dist/量化研究控制台.app`
3. 浏览器会自动打开：`http://127.0.0.1:8000`

如果还没有这个 App，先运行：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/create_app_shortcut.sh
```

备用方式：

1. 打开项目目录：`/Users/dayin/Code/a-share-swing-system`
2. 双击：`打开量化研究控制台.command`
3. 浏览器会自动打开：`http://127.0.0.1:8000`

如果 macOS 提示无法打开，请右键点击 `.app` 或 `.command`，选择“打开”。

如果仍然打不开：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/diagnose_app_launch.sh
```

如果诊断提示权限问题或 `.app` 缺失：

```bash
bash scripts/fix_app_launch_permissions.sh
```

如果 8000 端口已经是本项目 App 在运行，直接打开：

```text
http://127.0.0.1:8000
```

详细日志：

```text
logs/app_server.log
logs/app_launch_status.json
reports/app_launch_diagnostics.md
```

固定到 Dock：

- 推荐把 `dist/量化研究控制台.app` 拖到 Dock。
- `.command` 文件只适合作为备用启动器。

日志位置：

```text
logs/app_server.log
```

关闭 App：

关闭启动时弹出的终端窗口，或在终端里按 `Control + C`。

安全说明：

这个 App 只是本地量化研究控制台，不接券商 API，不真实下单，不读取真实账户，不显示 token 或密码。

历史权益曲线：

- `data/paper_equity_curve.csv` 是日常绩效模块持续写入的权益曲线。
- `data/paper_equity_curve_backfilled.csv` 是由交易流水和历史 close 估算回填的曲线。
- 回填数据会在 App 中标注为估算，不代表真实每日账户快照。
