# ETF Rotation Strategy Research

Generated at: 2026-06-18 15:47:04

本报告是回测前研究材料，不是最终交易规则；不修改 BUY ranking、仓位规则或模拟持仓。

## 主流 ETF 轮动框架

1. **动量/相对强弱轮动**：常见做法是在 ETF 池中选择过去一段时间表现更强的少数 ETF，并定期再平衡。Quantpedia 的 sector momentum 示例使用行业 ETF，选择 12 个月动量最强的 3 只并月度调仓，说明“Top N + 定期再平衡”是经典框架之一。来源：https://quantpedia.com/strategies/sector-momentum-rotational-system

2. **趋势 + 相对强弱二维观察**：State Street 的 Sector ETF Momentum Map 用相对强弱趋势和动量两个维度观察行业轮动，支持“横截面对比 + 趋势过滤”的思路。来源：https://www.ssga.com/dk/en_gb/intermediary/insights/sector-etf-momentum-map

3. **经济周期/行业轮动**：Investopedia 对 sector rotation 的说明强调用行业 ETF 承接经济周期、日历效应或地域机会，但也提示时点判断和交易成本会影响有效性。来源：https://www.investopedia.com/articles/exchangetradedfunds/08/sector-rotation.asp

4. **流动性和交易质量过滤**：BlackRock/iShares ETF 尽调框架把 exposure、structure、performance、liquidity 等作为 ETF 选择要素，说明 ETF 池构建不能只看收益。来源：https://www.blackrock.com/sg/en/ishares/education/choosing-the-right-etf

5. **A 股交易单位约束**：上交所 ETF FAQ 明确 ETF 买卖最低 1 手，即 100 份，最小价格变动单位 0.001 元；A 股股票 ETF 通常 T+1，债券/黄金/跨境/货币等部分品种支持 T+0。来源：https://www.sse.com.cn/assortment/fund/etf/question/

6. **QDII 溢价风险**：证券时报报道 2026 年多只 QDII 基金密集提示二级市场溢价风险，说明跨境 ETF 不能只用日线价格动量自动买入。来源：https://www.stcn.com/article/detail/3650684.html

## 回测前常见风险

- 幸存者偏差：当前 183 只多来自现存正式数据文件，不能代表历史任意时点可交易 ETF 池。
- 新基金样本不足：少于 120 个交易日的 ETF 不应进入第一版交易回测。
- 低流动性：成交额过低会放大冲击成本、滑点和成交不确定性。
- 交易成本：当前项目已有佣金、最低佣金、滑点、100 份整数倍，应进入回测。
- QDII 溢价：QDII 需额外加入 IOPV/溢价、汇率、海外交易日和申赎状态检查。
- 重复暴露：同一指数/主题多个 ETF 会让横截面排名看似分散，实际是同一风险源。
- 数据源差异：JQData/BaoStock 的复权、成交额口径需保持一致。

## 当前策略适合的回测方式

- 日频，收盘后生成信号。
- 第一版只做 ETF，不做个股。
- 最多持有 3 只。
- 单只不超过模拟本金 20%。
- 交易成本包含佣金 0.00012、最低佣金 5 元、滑点 0.0003、100 份整数倍。
- QDII 暂不自动买入。
- market_state 先展示，不直接改变仓位。
- 比较 original ranking 与 adjusted preview，但 adjusted preview 暂不进入真实模拟交易规则。

## 当前策略不适合做什么

- 不适合高频或日内。
- 不适合全市场个股 alpha。
- 不适合复杂机器学习主策略直接上线。
- 不适合对 QDII 做无溢价检查的自动交易。
- 不适合用全 183 只不加过滤直接回测。
