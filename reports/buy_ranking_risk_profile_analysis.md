# BUY Ranking 风险画像分析

本报告只分析当前 BUY Top 10 的风险结构，不修改 ranking。

- Top 10 数量：10
- Top10 avg realized_risk_score：55.0820
- Top10 avg structural_risk_score：64.8338
- realized risk_profile 分布：{'CORE': 4, 'BALANCED': 2, 'HIGH_BETA': 2, 'OFFENSIVE': 2}
- structural risk_profile 分布：{'OFFENSIVE': 6, 'BALANCED': 3, 'HIGH_BETA': 1}
- style_profile 分布：{'SECTOR_DEFENSIVE': 3, 'COMMODITY_CYCLICAL': 2, 'CORE_MID_CAP': 2, 'GROWTH_THEME': 2, 'SECTOR_CYCLICAL': 1}
- realized OFFENSIVE/HIGH_BETA 占比：40.00%
- structural OFFENSIVE/HIGH_BETA 占比：70.00%
- CORE/DEFENSIVE 占比：40.00%
- 是否天然偏进攻：False

| rank | symbol | name | group | rank_score | realized_risk_score | realized_risk_profile | structural_risk_score | structural_risk_profile | style_profile | data_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 512010 | 医药ETF | 消费医药 | 94.3042 | 39.7541 | CORE | 49.8125 | BALANCED | SECTOR_DEFENSIVE | ok |
| 2 | 512880 | 证券ETF | 金融地产 | 93.9395 | 55.6011 | BALANCED | 75.5625 | HIGH_BETA | SECTOR_CYCLICAL | ok |
| 3 | 159929 | 医药ETF | 消费医药 | 89.3657 | 39.3443 | CORE | 51.5625 | BALANCED | SECTOR_DEFENSIVE | ok |
| 4 | 588080 | 科创创业50ETF | 宽基 | 76.5887 | 76.6667 | HIGH_BETA | 67.6250 | OFFENSIVE | CORE_MID_CAP | ok |
| 5 | 588000 | 科创50ETF | 宽基 | 76.5586 | 77.2951 | HIGH_BETA | 67.6250 | OFFENSIVE | CORE_MID_CAP | ok |
| 6 | 512170 | 医疗ETF | 消费医药 | 76.2914 | 39.5355 | CORE | 52.7875 | BALANCED | SECTOR_DEFENSIVE | ok |
| 7 | 159865 | 养殖ETF | 周期资源 | 74.8890 | 43.1694 | CORE | 64.3875 | OFFENSIVE | COMMODITY_CYCLICAL | ok |
| 8 | 515000 | 科技ETF | 科技成长 | 71.3463 | 68.5519 | OFFENSIVE | 76.0750 | OFFENSIVE | GROWTH_THEME | ok |
| 9 | 159825 | 农业ETF | 周期资源 | 68.3897 | 44.3169 | BALANCED | 66.1375 | OFFENSIVE | COMMODITY_CYCLICAL | ok |
| 10 | 159869 | 游戏ETF | 科技成长 | 67.6638 | 66.5847 | OFFENSIVE | 76.7625 | OFFENSIVE | GROWTH_THEME | ok |

结论：如果 Top BUY 同时集中在 realized 与 structural OFFENSIVE/HIGH_BETA，说明 ranking 可能存在风险偏好偏置；本报告只提示后续 Regime Audit，不直接改变本期执行层。