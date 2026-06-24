# Exit Rule Backtest Design 2026-06-18 16:01:13

本设计用于 Phase 4A/4B 回测，不修改当前执行规则。

| 组合 | 逻辑 | 优点 | 缺点 | 可能过拟合点 | 需要观察指标 |
| --- | --- | --- | --- | --- | --- |
| No explicit profit stop + ranking exit | 只靠 ranking 掉队和基础风险退出 | 最贴近轮动本质，避免卖飞 | 回撤可能较大 | ranking 阈值 | turnover, drawdown, profit giveback |
| Fixed stop + ranking exit | 固定止损叠加排名掉队 | 简单，便于 baseline | 止损可能不适配类型 | 固定比例参数 | max drawdown, win rate, cost impact |
| ATR stop + ranking exit | 波动自适应止损叠加排名掉队 | 适配不同波动 ETF | ATR 倍数可能过拟合 | ATR window/multiple | Calmar, whipsaw count |
| Fixed stop + trailing profit + ranking exit | 固定亏损控制 + 利润回撤保护 | 兼顾亏损和盈利回吐 | 震荡市被洗出 | profit start / trail pct | profit giveback, avg win/loss |
| ATR trailing + trend breakdown | 波动自适应移动止盈 + 均线破坏 | 适合趋势延续 | 趋势破坏滞后 | MA window, ATR multiple | CAGR, drawdown, holding days |
| Time stop + ranking exit | 持有过久且收益不足时退出 | 提高资金效率 | 慢趋势被卖飞 | max days / min return | capital efficiency, turnover |
| ETF type-aware exit | 按 ETF 类型选择不同搜索空间 | 更符合波动差异 | 类型分类错误会污染结果 | type mapping | all metrics by type |
| Market state review only | 市场弱时触发复核，不自动退出 | 低风险接入 | 不能直接降低回撤 | state threshold | state-conditioned returns |

## 统一评价指标
- CAGR
- max drawdown
- Sharpe
- Calmar
- win rate
- avg win/loss
- turnover
- average holding days
- profit giveback
- whipsaw count
- transaction cost impact

## 第一版约束
- 只用推荐 trade_pool，不直接用全 183 只。
- 加入佣金、最低佣金、滑点、100 份整数倍。
- QDII、unknown、低流动性、短历史标的不进入自动交易池。
- market_state 和 portfolio_exposure 先作为 review/分组分析，不强制交易。
