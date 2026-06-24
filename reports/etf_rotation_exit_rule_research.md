# ETF Rotation Exit Rule Research 2026-06-18 16:01:13

本报告是 ETF 轮动退出规则调研材料，不是最终交易规则；不接入 paper_trade_engine，不修改模拟持仓。

## 摘要结论

1. ETF 轮动最自然的退出机制不是单一止盈止损，而是 ranking 掉队、趋势破坏、持有期效率和波动自适应止损的组合。
2. 固定止损/固定止盈适合作为 baseline，但容易过拟合，也容易卖飞趋势强的 ETF。
3. ATR/波动率止损更适合跨 ETF 类型比较，因为宽基、主题、高 beta、债券 ETF 的波动结构差异很大。
4. 移动止盈适合行业/主题/高 beta ETF，但要重点观察 whipsaw 和 profit giveback。
5. QDII 暂不进入自动退出规则，需要额外溢价、汇率、海外交易日和申赎状态数据。
6. 债券/货币 ETF 应单独设计，不套普通权益 ETF 的 5%-10% 止损。

## 常见退出机制评估

| 规则 | 适合 ETF 轮动吗 | 优点 | 主要风险 | 是否需回测 |
| --- | --- | --- | --- | --- |
| 固定止损 | baseline 适合 | 简单、可控最大亏损 | 不适配不同 ETF 波动，容易过紧 | 必须 |
| 固定止盈 | 只适合 baseline | 便于观察利润兑现 | 趋势行情容易卖飞 | 必须 |
| 移动止盈 | 行业/主题较适合 | 保护利润，允许趋势延续 | 震荡市被洗出 | 必须 |
| ATR 止损 | 强候选 | 波动自适应 | 参数多，可能过拟合 | 必须 |
| 均线趋势破坏 | 强候选 | 符合趋势策略 | 滞后或噪声 | 必须 |
| ranking 掉队 | 核心候选 | 符合横截面轮动 | 排名抖动导致换手 | 必须 |
| 时间止损 | 辅助候选 | 约束资金效率 | 慢趋势被卖飞 | 必须 |
| 市场状态恶化 | 风险叠加 | 控制系统性风险 | 可能踏空 | 先 review only |
| 组合暴露过高 | 风险叠加 | 控制集中度 | 不宜强制卖出 | 先 review only |

## 对当前项目的适配判断

- 当前系统已有 BUY ranking、sell_signal_review、ETF 分类、组合暴露和 shadow tracking；最适合优先回测 ranking exit + trend breakdown + ATR stop。
- 当前最多持有 3 只、单只 20%、交易成本和 100 份单位约束已经更贴近真实模拟，应在退出规则回测中保留。
- 不建议先上线固定 5% 止损或固定 10% 止盈。它们可以做 benchmark，但不能未经回测直接执行。

## 来源

- [Quantpedia sector momentum rotational system](https://quantpedia.com/strategies/sector-momentum-rotational-system)：行业/ETF 动量轮动的 Top-N + 定期再平衡框架参考。
- [State Street sector ETF momentum map](https://www.ssga.com/dk/en_gb/intermediary/insights/sector-etf-momentum-map)：用相对强弱和动量观察行业 ETF 轮动。
- [CME Group: ATR](https://www.cmegroup.com/education/courses/technical-analysis/understanding-average-true-range-indicator.html)：ATR 是波动率/真实波幅工具，适合做跨品种波动自适应止损研究。
- [Investopedia trailing stop](https://www.investopedia.com/terms/t/trailingstop.asp)：移动止损/移动止盈的基础定义和风险提示。
- [BlackRock/iShares ETF selection](https://www.blackrock.com/sg/en/ishares/education/choosing-the-right-etf)：ETF 选择应考虑流动性、结构、表现和交易质量。
- [SSE ETF FAQ](https://www.sse.com.cn/assortment/fund/etf/question/)：A 股 ETF 交易单位和交易机制约束参考。

## 安全边界

- 不接券商 API。
- 不真实下单。
- 不修改 paper_trades.csv。
- 不修改 paper_positions.csv。
- 不改变当前模拟盘执行逻辑。
