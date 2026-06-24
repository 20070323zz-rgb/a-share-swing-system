# ETF 轮动成熟模型参考报告 2026-06-19 00:51:29

本报告只用于 Phase 4B-1 研究，不直接修改交易策略、仓位规则或模拟持仓。

## 摘要结论

成熟 ETF/行业轮动框架通常不会机械地每天买入 Top3，而是把中期动量、相对强弱、趋势确认、风险调整、组合分散和换手控制结合起来。本项目的 ranking_model_v2 因此采用“Top10 候选池 + 二次筛选”的研究结构。

## 成熟框架参考

1. Sector momentum / sector rotation
   - 常见思想：按行业或 ETF 的中期表现排序，选 TopN，并以月度或较低频率再平衡，避免日频噪音驱动交易。
   - 可迁移：A 股行业 ETF 适合做横截面强弱比较，但需要加入政策、主题拥挤和流动性约束。
   - 参考：Quantpedia sector momentum/sector rotation 研究框架 https://quantpedia.com/strategies/sector-momentum/

2. Relative strength rotation
   - 常见思想：不仅看绝对涨幅，还看是否跑赢基准、跑赢同组资产。
   - 可迁移：本项目使用 relative_strength_vs_510300 与 relative_strength_vs_group，避免只买市场 beta。
   - 参考：Gary Antonacci dual momentum 讨论了 relative momentum 与 absolute momentum 的结合 https://www.optimalmomentum.com/research-papers/

3. Trend following / trend confirmation
   - 常见思想：用移动均线、趋势斜率等确认趋势，避免买入短反弹但中期趋势仍弱的资产。
   - 可迁移：MA20/MA60、trend_slope_20 和 ma_distance_20 适合作为 ETF 日线模型的趋势确认。
   - 参考：Meb Faber tactical asset allocation 使用移动均线趋势过滤思想 https://mebfaber.com/timing-model/

4. Risk-adjusted momentum
   - 常见思想：动量要扣除波动、回撤或 ATR；高波动上涨不一定更优。
   - 可迁移：本项目将 volatility/drawdown 作为风险惩罚，不把它们当主要 alpha 因子。
   - 参考：Moskowitz, Ooi, Pedersen time-series momentum 框架强调趋势收益与波动风险 https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum

5. Portfolio construction
   - 常见思想：从 TopN 候选池二次筛选，控制同类资产、主题拥挤和 high beta 暴露。
   - 可迁移：A 股 ETF 同质化明显，同一主题常有多只产品，直接 Top3 容易重复暴露。
   - 参考：BlackRock/iShares ETF 交易教育材料强调流动性、价差和成交质量 https://www.ishares.com/us/education/etf-education/etf-trading

6. Turnover control
   - 常见思想：最小持仓天数、确认天数、cooldown 和最小交易金额能降低交易成本。
   - 可迁移：小资金 ETF 轮动受最低佣金冲击明显，本项目必须做成本感知。
   - 参考：State Street SPDR ETF trading best practices 强调订单时点、流动性和交易成本 https://www.ssga.com/us/en/intermediary/etfs/resources/education/how-to-trade-etfs

7. Market regime / risk state
   - 常见思想：risk-on 可提高成长或 high beta 容忍度；risk-off 应降低风险资产暴露。
   - 本轮处理：只研究，不强制接入执行层。
   - 参考：Vanguard ETF 交易实践强调 ETF 价格、折溢价、价差和交易时点 https://investor.vanguard.com/investor-resources-education/etfs/how-to-trade-etfs

## A 股 ETF 迁移注意

- 适合迁移：中期动量、相对强弱、趋势确认、风险调整、同 group 分散、低换手。
- 不能直接迁移：美股 ETF 的全天高流动性假设、低佣金假设、QDII 无时差假设、全资产全球配置口径。
- A 股额外风险：政策预期变化、主题 ETF 波动、流动性分化、同类 ETF 重复、QDII 溢价/汇率/海外交易日、数据源滞后、小资金最低佣金。
- 本项目只使用本地日线价量数据，不引入机构级不可得数据。
- 成熟框架只作为候选，必须通过本地回测验证，不能直接上线。
