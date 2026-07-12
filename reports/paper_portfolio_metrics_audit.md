# 模拟仓绩效指标审计 2026-07-11 16:43:41

本审计只读取本地模拟仓文件，不修改 paper_trades.csv / paper_positions.csv。

## 当前数据来源
- 持仓来源：`/Users/dayin/Code/a-share-swing-system/data/paper_positions.csv`，当前 3 条持仓记录。
- 交易来源：`/Users/dayin/Code/a-share-swing-system/data/paper_trades.csv`，当前 11 条交易流水。
- 最新估值价格：优先使用 positions 当前价；权益曲线使用 `data/etf_daily/` 本地 close。

## 当前能计算的指标
- 当前现金、持仓市值、当前总资产、总盈亏、总收益率。
- 已实现盈亏：来自 SELL 流水或 FIFO 配对。
- 未实现盈亏：来自当前持仓市值与成本。
- 交易次数、买卖次数、胜率、平均盈利/亏损、profit factor。
- 权益曲线、每日盈亏、累计盈亏、最大回撤。

## 当前缺少或需要估算的字段
- 早于第一笔模拟交易之前的权益历史不存在，不能伪造。
- 若交易流水缺少完整 cost 字段，会使用 commission/stamp_tax/transfer_fee 或 fee 推导。
- 未平仓逐笔 PnL 使用最新 close 估算，状态标记为 open。

## 新增派生文件
- `/Users/dayin/Code/a-share-swing-system/data/paper_equity_curve.csv`
- `/Users/dayin/Code/a-share-swing-system/reports/paper_performance_summary.json`
- `/Users/dayin/Code/a-share-swing-system/reports/paper_performance_summary.md`
- `/Users/dayin/Code/a-share-swing-system/reports/paper_performance_daily.csv`
- `/Users/dayin/Code/a-share-swing-system/reports/paper_trade_pnl.csv`
- `/Users/dayin/Code/a-share-swing-system/reports/paper_trade_pnl.md`
- `/Users/dayin/Code/a-share-swing-system/reports/paper_equity_curve.md`

## 结论
- 是否需要新增 `data/paper_equity_curve.csv`：是，已新增。
- 当前权益曲线记录数：23。
- 当前逐笔 PnL 记录数：7。
- 安全边界：未接券商 API，未真实下单，未读取真实账户。