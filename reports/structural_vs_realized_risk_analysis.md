# Structural vs Realized Risk 差异分析

本报告解释结构性风险与近期实现风险的差异。它不是交易信号，不修改 ranking 或模拟仓。

- 行数：183
- 差异方向分布：{'aligned_or_mild_gap': 126, 'structural_gt_realized': 55, 'realized_gt_structural': 2}

## 重点 ETF
| symbol | name | style_profile | structural_risk_score | structural_risk_profile | realized_risk_score | realized_risk_profile | score_gap | profile_gap | gap_direction | gap_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 512800 | 银行ETF | SECTOR_DEFENSIVE | 44.1250 | CORE | 16.5574 | DEFENSIVE | 27.5676 | 1 | structural_gt_realized | SECTOR_DEFENSIVE has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 515000 | 科技ETF | GROWTH_THEME | 76.0750 | OFFENSIVE | 68.5519 | OFFENSIVE | 7.5231 | 0 | aligned_or_mild_gap | Structural and realized risk are broadly aligned or only mildly different. |
| 512880 | 证券ETF | SECTOR_CYCLICAL | 75.5625 | HIGH_BETA | 55.6011 | BALANCED | 19.9614 | 2 | structural_gt_realized | SECTOR_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 512010 | 医药ETF | SECTOR_DEFENSIVE | 49.8125 | BALANCED | 39.7541 | CORE | 10.0584 | 1 | aligned_or_mild_gap | Structural and realized risk are broadly aligned or only mildly different. |
| 588000 | 科创50ETF | CORE_MID_CAP | 67.6250 | OFFENSIVE | 77.2951 | HIGH_BETA | -9.6701 | -1 | aligned_or_mild_gap | Structural and realized risk are broadly aligned or only mildly different. |
| 159915 | 创业板ETF | CORE_MID_CAP | 63.2500 | OFFENSIVE | 63.8251 | OFFENSIVE | -0.5751 | 0 | aligned_or_mild_gap | Structural and realized risk are broadly aligned or only mildly different. |
| 510300 | 沪深300ETF | CORE_LARGE_CAP | 42.7750 | CORE | 38.0328 | CORE | 4.7422 | 0 | aligned_or_mild_gap | Structural and realized risk are broadly aligned or only mildly different. |
| 510500 | 中证500ETF | CORE_MID_CAP | 62.0250 | OFFENSIVE | 52.1038 | BALANCED | 9.9212 | 1 | aligned_or_mild_gap | Structural and realized risk are broadly aligned or only mildly different. |
| 510180 | 上证180ETF | CORE_LARGE_CAP | 42.7750 | CORE | 32.2131 | CORE | 10.5619 | 0 | aligned_or_mild_gap | Structural and realized risk are broadly aligned or only mildly different. |

## 显著差异样本 Top 40
| symbol | name | style_profile | structural_risk_score | structural_risk_profile | realized_risk_score | realized_risk_profile | score_gap | gap_direction | gap_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 159302 | 港股高股息ETF银华 | QDII_OBSERVATION | 40.9750 | CORE | 16.9672 | DEFENSIVE | 24.0078 | structural_gt_realized | QDII_OBSERVATION has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159332 | 央企红利ETF富国 | DIVIDEND | 36.9625 | CORE | 23.8798 | DEFENSIVE | 13.0827 | structural_gt_realized | DIVIDEND has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159333 | 港股央企红利ETF万家 | QDII_OBSERVATION | 42.7250 | CORE | 21.6667 | DEFENSIVE | 21.0583 | structural_gt_realized | QDII_OBSERVATION has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159545 | 恒生红利低波ETF易方达 | QDII_OBSERVATION | 42.7250 | CORE | 24.6448 | DEFENSIVE | 18.0802 | structural_gt_realized | QDII_OBSERVATION has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159547 | 红利低波ETF华夏 | DIVIDEND | 33.0250 | CORE | 17.3224 | DEFENSIVE | 15.7026 | structural_gt_realized | DIVIDEND has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159549 | 红利低波ETF天弘 | DIVIDEND | 33.0250 | CORE | 17.0765 | DEFENSIVE | 15.9485 | structural_gt_realized | DIVIDEND has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159551 | 机器人ETF国泰 | HIGH_BETA_THEME | 79.5750 | OFFENSIVE | 65.4372 | OFFENSIVE | 14.1378 | structural_gt_realized | HIGH_BETA_THEME has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159663 | 机床ETF华夏 | HIGH_BETA_THEME | 79.1375 | OFFENSIVE | 65.6011 | OFFENSIVE | 13.5364 | structural_gt_realized | HIGH_BETA_THEME has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159697 | 石油ETF鹏华 | COMMODITY_CYCLICAL | 63.8375 | OFFENSIVE | 37.4863 | CORE | 26.3512 | structural_gt_realized | COMMODITY_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159699 | 恒生消费ETF广发 | QDII_OBSERVATION | 54.6625 | BALANCED | 30.1093 | DEFENSIVE | 24.5532 | structural_gt_realized | QDII_OBSERVATION has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159703 | 新材料ETF天弘 | COMMODITY_CYCLICAL | 71.6250 | OFFENSIVE | 57.8962 | OFFENSIVE | 13.7288 | structural_gt_realized | COMMODITY_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159726 | 港股通高股息ETF华夏 | QDII_OBSERVATION | 43.1625 | CORE | 17.8689 | DEFENSIVE | 25.2936 | structural_gt_realized | QDII_OBSERVATION has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159735 | 港股消费ETF银华 | QDII_OBSERVATION | 55.8875 | BALANCED | 34.0437 | CORE | 21.8438 | structural_gt_realized | QDII_OBSERVATION has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159736 | 食品ETF | SECTOR_DEFENSIVE | 49.8125 | BALANCED | 33.0874 | CORE | 16.7251 | structural_gt_realized | SECTOR_DEFENSIVE has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159745 | 建材ETF国泰 | COMMODITY_CYCLICAL | 67.6000 | OFFENSIVE | 39.9454 | CORE | 27.6546 | structural_gt_realized | COMMODITY_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159763 | 新材料ETF建信 | COMMODITY_CYCLICAL | 71.6250 | OFFENSIVE | 57.4317 | OFFENSIVE | 14.1933 | structural_gt_realized | COMMODITY_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159770 | 机器人ETF | HIGH_BETA_THEME | 79.5750 | OFFENSIVE | 65.0000 | OFFENSIVE | 14.5750 | structural_gt_realized | HIGH_BETA_THEME has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159787 | 建材ETF易方达 | COMMODITY_CYCLICAL | 65.5875 | OFFENSIVE | 38.4973 | CORE | 27.0902 | structural_gt_realized | COMMODITY_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159825 | 农业ETF | COMMODITY_CYCLICAL | 66.1375 | OFFENSIVE | 44.3169 | BALANCED | 21.8206 | structural_gt_realized | COMMODITY_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159865 | 养殖ETF | COMMODITY_CYCLICAL | 64.3875 | OFFENSIVE | 43.1694 | CORE | 21.2181 | structural_gt_realized | COMMODITY_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159870 | 化工ETF | COMMODITY_CYCLICAL | 70.4250 | OFFENSIVE | 56.4208 | BALANCED | 14.0042 | structural_gt_realized | COMMODITY_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159888 | 智能汽车ETF华夏 | GROWTH_THEME | 70.7250 | OFFENSIVE | 57.5956 | OFFENSIVE | 13.1294 | structural_gt_realized | GROWTH_THEME has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159889 | 智能汽车ETF国泰 | GROWTH_THEME | 70.7250 | OFFENSIVE | 55.4918 | BALANCED | 15.2332 | structural_gt_realized | GROWTH_THEME has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159920 | 恒生ETF | QDII_OBSERVATION | 56.6750 | BALANCED | 30.2732 | DEFENSIVE | 26.4018 | structural_gt_realized | QDII_OBSERVATION has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159928 | 消费ETF | SECTOR_DEFENSIVE | 51.0375 | BALANCED | 36.4754 | CORE | 14.5621 | structural_gt_realized | SECTOR_DEFENSIVE has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159929 | 医药ETF | SECTOR_DEFENSIVE | 51.5625 | BALANCED | 39.3443 | CORE | 12.2182 | structural_gt_realized | SECTOR_DEFENSIVE has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159930 | 能源ETF | COMMODITY_CYCLICAL | 63.1625 | OFFENSIVE | 41.0383 | CORE | 22.1242 | structural_gt_realized | COMMODITY_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159940 | 金融ETF | SECTOR_CYCLICAL | 59.6125 | BALANCED | 31.4481 | CORE | 28.1644 | structural_gt_realized | SECTOR_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 159996 | 家电ETF | SECTOR_DEFENSIVE | 49.8125 | BALANCED | 30.3552 | DEFENSIVE | 19.4573 | structural_gt_realized | SECTOR_DEFENSIVE has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 510060 | 央企ETF | DIVIDEND | 34.7750 | CORE | 19.8361 | DEFENSIVE | 14.9389 | structural_gt_realized | DIVIDEND has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 510230 | 金融ETF | CORE_MID_CAP | 42.2625 | CORE | 25.9563 | DEFENSIVE | 16.3062 | structural_gt_realized | CORE_MID_CAP has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 510270 | 国企ETF | DIVIDEND | 38.7125 | CORE | 24.5628 | DEFENSIVE | 14.1497 | structural_gt_realized | DIVIDEND has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 510410 | 资源ETF | COMMODITY_CYCLICAL | 73.4875 | OFFENSIVE | 56.5574 | OFFENSIVE | 16.9301 | structural_gt_realized | COMMODITY_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 510880 | 红利ETF | DIVIDEND | 35.2125 | CORE | 22.6230 | DEFENSIVE | 12.5895 | structural_gt_realized | DIVIDEND has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 512070 | 非银ETF | SECTOR_CYCLICAL | 76.7875 | HIGH_BETA | 56.5301 | BALANCED | 20.2574 | structural_gt_realized | SECTOR_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 512170 | 医疗ETF | SECTOR_DEFENSIVE | 52.7875 | BALANCED | 39.5355 | CORE | 13.2520 | structural_gt_realized | SECTOR_DEFENSIVE has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 512200 | 房地产ETF | SECTOR_CYCLICAL | 66.3500 | OFFENSIVE | 50.4372 | BALANCED | 15.9128 | structural_gt_realized | SECTOR_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 512800 | 银行ETF | SECTOR_DEFENSIVE | 44.1250 | CORE | 16.5574 | DEFENSIVE | 27.5676 | structural_gt_realized | SECTOR_DEFENSIVE has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 512880 | 证券ETF | SECTOR_CYCLICAL | 75.5625 | HIGH_BETA | 55.6011 | BALANCED | 19.9614 | structural_gt_realized | SECTOR_CYCLICAL has higher long-term/structural risk character than recent realized market risk; not a trading signal. |
| 512890 | 红利低波ETF | DIVIDEND | 33.0250 | CORE | 15.7104 | DEFENSIVE | 17.3146 | structural_gt_realized | DIVIDEND has higher long-term/structural risk character than recent realized market risk; not a trading signal. |

## 512880 解释
- 512880 证券 ETF 属于金融高 beta 情绪资产，结构性风险可为 HIGH_BETA。
- 如果近期 realized_risk_profile 不是 HIGH_BETA，表示近期行情中的实际波动/回撤/beta 暂时收敛。
- 这不是冲突，也不应为了消除差异反向修改 realized risk。
- high_beta watch 应继续保留，但仍为观察层，不自动减仓或卖出。