# Ranking Model V2 Design 2026-06-18 20:28:15

本设计只用于后续历史回测，不接入执行层。

## Candidate A: Momentum + Trend Confirmation
- 因子：risk_adjusted_momentum, trend_slope_20, trend_slope_60, ma_distance_20, ma_distance_60
- 适合市场：risk-on and steady trend markets
- 可能过拟合点：MA and momentum windows can be over-tuned
- 预期改善：reduce false Top3 from short-term bounce-only momentum
- 回测优先级：high

## Candidate B: Relative Strength Rotation
- 因子：relative_strength_vs_510300, relative_strength_vs_group, momentum_20d, momentum_60d
- 适合市场：cross-sectional rotation markets
- 可能过拟合点：group definitions and benchmark choice may dominate
- 预期改善：separate broad market beta from ETF-specific strength
- 回测优先级：high

## Candidate C: Low Turnover Stable Ranking
- 因子：momentum_20d, momentum_60d, trend_confirm, ranking_persistence, turnover_penalty, cooldown_penalty
- 适合市场：range and noisy markets
- 可能过拟合点：persistence thresholds can overfit turnover
- 预期改善：reduce minimum-commission drag and whipsaw
- 回测优先级：high

## Candidate D: Risk-Aware Adjusted Ranking
- 因子：base_score, volatility_penalty, drawdown_penalty, high_beta_penalty, group_concentration_penalty, data_health_penalty, liquidity_filter
- 适合市场：neutral/risk-control regimes
- 可能过拟合点：too many penalties can suppress alpha
- 预期改善：improve drawdown and exposure profile
- 回测优先级：medium

## Candidate E: Market-State Conditional Ranking
- 因子：risk_on growth/high_beta, neutral balanced, risk_off broad_based/defensive/cash preference
- 适合市场：regime-switching markets
- 可能过拟合点：market_state misclassification can cause missed upside
- 预期改善：reduce common beta drawdown and style mismatch
- 回测优先级：medium

## 建议进入后续回测
- A Momentum + Trend Confirmation
- B Relative Strength Rotation
- C Low Turnover Stable Ranking
- D Risk-Aware Adjusted Ranking
- E Market-State Conditional Ranking 先作为分组/过滤研究。
