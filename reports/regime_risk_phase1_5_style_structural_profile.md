# Regime & Risk Allocation Phase 1.5 - Style / Structural Profile

本报告为研究层，不是交易方案。Structural / Realized Risk 均不接执行层。

## 摘要
- UNKNOWN 从 73 降至：0
- UNKNOWN 目标 <= 15：True
- style_profile 分布：{'COMMODITY_CYCLICAL': 35, 'QDII_OBSERVATION': 24, 'HIGH_BETA_THEME': 23, 'SECTOR_DEFENSIVE': 21, 'DIVIDEND': 20, 'CORE_MID_CAP': 16, 'BOND': 15, 'CORE_LARGE_CAP': 11, 'GROWTH_THEME': 10, 'SECTOR_CYCLICAL': 7, 'GROWTH_BROAD': 1}
- realized risk 分布：{'CORE': 37, 'HIGH_BETA': 37, 'OFFENSIVE': 37, 'BALANCED': 36, 'DEFENSIVE': 36}
- structural risk 分布：{'OFFENSIVE': 68, 'CORE': 38, 'BALANCED': 35, 'HIGH_BETA': 27, 'DEFENSIVE': 15}

## 定义
- Realized Risk：recent market-data realized risk based on volatility/beta/drawdown/downside/capture cross-sectional scoring
- Structural Risk：stable asset/style/concentration/long-cycle risk character based on ETF type, style keywords and longer-window risk metrics
- Structural Risk != Realized Risk。
- Style Profile != Risk Profile。

## Structural Risk 权重
- {'asset_class_and_concentration': 0.3, 'style_attribute': 0.25, 'long_cycle_risk_features': 0.35, 'diversification_concentration_adjustment': 0.1}
- 分层：0-25 DEFENSIVE, 25-45 CORE, 45-60 BALANCED, 60-80 OFFENSIVE, 80-100 HIGH_BETA, with asset-type constraints

## 当前组合双风险画像
- 组合加权 realized_risk_score：51.3118
- 组合加权 structural_risk_score：66.9416
- 若 515000 权重较大，组合结构性风险会偏成长/进攻。
- 若组合缺少 CORE/DEFENSIVE style，应进入后续 Regime Audit 观察，不自动调仓。

## BUY Ranking 双风险结构
- BUY Top10 平均 realized_risk_score：55.0820
- BUY Top10 平均 structural_risk_score：64.8338
- realized OFFENSIVE/HIGH_BETA 占比：40.00%
- structural OFFENSIVE/HIGH_BETA 占比：70.00%
- ranking 是否偏进攻：False

## 重点 ETF 双风险画像
| symbol | name | group | style_profile | realized_risk_score | realized_risk_profile | structural_risk_score | structural_risk_profile | data_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 512800 | 银行ETF | 金融地产 | SECTOR_DEFENSIVE | 16.5574 | DEFENSIVE | 44.1250 | CORE | ok |
| 515000 | 科技ETF | 科技成长 | GROWTH_THEME | 68.5519 | OFFENSIVE | 76.0750 | OFFENSIVE | ok |
| 512880 | 证券ETF | 金融地产 | SECTOR_CYCLICAL | 55.6011 | BALANCED | 75.5625 | HIGH_BETA | ok |
| 512010 | 医药ETF | 消费医药 | SECTOR_DEFENSIVE | 39.7541 | CORE | 49.8125 | BALANCED | ok |
| 588000 | 科创50ETF | 宽基 | CORE_MID_CAP | 77.2951 | HIGH_BETA | 67.6250 | OFFENSIVE | ok |
| 159915 | 创业板ETF | 宽基 | CORE_MID_CAP | 63.8251 | OFFENSIVE | 63.2500 | OFFENSIVE | ok |
| 510300 | 沪深300ETF | 宽基 | CORE_LARGE_CAP | 38.0328 | CORE | 42.7750 | CORE | ok |
| 510500 | 中证500ETF | 宽基 | CORE_MID_CAP | 52.1038 | BALANCED | 62.0250 | OFFENSIVE | ok |
| 510180 | 上证180ETF | 宽基 | CORE_LARGE_CAP | 32.2131 | CORE | 42.7750 | CORE | ok |

## 512880 差异解释
- 512880 证券 ETF 的人工 high_beta 来源是券商/证券类 ETF 的长期市场情绪弹性和 beta 属性。
- 本轮 structural_risk_profile 可保持 HIGH_BETA；realized_risk_profile 可根据近期行情为 BALANCED/OFFENSIVE 等。
- 这表示资产结构上高弹性，但近期实际波动风险暂处中等或未完全释放，属于合理差异。
- high_beta watch 应继续保留，仍不自动交易。

## 是否进入 Regime Audit Phase
- ready_for_regime_audit_phase：True
- 仅表示可以继续做 Regime Audit 研究，不表示接入执行层。

## 安全边界
- research_only=true。
- ready_for_execution=false。
- 未修改 BUY ranking / market_regime / paper_trade_engine / paper_trades / paper_positions。
- 不接券商 API，不真实下单，不读取真实账户，不暴露 token/密码。