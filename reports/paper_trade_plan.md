# 规则验证版模拟交易计划 2026-07-04

本报告只针对本地模拟盘，不接券商 API，不真实下单。
模拟执行日期为 2026-07-04；价格使用本地最新行情数据日 2026-07-03 的 close proxy。

## 引擎状态
- run_date：2026-07-04
- price_data_date：2026-07-03
- PAPER_MODE：rule_validation
- PAPER_AUTO_EXECUTE：True
- REAL_TRADE_ENABLED：False
- BROKER_API_ENABLED：False
- status：executed
- dry_run：False
- buy_count：0
- sell_count：0
- skipped_duplicate：False
- skip_reason：
- PAPER_USE_MARKET_STATE_POSITION：False

## 账户摘要
- 执行前现金：7058.11
- 执行前仓位：29.44%
- 执行后现金：7058.11
- 执行后仓位：29.44%

## Phase 2C 轻量接入说明
- etf_type / max_holding_days / stop_loss_pct 已进入计划解释和风险展示。
- market_state 只展示建议仓位区间，不改变买入金额或目标仓位。
- portfolio_exposure 只生成组合平衡提示和集中度提示，不阻断交易。
- 本轮不改变 max_holdings，不改变 paper_trade_engine 核心成交逻辑。

## 交易计划与结果
| run_date | price_data_date | symbol | name | action | status | raw_close | quantity | gross_amount | market_state | current/suggested position | etf_type | max_days | stop_loss_pct | exposure_status | balance_suggestion | concentration_warning | reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |
| 2026-07-04 | 2026-07-03 | 512800 | 银行ETF | SELL | skipped_no_sell_signal | 0.747 | 1100 | 821.45 | market_strong / 72.92 | 29.44% / 40.00%-60.00% (below_suggested_range) | sector | 30 | 6.00% | CAUTION | 当前组合缺少宽基，本候选不能改善宽基缺口。 | 当前组合已有金融/周期/高 beta 暴露，新增同类 ETF 可能加剧集中度。 | sell rules not triggered |
| 2026-07-04 | 2026-07-03 | 515000 | 科技ETF | SELL | skipped_no_sell_signal | 1.546 | 1000 | 1545.54 | market_strong / 72.92 | 29.44% / 40.00%-60.00% (below_suggested_range) | unknown | 0 | 0.00% | CAUTION | 当前组合缺少宽基，本候选不能改善宽基缺口。 |  | sell rules not triggered |
| 2026-07-04 | 2026-07-03 | 512880 | 证券ETF | SELL | skipped_no_sell_signal | 1.155 | 500 | 577.33 | market_strong / 72.92 | 29.44% / 40.00%-60.00% (below_suggested_range) | high_beta | 20 | 5.00% | CAUTION | 当前组合缺少宽基，本候选不能改善宽基缺口。 | 当前组合已有金融/周期/高 beta 暴露，新增同类 ETF 可能加剧集中度。 | sell rules not triggered |
| 2026-07-04 | 2026-07-03 | 512010 | 医药ETF | BUY | skipped_rule_blocked | 0.363 | 0 | 0 | market_strong / 72.92 | 29.44% / 40.00%-60.00% (below_suggested_range) | sector | 30 | 6.00% | CAUTION | 当前组合缺少宽基，本候选不能改善宽基缺口。 |  | max holdings reached |
| 2026-07-04 | 2026-07-03 | 512880 | 证券ETF | BUY | skipped_rule_blocked | 1.155 | 0 | 0 | market_strong / 72.92 | 29.44% / 40.00%-60.00% (below_suggested_range) | high_beta | 20 | 5.00% | CAUTION | 当前组合缺少宽基，本候选不能改善宽基缺口。 | 当前组合已有金融/周期/高 beta 暴露，新增同类 ETF 可能加剧集中度。 | already held |
| 2026-07-04 | 2026-07-03 | 159929 | 医药ETF | BUY | skipped_rule_blocked | 1.292 | 0 | 0 | market_strong / 72.92 | 29.44% / 40.00%-60.00% (below_suggested_range) | sector | 30 | 6.00% | CAUTION | 当前组合缺少宽基，本候选不能改善宽基缺口。 |  | max holdings reached |

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
- Top 3 是否变化：是。
- adjusted_rank_score_execution_enabled：false。
- PAPER_USE_MARKET_STATE_POSITION：false。

### Adjusted Preview Top 3
1. 512010 医药ETF：rank=1，score=95.1375
2. 512880 证券ETF：rank=2，score=90.493
3. 588000 科创50ETF：rank=3，score=79.6456
