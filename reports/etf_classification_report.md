# ETF 分类研究报告

本报告是 phase2_model_research_v1 的研究侧分类文件，不修改交易规则、不修改模拟仓、不生成买卖。

## 摘要
- 分类 ETF 数量：185
- 类型分布：{'unknown': 75, 'broad_index': 22, 'commodity_resource': 21, 'sector': 19, 'theme': 18, 'qdii': 15, 'bond_cash': 12, 'high_beta': 3}
- pool 分布：{'research_only': 77, 'trade_pool': 76, 'observe_pool': 32}
- excluded/failed/unresolved 数量：0

## 当前持仓分类
| symbol | name | group | pool | etf_type | risk_profile | holding_profile | stop_loss_pct | auto_buy_allowed | reason |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| 512800 | 银行ETF | 金融地产 | trade_pool | sector | sector_beta | 10-30 | 6.00% | 1 | 银行金融红利属性，按低敏感行业处理 |
| 512880 | 证券ETF | 金融地产 | trade_pool | high_beta | high_beta | 5-20 | 5.00% | 1 | 券商/非银高 beta 情绪行业 |
| 515000 | 科技ETF | 科技成长 | trade_pool | unknown | manual_review | N/A | 0.00% | 0 | ETF但规则无法确定，需人工确认 |

## 分类规则
- broad_index：宽基指数，适合中期趋势与横截面轮动研究。
- sector：行业/风格 ETF，退出敏感度中等，需要行业新闻作为解释或风险过滤。
- theme/high_beta：主题或高 beta ETF，短周期更敏感，新闻情绪暂不进入 BUY 主分。
- commodity_resource：周期资源 ETF，需要关注商品价格、政策和供需事件。
- bond_cash：债券/货币类，默认不进入进攻型自动买入。
- qdii：跨境类，需要额外溢价、汇率、海外交易日检查。
- unknown：不强行分类，需要人工复核。

## 安全边界
- 只写入 data/etf_classification.csv 和兼容文件 data/etf_type_classification.csv。
- 不修改 watchlist、不修改 trade_pool、不修改 paper_positions/paper_trades。
- 不接券商 API，不真实下单。