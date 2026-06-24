# 本地正式版使用说明

版本：v0.1.0-local

## 如何启动

方式一：双击本地 App

先生成本地 App 包装器：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/create_app_shortcut.sh
```

然后双击：

- `dist/量化研究控制台.app`

方式二：双击启动器

双击项目根目录中的：

- `打开量化研究控制台.command`
- 或 `A-Share Swing App.command`

方式三：终端启动

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/run_app.sh
```

方式四：局域网模式

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/run_app.sh --lan
```

局域网模式只适合同一 Wi-Fi 下临时查看，不建议公网部署。

## 如何关闭

关闭启动 App 的终端窗口，或在终端按 `Ctrl+C`。

## 如何查看日志

主要日志：

- `logs/app_server.log`
- `logs/app_tasks/latest.log`
- `logs/daily_close.log`

也可以在 App 的“设置与安全 -> 日志”中查看。

## 如何固定到桌面或 Dock

- 推荐把 `dist/量化研究控制台.app` 拖到桌面或 Dock。
- 如果 macOS 提示无法打开，请右键点击 App，选择“打开”。
- `.command` 文件可以拖到桌面，但不适合固定到 Dock。
- 图标资源位于 `assets/app_icon.svg` 和 `assets/app_icon.png`，均为本地自绘，不使用外部版权素材。

## 如何刷新报告

进入 App 的“设置与安全 -> 研究任务”，使用白名单任务：

- 刷新全部研究报告；
- 刷新模拟仓绩效；
- 生成交易复盘报告；
- 回填模拟仓历史权益曲线；
- 创建本地 App 快捷图标；
- 刷新 shadow 观察报告。

这些任务都是本地研究任务，不会真实交易。

## 历史权益曲线说明

早期模拟仓没有每天持续保存完整账户快照，因此原始 `data/paper_equity_curve.csv` 记录可能较少。现在可以生成：

```text
data/paper_equity_curve_backfilled.csv
```

它由模拟交易流水和 ETF 历史收盘价估算回填。App 会标注“历史回填数据（估算）”，不会把它伪装成真实每日快照。

## 如何确认安全边界

进入“设置与安全 -> 安全边界”，确认：

- 真实交易：关闭；
- 券商接口：关闭；
- 真实账户读取：关闭；
- Shadow 接执行层：关闭；
- 网页任意命令：关闭。

## 常见问题

### 离开 PyCharm 后打不开

请优先使用双击启动器，或运行：

```bash
bash scripts/check_app_env.sh
```

也可以运行更完整的启动诊断：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/diagnose_app_launch.sh
```

如果提示权限问题或 `.app` 包装器缺失：

```bash
bash scripts/fix_app_launch_permissions.sh
```

诊断结果会写入：

- `reports/app_launch_diagnostics.md`
- `reports/app_launch_diagnostics.json`
- `logs/app_launch_status.json`

这些脚本不会读取 `.env` 内容，不会显示 token，不会真实交易。

### 8000 端口被占用

启动脚本会提示端口占用。若本项目已经在运行，直接访问：

```text
http://127.0.0.1:8000
```

若被其他程序占用，请关闭占用 8000 端口的其他程序后重试。启动脚本不会强杀任何进程。

### 前端页面缺失

启动脚本会尝试自动构建前端。如果电脑没有 npm，请先安装 Node.js/npm。

## 为什么不是实盘系统

本项目当前定位是 ETF 模拟盘和量化学习系统。它不接券商 API，不读取真实账户，不真实下单，不保存交易密码。

## 为什么不能公网部署

当前 App 只面向本机本地研究。公网部署会引入账户安全、网络暴露、任务误触发和数据源密钥管理风险，不符合当前 L2 权限边界。
