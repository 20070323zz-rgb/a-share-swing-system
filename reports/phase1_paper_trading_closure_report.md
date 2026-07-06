# 第一阶段模拟买卖闭环升级报告

- 生成时间：2026-07-04 00:00:52
- 阶段目标：模拟盘自动买卖闭环 + 真实化交易成本/滑点/交易单位约束。
- 本报告是本地模拟盘研究报告，不是真实交易方案。

## 闭环状态
- paper_trade_engine 状态：executed
- dry_run：False
- 今日买入数量：0
- 今日卖出数量：0
- 今日跳过重复：False
- 跳过原因：
- 执行前现金：7058.11
- 执行后现金：7058.11
- 执行后持仓数：3
- 执行后仓位：29.44%

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
- 今日佣金：0.00
- 今日滑点成本估算：0.00
- ETF 模拟暂不计印花税：0.0

## 安全边界
- REAL_TRADE_ENABLED：False
- BROKER_API_ENABLED：False
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。

## 今日计划摘要
| symbol | action | status | quantity | gross_amount | commission | reason |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 512800 | SELL | skipped_no_sell_signal | 1100 | 821.45 | 5 | sell rules not triggered |
| 515000 | SELL | skipped_no_sell_signal | 1000 | 1545.54 | 5 | sell rules not triggered |
| 512880 | SELL | skipped_no_sell_signal | 500 | 577.33 | 5 | sell rules not triggered |
| 512010 | BUY | skipped_rule_blocked | 0 | 0 | 0 | max holdings reached |
| 512880 | BUY | skipped_rule_blocked | 0 | 0 | 0 | already held |
| 159929 | BUY | skipped_rule_blocked | 0 | 0 | 0 | max holdings reached |