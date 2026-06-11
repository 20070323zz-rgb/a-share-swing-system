# paper_trade_engine 设计报告

- 模式：rule_validation。
- 只服务本地模拟盘自动执行验证。
- 卖出优先于买入。
- 买入要求 trade_pool、mid_trend=BUY、short_swing=BUY、Top3、未持有、未冷静期、仓位合规。
- 卖出只在 SELL、止损、mid_trend SELL、short_swing SELL+低分、data_health error 等硬条件触发。
- 买入后 1-2 日保护期内，除硬风控外不自动卖出。
- 单只 ETF 上限 20%，最多持有 3 只，默认 neutral 目标仓位 30%。
- dashboard 只读展示，不提供真实交易按钮。

## 下一步
- 继续回测自动买卖规则对回撤、胜率和过度交易的影响。