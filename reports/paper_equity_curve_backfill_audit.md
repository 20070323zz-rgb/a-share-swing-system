# 模拟仓权益曲线回填审计

## 输入文件

- 交易流水：`data/paper_trades.csv`，读取 5 条
- 当前持仓：`data/paper_positions.csv`，读取 3 条
- 原始权益曲线：`data/paper_equity_curve.csv`，读取 9 条
- ETF 日线目录：`/Users/dayin/Code/a-share-swing-system/data/etf_daily`

## 字段映射

- 日期：优先 `date`，缺失时使用 `trade_date`。
- 交易方向：`BUY` / `SELL`，兼容 `PAPER_BUY` / `PAPER_SELL`。
- 成交价：优先 `execution_price`，缺失时使用 `price`。
- 现金变化：优先 `net_cash_change`，缺失时用成交额和费用估算。
- 费用：优先 `fee`，否则使用 `commission + stamp_tax + transfer_fee`。

## 回填规则

- 初始本金：10,000.00 元，来源 `reports/paper_performance_summary.json.initial_cash`。
- 从首笔交易前一个可用交易日开始回放；如果没有前一交易日，则从首笔交易日开始。
- 逐日应用交易流水，更新现金和持仓数量。
- 每日按 ETF 本地 close 估值。
- 非交易日或缺当日 close 时使用最近可用 close，并标记为 `estimated_carry_forward`。
- 如果完全找不到价格，标记为 `missing_price_estimated`。

## 安全边界

- 未修改 `data/paper_trades.csv`。
- 未修改 `data/paper_positions.csv`。
- 未修改 `src/paper_trade_engine.py`。
- 未接券商 API。
- 未真实下单。
- 未读取真实账户。