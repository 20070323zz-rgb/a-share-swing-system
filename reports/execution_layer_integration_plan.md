# 执行层接入建议计划

本计划只提出下一步最小安全改动，不在本轮修改 paper_trade_engine 或自动买卖规则。

## A. 可以立即接入
- etf_type -> dashboard/sell_review 中展示研究性止损线与 max_holding_days
- etf_type -> paper_trade_engine 配置层候选：默认不强制，先生成 plan/review 字段
- dashboard 展示 market_state 建议仓位区间
- portfolio_exposure 展示组合集中度、缺少宽基、data_health caution，不强制交易

## B. 需要观察后接入
- market_state -> 目标仓位：新增 PAPER_USE_MARKET_STATE_POSITION = False，默认关闭
- portfolio_balance_bonus：只在 BUY ranking 分数接近时作为小权重辅助
- high_beta 自动降权：需要模拟样本验证后再接入
- 同 group 重复买入限制：先做提示，再做软限制

## C. 暂不建议接入
- 新闻情绪直接作为 BUY 主因子
- 复杂机器学习模型替代 mid_trend / short_swing
- 动态 max_holdings 自动切换
- 未经成本回测的部分减仓/连续 2 日直接卖出
- market_state 自动修改真实或模拟持仓

## 建议新增配置开关
- `PAPER_USE_MARKET_STATE_POSITION = False`
- `PAPER_USE_ETF_TYPE_RISK_PROFILE = False`
- `PAPER_USE_PORTFOLIO_BALANCE_BONUS = False`
- `PAPER_LIMIT_SAME_GROUP_BUYS = False`

## 最小安全路线
1. 先把 etf_type、market_state、portfolio_exposure 都保留在 dashboard 和 review 报告里。
2. 下一轮只增加配置开关和 plan 字段，不直接改变成交。
3. 等 weekly/monthly 复盘确认稳定后，再考虑让 sell_signal_review 使用 etf_type 止损和持仓期。
4. paper_trade_engine 的真实执行逻辑最后改，而且必须保留 dry-run 和人工复核。

## 安全边界
- 不接券商 API，不真实下单，不读取真实账户。
- 不保存密码/token。
- 不修改现有模拟仓和模拟交易流水。