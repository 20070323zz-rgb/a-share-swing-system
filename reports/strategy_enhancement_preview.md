# 策略增强预览报告 2026-07-10 16:28:07

本报告只计算 adjusted_rank_score_preview，不改变 BUY ranking、不改变 paper_trade_engine 真实排序、不写模拟交易。

## 摘要
- market_state：market_neutral / market_score=62.22
- portfolio_exposure_status：CAUTION
- Top 3 是否变化：否
- adjusted_rank_score_execution_enabled：false
- PAPER_USE_MARKET_STATE_POSITION：false

## Original Top 3
1. 516510 云计算ETF：rank=1，score=88.861
2. 159929 医药ETF：rank=2，score=86.2162
3. 515000 科技ETF：rank=3，score=77.0373

## Adjusted Preview Top 3
1. 516510 云计算ETF：rank=1，score=86.861
2. 159929 医药ETF：rank=2，score=84.2162
3. 515000 科技ETF：rank=3，score=75.0373

## Top 3 差异
- 本轮差异：原始 Top 3 与增强预览 Top 3 一致。
- 最大分数变化：512760 芯片ETF，delta=-5，原因：当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3

## 组合平衡 bonus 命中
- 510500 中证500ETF：broad_index_balance_bonus=3；组合缺少宽基，broad_index_balance_bonus +3
- defensive_balance_bonus：无命中。

## 降权命中
- 516510 云计算ETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 159929 医药ETF：same_group_concentration_penalty=-2；当前持仓已有 消费医药 暴露，same_group_concentration_penalty -2
- 515000 科技ETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- 512760 芯片ETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3
- 159869 游戏ETF：same_group_concentration_penalty=-2；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2
- high_beta_penalty：无命中。
- 512760 芯片ETF：data_health_penalty=-3；当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3

## 全部预览明细
| original_rank | adjusted_rank | symbol | name | etf_type | group | original_score | adjusted_score | delta | bonus/penalty reason | execution_status |
| ---: | ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | 1 | 516510 | 云计算ETF | theme | 科技成长 | 88.861 | 86.861 | -2 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2 | preview_only_not_executed |
| 2 | 2 | 159929 | 医药ETF | sector | 消费医药 | 86.2162 | 84.2162 | -2 | 当前持仓已有 消费医药 暴露，same_group_concentration_penalty -2 | preview_only_not_executed |
| 3 | 3 | 515000 | 科技ETF | sector | 科技成长 | 77.0373 | 75.0373 | -2 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2 | preview_only_not_executed |
| 6 | 4 | 510500 | 中证500ETF | broad_index | 宽基 | 71.5314 | 74.5314 | 3 | 组合缺少宽基，broad_index_balance_bonus +3 | preview_only_not_executed |
| 4 | 5 | 512760 | 芯片ETF | theme | 科技成长 | 75.6699 | 70.6699 | -5 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2; data_health=提醒，data_health_penalty -3 | preview_only_not_executed |
| 5 | 6 | 159869 | 游戏ETF | theme | 科技成长 | 71.7119 | 69.7119 | -2 | 当前持仓已有 科技成长 暴露，same_group_concentration_penalty -2 | preview_only_not_executed |
| 7 | 7 | 159865 | 养殖ETF | commodity_resource | 周期资源 | 67.0231 | 67.0231 | 0 | 未触发 B1 预览加减分 | preview_only_not_executed |

## 安全边界
- 本轮只做 preview，不改变真实模拟盘成交结果。
- 不修改 paper_trade_engine 核心执行规则。
- 不启用 market_state 仓位控制。
- 不启用 adjusted_rank_score 作为真实买入排序。
- 不接券商 API，不真实下单，不读取真实账户，不保存密码/token。
