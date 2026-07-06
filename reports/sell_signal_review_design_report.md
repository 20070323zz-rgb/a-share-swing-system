# 卖出复核系统设计报告

- 生成时间：2026-07-04 00:03:54
- 权限等级：L2 联网数据权限。
- 本设计只服务模拟盘复核，不生成真实交易指令。

## 1. 为什么不能单日评分下降就卖
- BUY ranking 是横截面评分，单日下降可能来自市场风格切换、成交量短噪声或新候选变强。
- ETF 买入后 1-2 个交易日容易出现正常回撤，直接 SELL 会放大噪声交易。
- 因此需要结合 mid_trend、short_swing、止损线、data_health、ETF 类型和持仓天数共同判断。

## 2. 状态定义
- HOLD：中期和短期信号仍健康，未触发止损和数据异常。
- WATCH：rank_score 单日明显下降，但趋势和止损未破坏，继续持有观察。
- REVIEW：短周期转弱、rank 连续下降、data_health caution 或高波动主题大幅降分，需要人工复核。
- REDUCE：连续下降叠加短周期转弱，或主题/高 beta 动量明显衰减，仅作为减仓候选。
- SELL：跌破止损、中期趋势转 SELL、短周期 SELL 且 rank 跌破阈值、严重数据异常或持有期过长且信号未恢复，仅作为卖出候选。

## 3. 买入后保护期
- 买入后 2 个交易日为观察保护期。
- rank_score 单日大跌：WATCH。
- rank_score 大跌 + short_swing 转 WATCH：REVIEW。
- rank_score 大跌 + short_swing SELL 或跌破止损：SELL 候选。
- 除非硬风控触发，否则不因单日评分下降直接 SELL。

## 4. ETF 类型敏感度
- broad_index：宽基，卖出不敏感；连续转弱再 REVIEW。
- sector：行业，中等敏感；评分下降 + short_swing 转弱进入 REVIEW。
- commodity_resource：周期资源，中高敏感；关注价格和政策周期。
- theme / high_beta：主题或高 beta，更敏感；连续下降 + 短周期转弱可进入 REDUCE/SELL 候选。
- bond_cash：低波动，单独处理。
- qdii：先 REVIEW，需要溢价/汇率/海外交易日检查。

## 5. 当前三只持仓复核结果
| ETF | 名称 | 类型 | 状态 | 主要原因 |
| --- | --- | --- | --- | --- |
| 512800 | 银行ETF | sector | REVIEW | short_swing_buy_to_watch; floating_loss_over_3_5pct; rank_decline_2d |
| 515000 | 科技ETF | unknown | REVIEW | rank_score_single_day_drop; rank_score_large_drop; rank_score_drop_pct_over_12; short_swing_buy_to_watch |
| 512880 | 证券ETF | high_beta | HOLD |  |

## 6. 是否修改交易记录
- paper_trades.csv 当前行数：7。
- 本轮未新增模拟交易。
- 本轮未修改 paper_positions.csv。

## 7. 是否保持 L2 边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存密码/token。
- 不自动卖出、减仓或修改持仓。
- 不修改正式仓位规则。

## 8. 下一步
- 需要对 WATCH/REVIEW/REDUCE/SELL 候选规则做离线回测。
- 尤其要验证 rank_score 连续下降、short_swing 转弱、类型化止损是否能改善回撤而不过度交易。