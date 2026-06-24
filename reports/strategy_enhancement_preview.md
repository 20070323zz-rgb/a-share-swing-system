# 策略增强预览报告 2026-06-24 23:04:53

本报告只计算 adjusted_rank_score_preview，不改变 BUY ranking、不改变 paper_trade_engine 真实排序、不写模拟交易。

## 摘要
- market_state：market_strong / market_score=70.92
- portfolio_exposure_status：CAUTION
- Top 3 是否变化：否
- adjusted_rank_score_execution_enabled：false
- PAPER_USE_MARKET_STATE_POSITION：false

## Original Top 3
1. 512880 证券ETF：rank=1，score=91.8274
2. 159819 人工智能ETF：rank=2，score=88.4364
3. 515070 AIETF：rank=3，score=88.3806

## Adjusted Preview Top 3
1. 512880 证券ETF：rank=1，score=87.8274
2. 159819 人工智能ETF：rank=2，score=86.4364
3. 515070 AIETF：rank=3，score=86.3806

## Top 3 差异
- 本轮差异：原始 Top 3 与增强预览 Top 3 一致。
- 最大分数变化：515050 5GETF，delta=-5，原因：当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3

## 组合平衡 bonus 命中
- 510050 上证50ETF：broad_index_balance_bonus=3；组合缺少宽基，broad_index_balance_bonus +3
- 510180 上证180ETF：broad_index_balance_bonus=3；组合缺少宽基，broad_index_balance_bonus +3
- defensive_balance_bonus：无命中。

## 降权命中
- 512880 证券ETF：same_group_concentration_penalty=-2；当前持仓已有 金融地产 暴露，same_group_concentration_penalty -2; 当前已有 high_beta 暴露，high_beta_penalty -2
- 159819 人工智能ETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 515070 AIETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 512070 非银ETF：same_group_concentration_penalty=-2；当前持仓已有 金融地产 暴露，same_group_concentration_penalty -2; 当前已有 high_beta 暴露，high_beta_penalty -2
- 515000 科技ETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 515050 5GETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3
- 512880 证券ETF：high_beta_penalty=-2；当前持仓已有 金融地产 暴露，same_group_concentration_penalty -2; 当前已有 high_beta 暴露，high_beta_penalty -2
- 512070 非银ETF：high_beta_penalty=-2；当前持仓已有 金融地产 暴露，same_group_concentration_penalty -2; 当前已有 high_beta 暴露，high_beta_penalty -2
- 515050 5GETF：data_health_penalty=-3；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3
- 516780 稀土ETF：data_health_penalty=-3；data_health=提醒，data_health_penalty -3

## 全部预览明细
| original_rank | adjusted_rank | symbol | name | etf_type | group | original_score | adjusted_score | delta | bonus/penalty reason | execution_status |
| ---: | ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | 1 | 512880 | 证券ETF | high_beta | 金融地产 | 91.8274 | 87.8274 | -4 | 当前持仓已有 金融地产 暴露，same_group_concentration_penalty -2; 当前已有 high_beta 暴露，high_beta_penalty -2 | preview_only_not_executed |
| 2 | 2 | 159819 | 人工智能ETF | theme | 科技成长 | 88.4364 | 86.4364 | -2 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2 | preview_only_not_executed |
| 3 | 3 | 515070 | AIETF | theme | 科技成长 | 88.3806 | 86.3806 | -2 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2 | preview_only_not_executed |
| 4 | 4 | 512070 | 非银ETF | high_beta | 金融地产 | 87.6528 | 83.6528 | -4 | 当前持仓已有 金融地产 暴露，same_group_concentration_penalty -2; 当前已有 high_beta 暴露，high_beta_penalty -2 | preview_only_not_executed |
| 5 | 5 | 515000 | 科技ETF | sector | 科技成长 | 80.3898 | 78.3898 | -2 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2 | preview_only_not_executed |
| 8 | 6 | 510050 | 上证50ETF | broad_index | 宽基 | 72.8343 | 75.8343 | 3 | 组合缺少宽基，broad_index_balance_bonus +3 | preview_only_not_executed |
| 7 | 7 | 512010 | 医药ETF | sector | 消费医药 | 73.645 | 73.645 | 0 | 未触发 B1 预览加减分 | preview_only_not_executed |
| 9 | 8 | 510180 | 上证180ETF | broad_index | 宽基 | 70.0769 | 73.0769 | 3 | 组合缺少宽基，broad_index_balance_bonus +3 | preview_only_not_executed |
| 6 | 9 | 515050 | 5GETF | theme | 科技成长 | 74.0456 | 69.0456 | -5 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3 | preview_only_not_executed |
| 10 | 10 | 516780 | 稀土ETF | commodity_resource | 周期资源 | 68.4123 | 65.4123 | -3 | data_health=提醒，data_health_penalty -3 | preview_only_not_executed |
| 11 | 11 | 159929 | 医药ETF | sector | 消费医药 | 59.8614 | 59.8614 | 0 | 未触发 B1 预览加减分 | preview_only_not_executed |

## 安全边界
- 本轮只做 preview，不改变真实模拟盘成交结果。
- 不修改 paper_trade_engine 核心执行规则。
- 不启用 market_state 仓位控制。
- 不启用 adjusted_rank_score 作为真实买入排序。
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。
