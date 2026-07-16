# 第一次模拟买入复盘报告

检查时间：2026-06-10

本报告只复盘本地模拟盘文件和本地报告，不接券商 API，不真实下单，不读取真实账户，不新增买入。

## 本次模拟买入摘要

| trade_date | ETF | 名称 | 买入金额 | 成交价 | 数量 | 策略来源 | execution_price_type |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| 2026-06-09 | 515220 | 煤炭ETF | 1496.00 | 1.360 | 1100 | resonance | close_price |
| 2026-06-09 | 512800 | 银行ETF | 871.20 | 0.792 | 1100 | resonance | close_price |
| 2026-06-09 | 515880 | 证券公司ETF | 508.50 | 1.695 | 300 | resonance | close_price |

- 买入总金额：2875.70
- 当前现金：7124.30
- 当前持仓市值：2875.70
- 当前总资产：10000.00
- 当前持仓数：3

## 规则检查

1. 仓位规则：通过
   - 本次 market_neutral 计划总仓位为 20%-40%，实际持仓 28.76%，符合规则。
   - 最多持有 3 只 ETF，当前正好 3 只，符合规则。

2. 标的类型：通过
   - `515220`、`512800`、`515880` 均为 `watchlist.csv` 中的 ETF。
   - 本次未买入个股。

3. 单只 ETF 20% 上限：通过
   - 单只上限为 2000.00。
   - 最大单只为 `515220`，市值 1496.00，占模拟本金 14.96%。
   - `512800` 为 871.20，占 8.71%。
   - `515880` 为 508.50，占 5.09%。

4. failed/quarantine ETF：通过
   - 本次 3 只买入 ETF 均不在 failed/quarantine/unresolved 列表中。

5. `515880` data_health caution：部分通过
   - `reports/buy_signal_ranking.md` 已标注：`data_health 提醒，需人工复核`。
   - `reports/latest_data_health.md` 中 `515880` 状态为“提醒”，原因为存在一次极端单日涨跌幅提示。
   - 但 `data/paper_positions.csv` 和 `reports/latest_paper_portfolio.md` 的 `risk_alert` 字段目前为空，尚未把该 caution 显式带入持仓风险字段。
   - 建议后续优化：持仓估值报告应把 data_health warning 映射到持仓 `risk_alert` 或单独的 `data_warning` 字段。

6. `paper_trades.csv` 与 `paper_positions.csv` 一致性：通过
   - 两个文件均包含 3 只标的：`515220`、`512800`、`515880`。
   - 交易金额合计：2875.70。
   - 持仓 cost 合计：2875.70。
   - 持仓 market_value 合计：2875.70。
   - 当前为买入当天收盘价估值，浮动盈亏为 0。

7. `latest_paper_portfolio.md` 估值：通过
   - 现金：7124.30，与交易后模拟现金一致。
   - 持仓市值：2875.70，与 positions 合计一致。
   - 总资产：10000.00，与现金 + 持仓市值一致。
   - 已实现盈亏：0.00。
   - 浮动盈亏：0.00。

8. `dashboard_data.json`：通过
   - `paper_summary.cash`：7124.30
   - `paper_summary.market_value`：2875.70
   - `paper_summary.total_equity`：10000.00
   - `paper_summary.position_count`：3
   - `positions` 包含：`515220`、`512800`、`515880`
   - `trades` 包含：`515220`、`512800`、`515880`

## 明日自动更新后重点观察

1. 价格与止损
   - `515220` 止损参考：1.258
   - `512800` 止损参考：0.7326
   - `515880` 止损参考：1.567875
   - 明日更新后重点检查是否接近或跌破止损价。

2. `515880` 数据健康提醒
   - 继续观察 `data_health` 是否仍提示极端涨跌幅。
   - 若明日仍有异常提醒，应优先复核该 ETF 的历史复权、成交量和价格口径。

3. 仓位与重复买入
   - 当前已满 3 只 ETF，不应自动继续新增持仓。
   - 若 BUY ranking 仍有新标的，也应先等待已有持仓复核，不应突破 3 只上限。

4. 双周期信号变化
   - 重点观察 3 只持仓是否继续维持 `mid_trend BUY + short_swing BUY`。
   - 若出现 short_swing 转弱但 mid_trend 仍在，可继续观察。
   - 若 mid_trend 转弱或出现 SELL，应进入卖出/风控复核。

5. 模拟盘盈亏
   - daily_close 后应自动刷新 `reports/latest_paper_portfolio.md`。
   - 重点看 `unrealized_pnl`、`unrealized_pnl_pct`、`cash`、`total_equity` 是否正确更新。

## 安全边界确认

- 不接券商 API：yes
- 不真实下单：yes
- 不读取真实账户：yes
- 不保存密码/token：yes
- 不新增买入：yes
- 不修改持仓：yes
- 本报告只做第一次模拟买入后的复盘检查：yes

