# 组合暴露研究报告

本报告只读取本地模拟持仓，不修改 paper_positions / paper_trades，不生成真实交易。

## 摘要
- overall_status：CAUTION
- 当前持仓市值：2945.20
- 当前仓位：29.45%
- 估值日期：2026-07-03
- 估值口径：paper_positions + etf_daily latest close
- 价格警告数量：0
- 风险提示数量：1

## 风险提示
- 组合暂无宽基 ETF，波动可能更依赖行业/主题轮动。

## 持仓暴露
| symbol | name | group | etf_type | latest_close | as_of_date | market_value | position_ratio | portfolio_weight | data_health | sell_review | price_status | note |
| --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| 512800 | 银行ETF | 金融地产 | sector | 0.7470 | 2026-07-03 | 821.70 | 8.22% | 27.90% | 正常 | REVIEW | ok | 银行金融红利属性，按低敏感行业处理; sell_review=REVIEW |
| 515000 | 科技ETF | 科技成长 | unknown | 1.5460 | 2026-07-03 | 1546.00 | 15.46% | 52.49% | 正常 | REVIEW | ok | ETF但规则无法确定，需人工确认; sell_review=REVIEW |
| 512880 | 证券ETF | 金融地产 | high_beta | 1.1550 | 2026-07-03 | 577.50 | 5.78% | 19.61% | 正常 | HOLD | ok | 券商/非银高 beta 情绪行业 |

## 暴露汇总
| dimension | bucket | market_value | portfolio_weight |
| --- | --- | ---: | ---: |
| group | 科技成长 | 1546.00 | 52.49% |
| group | 金融地产 | 1399.20 | 47.51% |
| etf_type | unknown | 1546.00 | 52.49% |
| etf_type | sector | 821.70 | 27.90% |
| etf_type | high_beta | 577.50 | 19.61% |
| risk_profile | manual_review | 1546.00 | 52.49% |
| risk_profile | sector_beta | 821.70 | 27.90% |
| risk_profile | high_beta | 577.50 | 19.61% |

## 研究边界
- 暴露报告只用于风险观察和看板展示。
- 不自动改变总仓位、不自动加减仓、不改变单 ETF 上限。