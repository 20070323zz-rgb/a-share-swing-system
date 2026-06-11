# ETF 模拟盘只读看板

推荐打开方式：

双击：

```text
dashboard/open_dashboard.command
```

或在终端打开：

```bash
open dashboard/index.html
```

也可以在 Safari 地址栏打开：

```text
file:///Users/dayin/Code/a-share-swing-system/dashboard/index.html
```

刷新静态看板：

```bash
python3 dashboard/build_dashboard.py
```

`src/main.py` 和 `scripts/run_daily_close.sh` 已接入该刷新步骤。每次生成最新报告后，`dashboard/index.html` 会同步刷新。

手机端说明：页面采用响应式布局，表格会横向滚动，图表会自动变成单列。iPhone/iPad 可以通过 iCloud Drive、AirDrop 或同一局域网只读静态文件服务打开这份 HTML；网页本身不依赖 Streamlit 服务。

## 当前看板内容

- Control Room：今日结论、系统状态、模拟交易引擎、Top BUY、卖出复核、链接健康。
- 首页指标：总资产、现金、持仓市值、持仓 ETF 数、交易记录、风险提醒。
- 模拟交易引擎：执行状态、dry-run / execute、买入/卖出数量、跳过原因。
- 当前持仓：成本、最新价、市值、浮盈、本金占比、买入理由、风险。
- 今日信号：BUY ranking、双周期状态、风险提示。
- 系统健康：数据健康、自动化状态、隔离 ETF、链接体检、真实交易禁用状态。
- 图表工作台：资产分布、持仓规模、BUY 排名强度、group 暴露。
- 模拟交易：最近交易时间线和完整流水表。
- 报告中心：核心 Markdown/CSV/JSON 报告入口，生成时检查链接文件是否存在。
- 规则与边界：仓位规则、安全边界、本地文件入口。

## 设计参考

看板结构参考了开源量化交易台、专业量化平台、券商组合分析和风险平台的做法：先看今日结论、风险和系统状态，再看持仓、信号、执行、回测和本地文件。详细参考见：

```text
reports/dashboard_redesign_research.md
```

## Streamlit 备选方式

如果要临时查看 Streamlit 版本，可以运行：

```bash
.venv/bin/streamlit run dashboard/app.py
```

## 安全边界

- 只读取本地 CSV 和 Markdown 报告。
- 不接券商 API。
- 不真实下单。
- 不读取真实资金账户。
- 不保存账号、密码、token。
- 不提供真实买入/卖出按钮。
- 不允许通过网页修改交易规则或仓位规则。
