# 规则验证版模拟交易计划 2026-07-10

本报告只针对本地模拟盘，不接券商 API，不真实下单。
模拟执行日期为 2026-07-10；价格使用本地最新行情数据日 2026-07-09 的 close proxy。

## 引擎状态
- run_date：2026-07-10
- price_data_date：2026-07-09
- PAPER_MODE：rule_validation
- PAPER_AUTO_EXECUTE：True
- REAL_TRADE_ENABLED：False
- BROKER_API_ENABLED：False
- status：executed
- dry_run：False
- buy_count：2
- sell_count：1
- skipped_duplicate：False
- skip_reason：
- PAPER_USE_MARKET_STATE_POSITION：False

## 账户摘要
- 执行前现金：7608.44
- 执行前仓位：24.43%
- 执行后现金：7040.47
- 执行后仓位：29.96%

## Phase 2C 轻量接入说明
- etf_type / max_holding_days / stop_loss_pct 已进入计划解释和风险展示。
- market_state 只展示建议仓位区间，不改变买入金额或目标仓位。
- portfolio_exposure 只生成组合平衡提示和集中度提示，不阻断交易。
- 本轮不改变 max_holdings，不改变 paper_trade_engine 核心成交逻辑。

## 交易计划与结果
| run_date | price_data_date | symbol | name | action | status | raw_close | quantity | gross_amount | market_state | current/suggested position | etf_type | max_days | stop_loss_pct | exposure_status | balance_suggestion | concentration_warning | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |
| 2026-07-10 | 2026-07-09 | 512800 | 银行ETF | SELL | executed | 0.761 | 1100 | 836.85 | market_neutral / 49.34 | 24.43% / 20.00%-40.00% (aligned) | sector | 30 | 6.00% | CAUTION | 当前组合缺少宽基，本候选不能改善宽基缺口。 | 当前组合已有金融/周期/高 beta 暴露，新增同类 ETF 可能加剧集中度。 | max_holding_days reached without signal recovery |
| 2026-07-10 | 2026-07-09 | 515000 | 科技ETF | SELL | skipped_no_sell_signal | 1.622 | 1000 | 1621.51 | market_neutral / 49.34 | 24.43% / 20.00%-40.00% (aligned) | unknown | 0 | 0.00% | CAUTION | 当前组合缺少宽基，本候选不能改善宽基缺口。 |  | sell rules not triggered |
| 2026-07-10 | 2026-07-09 | 516510 | 云计算ETF | BUY | executed | 1.805 | 700 | 1263.88 | market_neutral / 49.34 | 24.43% / 20.00%-40.00% (aligned) | theme | 20 | 5.00% | CAUTION | 当前组合缺少宽基，本候选不能改善宽基缺口。 |  | paper_rule_validation; rank=1; rank_score=88.861036; mid_trend=BUY; short_swing=BUY; amount=1263.88 |
| 2026-07-10 | 2026-07-09 | 159929 | 医药ETF | BUY | executed | 1.259 | 100 | 125.94 | market_neutral / 49.34 | 24.43% / 20.00%-40.00% (aligned) | sector | 30 | 6.00% | CAUTION | 当前组合缺少宽基，本候选不能改善宽基缺口。 |  | paper_rule_validation; rank=2; rank_score=86.216237; mid_trend=BUY; short_swing=BUY; amount=125.94 |
| 2026-07-10 | 2026-07-09 | 515000 | 科技ETF | BUY | skipped_rule_blocked | 1.622 | 0 | 0 | market_neutral / 49.34 | 24.43% / 20.00%-40.00% (aligned) | unknown | 0 | 0.00% | CAUTION | 当前组合缺少宽基，本候选不能改善宽基缺口。 |  | already held |

## 交易成本口径
- 佣金率：0.00012
- 单笔最低佣金：5.00 元
- 滑点率：0.0003
- ETF 模拟暂不计印花税：0.0
- 过户费：0.0
- 执行价格口径：close_price_with_slippage

## 安全边界
- 只写本地模拟盘。
- 不接真实交易。
- 不添加真实交易按钮。

## B1 策略增强预览

- 本节由 `strategy_enhancement_preview.py` 追加，只作预览，不改变真实模拟交易计划。
- Top 3 是否变化：否。
- adjusted_rank_score_execution_enabled：false。
- PAPER_USE_MARKET_STATE_POSITION：false。

### Adjusted Preview Top 3
1. 516510 云计算ETF：rank=1，score=86.861
2. 159929 医药ETF：rank=2，score=84.2162
3. 515000 科技ETF：rank=3，score=75.0373
