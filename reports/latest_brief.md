# 每日最简摘要 2026-06-10

本摘要只用于模拟盘观察，不包含任何真实交易指令。

## 数据覆盖摘要
- 观察标的总数：78
- ETF 总数：76
- ETF 数据缺失数量：0
- 个股观察缺失数量：2
- observe_pool 总缺失数量：2
- 有效数据数量：76
- 数据过期数量：0
- trade_pool 覆盖率：100.00%
- observe_pool 覆盖率：86.67%
- 600519、300750 等 STOCK 属于个股观察，不属于 ETF 下载脚本处理范围。

## 数据健康摘要
- 正常：72
- 提醒：4
- 异常：0
- 缺失：2

## 双周期信号数量
- mid_trend：BUY 4 / WATCH 59 / SELL 0 / RISK 0
- short_swing：BUY 2 / WATCH 61 / SELL 0 / RISK 0

## 模拟盘摘要
- 当前总资产：9935.40 元
- 当前现金：7124.30 元
- 当前持仓数：3
- 今日是否有候选模拟买入：是，5 个候选仅供模拟观察
- 是否触发风险提醒：否

## 双周期共振
- mid BUY + short BUY：1 个；512800 银行ETF（金融地产）
- mid BUY + short WATCH：3 个；515880 证券公司ETF（金融地产）；515220 煤炭ETF（周期资源）；515000 科技ETF（科技成长）
- mid WATCH + short BUY：1 个；159940 金融ETF（金融地产）

## STRONG_RESONANCE 标的
- 512800 银行ETF（金融地产）：双周期强共振

## SHORT_TRIAL 标的
- 159940 金融ETF（金融地产）：短期试探，不动用中期资金

## RISK_ALERT 标的
- 无

## STRONG_RESONANCE 解释
### 512800 银行ETF
- 趋势理由：收盘价站上 MA20；收盘价站上 MA60；MA20 向上
- 动量理由：20 日涨幅 0.033333，5 日涨幅 0.029374。
- 相对强弱理由：relative_strength 0.079775。
- 成交量理由：volume_ratio 1.233012。
- group 支撑：金融地产 平均 composite_score 57.697052。
- 风险提示：未见主要阻断原因，但仍需按模拟盘仓位和止损规则观察。

## 综合 Top 5
- 512800 银行ETF（金融地产）：89.428571
- 515880 证券公司ETF（金融地产）：83.873016
- 515220 煤炭ETF（周期资源）：83.111111
- 515000 科技ETF（科技成长）：82.174603
- 510880 红利ETF（防御风格）：79.536508

## watch_score Top 5
- 512800 银行ETF（金融地产）：100
- 515880 证券公司ETF（金融地产）：100
- 515000 科技ETF（科技成长）：100
- 515220 煤炭ETF（周期资源）：100
- 510880 红利ETF（防御风格）：90

## group 强弱 Top 5
- 金融地产：7 个，平均 composite_score 57.697052，平均 relative_strength 0.015165
- 防御风格：5 个，平均 composite_score 47.566984，平均 relative_strength 0.003143
- 科技成长：12 个，平均 composite_score 41.518518，平均 relative_strength -0.01602
- 宽基：10 个，平均 composite_score 37.396825，平均 relative_strength -0.013397
- 周期资源：8 个，平均 composite_score 31.207936，平均 relative_strength -0.103214

## 数据缺失和异常提醒
- ETF 数据缺失数量：0
- 个股观察缺失数量：2
- observe_pool 总缺失数量：2
- 主策略加载阶段未发现额外数据缺失问题。
- 健康检查需关注：515880, 512760, 515050, 516780, 600519, 300750

## 今日建议
- 短期试探 / 等待中期确认 / 观察
- BUY ETF 排名请查看 reports/latest_buy_ranking.md；首次模拟买入计划请查看 reports/first_paper_buy_plan.md。

## 安全边界
- 不接券商 API，不下单，不读取账号密码，不自动交易。