# 组合暴露研究报告

本报告只读取本地模拟持仓，不修改 paper_positions / paper_trades，不生成真实交易。

## 摘要
- overall_status：CAUTION
- 当前持仓市值：3011.40
- 当前仓位：30.11%
- 估值日期：2026-07-09
- 估值口径：paper_positions + etf_daily latest close
- 价格警告数量：0
- 风险提示数量：2

## 风险提示
- 科技成长 占持仓市值 95.8%，主题集中度偏高。
- 组合暂无宽基 ETF，波动可能更依赖行业/主题轮动。

## 持仓暴露
| symbol | name | group | etf_type | latest_close | as_of_date | market_value | position_ratio | portfolio_weight | data_health | sell_review | price_status | note |
| --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| 515000 | 科技ETF | 科技成长 | unknown | 1.6220 | 2026-07-09 | 1622.00 | 16.22% | 53.86% | 正常 | REVIEW | ok | ETF但规则无法确定，需人工确认; sell_review=REVIEW |
| 516510 | 云计算ETF | 科技成长 | theme | 1.8050 | 2026-07-09 | 1263.50 | 12.63% | 41.96% | N/A | N/A | ok | 主题/科技成长关键词 |
| 159929 | 医药ETF | 消费医药 | sector | 1.2590 | 2026-07-09 | 125.90 | 1.26% | 4.18% | N/A | N/A | ok | 行业/风格关键词 |

## 暴露汇总
| dimension | bucket | market_value | portfolio_weight |
| --- | --- | ---: | ---: |
| group | 科技成长 | 2885.50 | 95.82% |
| group | 消费医药 | 125.90 | 4.18% |
| etf_type | unknown | 1622.00 | 53.86% |
| etf_type | theme | 1263.50 | 41.96% |
| etf_type | sector | 125.90 | 4.18% |
| risk_profile | manual_review | 1622.00 | 53.86% |
| risk_profile | theme_beta | 1263.50 | 41.96% |
| risk_profile | sector_beta | 125.90 | 4.18% |

## 研究边界
- 暴露报告只用于风险观察和看板展示。
- 不自动改变总仓位、不自动加减仓、不改变单 ETF 上限。