# 模型防过拟合护栏

1. 每个新候选模型最多新增 2-3 个核心 alpha 因子。
2. 每个因子必须有明确经济逻辑。
3. 不允许因为历史收益最高就直接采用。
4. 必须输出年度表现、月度表现、最大回撤期表现。
5. 必须保留 510300 buy-and-hold、original、adjusted、top10_diversified_filter_v2 作为对照。
6. 必须计算交易次数和成本。
7. 必须检查是否依赖单一 ETF 或单一年份。
8. 不允许使用 future_return、future_drawdown、future_rank 作为特征。
9. 不允许使用没有 available_date 的外部数据。
10. 新模型如果只在单一年份有效，不得标记为候选。
11. 新模型如果收益提高但回撤大幅恶化，不得标记为可 shadow。
12. 新模型只能 research/backtest，不得接执行层。