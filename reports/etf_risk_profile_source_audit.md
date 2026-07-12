# ETF Risk Profile 来源审计

本审计只读取本地文件，不修改 watchlist 或交易规则。

## 结论
- 期望 data/watchlist.csv 是否存在：False
- 实际 watchlist：watchlist.csv
- watchlist group：['QDII观察', '个股观察', '债券货币观察', '周期资源', '宽基', '新能源制造', '消费医药', '科技成长', '金融地产', '防御风格']
- watchlist type：['ETF', 'STOCK']
- etf_type 分布：{'unknown': 75, 'broad_index': 22, 'commodity_resource': 21, 'sector': 19, 'theme': 18, 'qdii': 15, 'bond_cash': 12, 'high_beta': 3}
- risk_profile 分布：{'manual_review': 75, 'core_beta': 22, 'commodity_cycle': 21, 'sector_beta': 19, 'theme_beta': 18, 'cross_border': 15, 'low_volatility': 12, 'high_beta': 3}
- unknown 分类数量：75
- profile UNKNOWN style 数量：0

## 现有定义
- high_beta：Existing high_beta watcher flags names/types containing high_beta, 证券, 券商. Risk Profile additionally uses beta_60d>=1.20 or annualized volatility_60d>=35%.
- broad_base：Existing broad_base preview uses curated traditional/quasi broad codes and broad-index names. Risk Profile splits is_broad_base and is_quasi_broad_base with code/name/group rules.

## 可用输入
- 人工标签字段：['watchlist.group', 'watchlist.role', 'classification.etf_type', 'classification.risk_profile', 'classification.classification_reason']
- 历史行情字段：['return_20d/60d/120d', 'volatility_20d/60d/120d', 'beta_60d/120d', 'max_drawdown_60d/120d', 'downside_volatility_60d', 'up_capture_60d', 'down_capture_60d']
- 综合可用输入：['name', 'group', 'type', 'etf_type', 'pool', 'local daily OHLCV/amount', 'existing high_beta/broad_base/portfolio exposure reports']

## 关键词代码命中 Top 20
| keyword | file_count | hit_count | example_files |
| --- | --- | --- | --- |
| type | 71 | 1410 | src/trade_review.py, src/high_beta_risk_watch.py, src/shadow_observation_weekly.py, src/ranking_model_v2_backtest.py, src/factor_analysis.py |
| group | 54 | 831 | src/high_beta_risk_watch.py, src/shadow_observation_weekly.py, src/ranking_model_v2_backtest.py, src/factor_analysis.py, src/labels.py |
| high_beta | 33 | 593 | src/high_beta_risk_watch.py, src/shadow_observation_weekly.py, src/ranking_model_v2_backtest.py, src/chatgpt_weekly_packet.py, src/phase4c_alpha_common.py |
| theme | 25 | 109 | src/shadow_observation_weekly.py, src/ranking_model_v2_backtest.py, src/chatgpt_weekly_packet.py, src/phase4c_alpha_common.py, src/etf_classifier.py |
| defensive | 14 | 72 | src/regime_aware_model_research.py, src/phase4c_alpha_common.py, src/etf_volatility_profile.py, src/strategy_preview_tracking.py, src/etf_style_profile.py |
| sector | 15 | 68 | src/ranking_model_v2_backtest.py, src/etf_classifier.py, src/universe_quality_review.py, src/etf_volatility_profile.py, src/etf_style_profile.py |
| bond | 15 | 64 | src/ranking_model_v2_backtest.py, src/phase4c_alpha_common.py, src/etf_classifier.py, src/etf_volatility_profile.py, src/etf_style_profile.py |
| growth | 8 | 44 | src/chatgpt_weekly_packet.py, src/phase4c_alpha_common.py, src/etf_style_profile.py, src/broad_base_balance_preview.py, src/etf_risk_profile.py |
| is_broad_base | 3 | 16 | src/etf_style_profile.py, src/broad_base_balance_preview.py, src/etf_risk_profile.py |
| is_quasi_broad_base | 3 | 9 | src/etf_style_profile.py, src/broad_base_balance_preview.py, src/etf_risk_profile.py |
| dividend | 3 | 9 | src/etf_style_profile.py, src/exit_rule_candidates.py, src/etf_risk_profile.py |
| low_vol | 4 | 9 | src/etf_classifier.py, src/etf_style_profile.py, src/strategy_enhancement_preview.py, src/etf_risk_profile.py |

## 安全边界
- watchlist_modified=false。
- execution_allowed=false。