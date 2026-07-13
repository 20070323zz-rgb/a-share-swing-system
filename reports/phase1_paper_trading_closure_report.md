# 第一阶段模拟买卖闭环升级报告

- 生成时间：2026-07-10 16:28:05
- 阶段目标：模拟盘自动买卖闭环 + 真实化交易成本/滑点/交易单位约束。
- 本报告是本地模拟盘研究报告，不是真实交易方案。

## 闭环状态
- paper_trade_engine 状态：executed
- dry_run：False
- 今日买入数量：2
- 今日卖出数量：1
- 今日跳过重复：False
- 跳过原因：
- 执行前现金：7608.44
- 执行后现金：7040.47
- 执行后持仓数：3
- 执行后仓位：29.96%

## 规则落地
- 卖出优先于买入。
- 买入只考虑 trade_pool、BUY 共振、Top3、未持有、未冷静期、仓位和现金合规的 ETF。
- 单只 ETF 不超过总权益 20%，最多持有 3 只。
- 交易数量按 100 份整数倍。
- 同一交易日、同一 symbol、同一 action、同一 source 防重复写入。

## 交易成本
- 佣金率：0.00012
- 单笔最低佣金：5.00 元
- 滑点率：0.0003
- 今日佣金：15.00
- 今日滑点成本估算：0.67
- ETF 模拟暂不计印花税：0.0

## 安全边界
- REAL_TRADE_ENABLED：False
- BROKER_API_ENABLED：False
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。

## 今日计划摘要
| symbol | action | status | quantity | gross_amount | commission | reason |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 512800 | SELL | executed | 1100 | 836.85 | 5 | max_holding_days reached without signal recovery |
| 515000 | SELL | skipped_no_sell_signal | 1000 | 1621.51 | 5 | sell rules not triggered |
| 516510 | BUY | executed | 700 | 1263.88 | 5 | paper_rule_validation; rank=1; rank_score=88.861036; mid_trend=BUY; short_swing=BUY; amount=1263.88 |
| 159929 | BUY | executed | 100 | 125.94 | 5 | paper_rule_validation; rank=2; rank_score=86.216237; mid_trend=BUY; short_swing=BUY; amount=125.94 |
| 515000 | BUY | skipped_rule_blocked | 0 | 0 | 0 | already held |