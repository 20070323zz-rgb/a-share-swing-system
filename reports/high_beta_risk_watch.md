# high_beta 持仓风险观察 2026-07-04 00:03:53

本报告只做 high_beta 风险观察，不自动减仓、不自动卖出、不写入 paper_trades.csv、不修改 paper_positions.csv。

## 组合级 high_beta 暴露
- high_beta 持仓数量：1
- high_beta 持仓市值：577.50
- high_beta 占总资产比例：5.77%
- high_beta 占持仓市值比例：19.61%
- 金融地产组市值：1399.20
- 金融地产组占总资产比例：13.99%
- 金融地产组占持仓市值比例：47.51%
- high_beta_exposure_state：HB_WATCH
- high_beta_exposure_reasons：金融地产组占持仓市值超过 40%，组合集中度需观察。
- execution_allowed：false

## 持仓级 high_beta 观察
| symbol | name | state | group | mv | equity_weight | holdings_weight | pnl | rank | rank_change | rank_decay | ret5 | ret10 | vol10 | dd10 | action |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 512880 | 证券ETF | HB_CAUTION / 高波动谨慎 | 金融地产 | 577.50 | 5.77% | 19.61% | 1.20% | 94.493 | 3.186 | 0 | 4.34% | 10.00% | 3.41% | -1.79% | 高波动谨慎观察；不自动减仓或卖出。 |

## 512880 证券ETF 重点观察
- high_beta_risk_state：HB_CAUTION / 高波动谨慎
- 当前市值：577.50
- 占总资产：5.77%
- 占持仓市值：19.61%
- 近 10 日波动率：3.41%
- 近 10 日回撤：-1.79%
- 原因：证券/券商类 ETF 属 high_beta，对成交额、风险偏好和市场情绪更敏感。；金融地产组占持仓市值比例偏高，需观察组合集中度。；浮盈保护层进入复核/锁定候选。；当前 high_beta 占总资产 5.77%，占持仓 19.61%；金融地产组占持仓 47.51%。；近 10 日波动率 3.41%，近 10 日回撤 -1.79%。

## 解释
- high_beta 观察层用于监控证券/券商等高波动 ETF 对市场情绪的敏感性。
- 它与 REVIEW / PROFIT_WATCH 的区别：本报告关注波动、回撤和组合集中度，不改变持仓复核或浮盈保护状态。
- 是否需要自动减仓：否。当前只是 observation。
- 后续重点观察：short_swing 是否转弱、rank 是否连续下降、金融地产组是否继续集中、10 日回撤是否扩大。

## 安全边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不修改 paper_trade_engine.py。
- 不修改 paper_trades.csv / paper_positions.csv。