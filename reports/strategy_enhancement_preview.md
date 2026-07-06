# 策略增强预览报告 2026-07-04 00:00:54

本报告只计算 adjusted_rank_score_preview，不改变 BUY ranking、不改变 paper_trade_engine 真实排序、不写模拟交易。

## 摘要
- market_state：market_neutral / market_score=61.67
- portfolio_exposure_status：CAUTION
- Top 3 是否变化：是
- adjusted_rank_score_execution_enabled：false
- PAPER_USE_MARKET_STATE_POSITION：false

## Original Top 3
1. 512010 医药ETF：rank=1，score=95.1375
2. 512880 证券ETF：rank=2，score=94.493
3. 159929 医药ETF：rank=3，score=79.4343

## Adjusted Preview Top 3
1. 512010 医药ETF：rank=1，score=95.1375
2. 512880 证券ETF：rank=2，score=90.493
3. 588000 科创50ETF：rank=3，score=79.6456

## Top 3 差异
- 本轮差异：原始 Top 3 与增强预览 Top 3 不一致。
- 最大分数变化：512760 芯片ETF，delta=-5，原因：当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3

## 组合平衡 bonus 命中
- 588000 科创50ETF：broad_index_balance_bonus=3；组合缺少宽基，broad_index_balance_bonus +3
- 510180 上证180ETF：broad_index_balance_bonus=3；组合缺少宽基，broad_index_balance_bonus +3
- defensive_balance_bonus：无命中。

## 降权命中
- 512880 证券ETF：same_group_concentration_penalty=-2；当前持仓已有 金融地产 暴露，same_group_concentration_penalty -2; 当前已有 high_beta 暴露，high_beta_penalty -2
- 159995 芯片ETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 512760 芯片ETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3
- 515000 科技ETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 159869 游戏ETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 515070 AIETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 159819 人工智能ETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 512880 证券ETF：high_beta_penalty=-2；当前持仓已有 金融地产 暴露，same_group_concentration_penalty -2; 当前已有 high_beta 暴露，high_beta_penalty -2
- 512760 芯片ETF：data_health_penalty=-3；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3

## 全部预览明细
| original_rank | adjusted_rank | symbol | name | etf_type | group | original_score | adjusted_score | delta | bonus/penalty reason | execution_status |
| ---: | ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | 1 | 512010 | 医药ETF | sector | 消费医药 | 95.1375 | 95.1375 | 0 | 未触发 B1 预览加减分 | preview_only_not_executed |
| 2 | 2 | 512880 | 证券ETF | high_beta | 金融地产 | 94.493 | 90.493 | -4 | 当前持仓已有 金融地产 暴露，same_group_concentration_penalty -2; 当前已有 high_beta 暴露，high_beta_penalty -2 | preview_only_not_executed |
| 5 | 3 | 588000 | 科创50ETF | broad_index | 宽基 | 76.6456 | 79.6456 | 3 | 组合缺少宽基，broad_index_balance_bonus +3 | preview_only_not_executed |
| 3 | 4 | 159929 | 医药ETF | sector | 消费医药 | 79.4343 | 79.4343 | 0 | 未触发 B1 预览加减分 | preview_only_not_executed |
| 4 | 5 | 512170 | 医疗ETF | sector | 消费医药 | 78.1092 | 78.1092 | 0 | 未触发 B1 预览加减分 | preview_only_not_executed |
| 7 | 6 | 512660 | 军工ETF | commodity_resource | 新能源制造 | 74.2589 | 74.2589 | 0 | 未触发 B1 预览加减分 | preview_only_not_executed |
| 6 | 7 | 159995 | 芯片ETF | theme | 科技成长 | 75.3906 | 73.3906 | -2 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2 | preview_only_not_executed |
| 12 | 8 | 510180 | 上证180ETF | broad_index | 宽基 | 68.8625 | 71.8625 | 3 | 组合缺少宽基，broad_index_balance_bonus +3 | preview_only_not_executed |
| 10 | 9 | 159865 | 养殖ETF | commodity_resource | 周期资源 | 69.6699 | 69.6699 | 0 | 未触发 B1 预览加减分 | preview_only_not_executed |
| 8 | 10 | 512760 | 芯片ETF | theme | 科技成长 | 73.4873 | 68.4873 | -5 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3 | preview_only_not_executed |
| 9 | 11 | 515000 | 科技ETF | sector | 科技成长 | 70.4155 | 68.4155 | -2 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2 | preview_only_not_executed |
| 11 | 12 | 159869 | 游戏ETF | theme | 科技成长 | 69.3119 | 67.3119 | -2 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2 | preview_only_not_executed |
| 13 | 13 | 515070 | AIETF | theme | 科技成长 | 66.9322 | 64.9322 | -2 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2 | preview_only_not_executed |
| 14 | 14 | 159819 | 人工智能ETF | theme | 科技成长 | 66.544 | 64.544 | -2 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2 | preview_only_not_executed |
| 15 | 15 | 159996 | 家电ETF | sector | 消费医药 | 63.7697 | 63.7697 | 0 | 未触发 B1 预览加减分 | preview_only_not_executed |
| 16 | 16 | 159825 | 农业ETF | commodity_resource | 周期资源 | 62.9751 | 62.9751 | 0 | 未触发 B1 预览加减分 | preview_only_not_executed |
| 17 | 17 | 516110 | 汽车ETF | sector | 消费医药 | 54.4656 | 54.4656 | 0 | 未触发 B1 预览加减分 | preview_only_not_executed |

## 安全边界
- 本轮只做 preview，不改变真实模拟盘成交结果。
- 不修改 paper_trade_engine 核心执行规则。
- 不启用 market_state 仓位控制。
- 不启用 adjusted_rank_score 作为真实买入排序。
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。
