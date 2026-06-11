# 看板彻底升级设计说明

生成日期：2026-06-11

本报告用于说明本次静态看板升级的参考来源与落地原则。它不是交易策略变更，不修改仓位规则，不接券商 API，不提供真实下单能力。

## 参考对象

| 类型 | 来源 | 借鉴点 |
| --- | --- | --- |
| 开源量化 | Freqtrade / FreqUI：https://github.com/freqtrade/frequi | 交易台需要清晰展示持仓、订单、策略状态、执行结果和日志。 |
| 量化平台 | QuantConnect Backtest Results：https://www.quantconnect.com/docs/v2/cloud-platform/backtesting/results | 回测、交易、统计、持仓需要可追溯并与研究报告相连。 |
| 图表平台 | TradingView Features：https://www.tradingview.com/features/ | 观察列表、图表、信号、提醒应在一个工作台中快速扫读。 |
| 券商平台 | Interactive Brokers PortfolioAnalyst：https://www.interactivebrokers.com/en/software/portfolioanalyst.php | 组合平台应突出资产、表现、风险、归因和报告入口。 |
| 风险平台 | BlackRock Aladdin：https://www.blackrock.com/aladdin | 专业风险系统先展示风险状态、系统状态和透明度，再进入明细。 |
| 券商终端 | thinkorswim：https://www.schwab.com/trading/thinkorswim | 终端式工作区需要导航锚点、模块分区、监控列表和高可读表格。 |

## 本次落地

1. 新增深色“模拟 ETF Control Room”首屏驾驶舱。
2. 顶部增加横向导航锚点，便于手机和电脑快速跳转。
3. 将今日结论、模拟交易引擎、Top BUY、卖出复核、链接健康放到第一屏。
4. 新增 System Health 模块，集中展示数据健康、自动化、模拟引擎、链接体检。
5. 新增 Links 报告中心，所有核心本地报告生成时检查文件是否存在。
6. 新增 Design References 模块，记录外部参考来源和借鉴点。
7. 保留原有持仓、卖出复核、BUY Ranking、组合风险、自动化、回测复盘、交易记录等内容。

## 稳定性原则

- 看板仍是 `dashboard/index.html` 静态文件，Safari 可直接打开。
- 不依赖 Streamlit、Flask、Node 服务或后台进程。
- 每次运行 `python3 dashboard/build_dashboard.py` 会刷新 `reports/dashboard_data.json` 和 `dashboard/index.html`。
- daily_close 自动化完成后会自动刷新看板。
- 内置链接使用相对路径，适合本地静态文件浏览。

## 安全边界

- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存密码或 token。
- 不提供真实交易按钮。
- 不允许通过网页修改交易规则。
- 所有交易展示均为本地模拟盘。

