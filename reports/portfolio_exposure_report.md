# 组合暴露研究报告

本报告只读取本地模拟持仓，不修改 paper_positions / paper_trades，不生成真实交易。

## 摘要
- overall_status：CAUTION
- 当前持仓市值：2973.30
- 当前仓位：29.73%
- 风险提示数量：1

## 风险提示
- 组合暂无宽基 ETF，波动可能更依赖行业/主题轮动。

## 持仓暴露
| symbol | name | group | etf_type | risk_profile | market_value | position_ratio | portfolio_weight | data_health | sell_review | note |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| 512800 | 银行ETF | 金融地产 | sector | sector_beta | 855.80 | 8.56% | 28.78% | 正常 | REVIEW | 银行金融红利属性，按低敏感行业处理; sell_review=REVIEW |
| 515000 | 科技ETF | 科技成长 | unknown | manual_review | 1552.00 | 15.52% | 52.20% | 正常 | HOLD | ETF但规则无法确定，需人工确认 |
| 512880 | 证券ETF | 金融地产 | high_beta | high_beta | 565.50 | 5.66% | 19.02% | 正常 | HOLD | 券商/非银高 beta 情绪行业 |

## 暴露汇总
| dimension | bucket | market_value | portfolio_weight |
| --- | --- | ---: | ---: |
| group | 科技成长 | 1552.00 | 52.20% |
| group | 金融地产 | 1421.30 | 47.80% |
| etf_type | unknown | 1552.00 | 52.20% |
| etf_type | sector | 855.80 | 28.78% |
| etf_type | high_beta | 565.50 | 19.02% |
| risk_profile | manual_review | 1552.00 | 52.20% |
| risk_profile | sector_beta | 855.80 | 28.78% |
| risk_profile | high_beta | 565.50 | 19.02% |

## 研究边界
- 暴露报告只用于风险观察和看板展示。
- 不自动改变总仓位、不自动加减仓、不改变单 ETF 上限。