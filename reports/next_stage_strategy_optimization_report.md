# 下一阶段策略优化研究总报告

本报告汇总本轮 research/simulation 层改造，不修改当前交易策略、仓位规则或模拟持仓。

## 0. 现状读取
- 当前模拟持仓：['515220', '512800', '515880']
- watchlist role 分布：{'trade_pool': 63, 'observe_pool': 15}
- ETF 类型分层 pool 分布：{'trade_pool': 79, 'observe_pool': 32, 'research_only': 3}
- data_health 摘要：检查标的总数：78；正常：72；提醒：4；异常：0；缺失：2
- 当前 paper_positions.csv / paper_trades.csv 未由本轮脚本写入或修改。

## 1. 本轮优化研究范围
- ETF 类型分层。
- 类型化持有周期离线研究。
- 候选退出规则离线研究。
- 新闻情绪风险过滤框架。
- 新闻数据源接入计划。
- 当前持仓专项复核。
- dashboard 只读研究展示。

## 2. ETF 类型分层结果
- 各类型数量：{'sector': 22, 'commodity_resource': 21, 'broad_index': 17, 'theme': 16, 'qdii': 15, 'unknown': 11, 'bond_cash': 10, 'hot_theme': 2}
- 详见 reports/etf_type_classification_report.md。

## 3. 持有周期研究结果
- 已生成 reports/holding_period_research_report.md 和 results.csv。
- 当前研究使用 proxy_buy_signal、short_swing_weakening、proxy_rank_decline_3d。
- 结论必须区分 evidence_supported / sample_limited / hypothesis_only。

## 4. 退出规则离线验证结果
- 已生成 reports/exit_rule_research_report.md。
- rank_score 历史目前用 proxy_score 代替，不建议直接上线。
- short_swing 转弱可优先进入 REVIEW/禁止加仓候选。

## 5. 新闻情绪框架
- 已生成 data/etf_theme_keywords.csv。
- 已生成 reports/news_sentiment_framework.md。
- 新闻情绪不进入 BUY 主分，只作为解释层/风险过滤器候选。

## 6. 新闻数据源接入计划
- 已生成 reports/news_data_source_plan.md。
- Tushare 权限需用户本地 token 实测。
- 东方财富、财联社、三大证券报、巨潮、AKShare 可分阶段低频接入或人工复核。

## 7. 当前持仓专项复核
- 已生成 reports/current_positions_strategy_fit_report.md。
- 515220 属于 commodity_resource，研究周期 10-45 天。
- 512800 属于 sector，研究周期 10-30 天。
- 515880 属于 sector，且 data_health caution，应禁止加仓并 REVIEW。

## 8. dashboard 展示改造
- dashboard 增加 ETF 类型、holding_profile、研究周期、持仓天数 vs 研究周期、sentiment_status 占位。
- dashboard 只读，不提供交易按钮。

## 9. 可进入下一阶段模拟观察
- ETF 类型分层展示。
- 持仓天数 vs 研究周期提醒。
- data_health caution 禁止加仓提示。
- short_swing 转弱进入 REVIEW 的观察项。

## 10. 必须继续回测
- 类型化止损。
- rank_score 连续下降退出。
- Top3 跌出 Top10 退出。
- 热度衰减代理规则。

## 11. 不建议上线
- 新闻情绪直接作为 BUY 主因子。
- 自动卖出/自动减仓。
- 未经验证的主题 ETF 短止损。
- 对当前 515220、512800、515880 自动改仓。

## 12. 风险与限制
- rank_score 历史序列不足，部分研究使用 proxy。
- 新闻数据尚未接入历史库，情绪框架只做设计。
- 扩池 ETF 历史较短，部分类型 sample_limited。

## 13. L2 边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存密码/token。
- 不修改 mid_trend / short_swing 核心策略。
- 不修改 paper_positions.csv / paper_trades.csv。
- 不把新闻情绪直接接入 BUY 主分。