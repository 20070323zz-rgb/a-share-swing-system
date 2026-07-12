# Exposure Window Stability

## Method

Window stability uses Spearman rank correlation, sign consistency, and top/bottom quartile overlap across ETFs. Verdict thresholds are qualitative and research-only.

## Window Pair Results

| exposure_name | window_pair | spearman_rank_corr | sign_consistency | top_quartile_overlap | bottom_quartile_overlap | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| market_beta | beta_60_vs_120 | 0.947 | 0.938 | 1.000 | 1.000 | STABLE |
| realized_volatility | vol_20_vs_60 | 0.903 | 1.000 | 1.000 | 1.000 | STABLE |
| downside_drawdown_risk | max_drawdown_60_vs_120 | 0.765 | 1.000 | 1.000 | 1.000 | PARTIALLY_STABLE |
| downside_drawdown_risk | downside_vol_60_vs_120 | 0.938 | 1.000 | 1.000 | 1.000 | STABLE |
| trading_liquidity | avg_amount_20_vs_60 | 0.956 | 1.000 | 1.000 | 1.000 | STABLE |
| trading_liquidity | avg_volume_20_vs_60 | 0.962 | 1.000 | 1.000 | 1.000 | STABLE |
| return_momentum | return_20_vs_60 | 0.924 | 0.938 | 1.000 | 1.000 | STABLE |
| return_momentum | return_60_vs_120 | 0.697 | 0.625 | 1.000 | 1.000 | UNSTABLE |
| return_momentum | return_20_vs_120 | 0.641 | 0.688 | 1.000 | 1.000 | UNSTABLE |

## Exposure-Level Verdicts

| exposure_name | window_stability |
| --- | --- |
| market_beta | STABLE |
| realized_volatility | STABLE |
| downside_drawdown_risk | PARTIALLY_STABLE |
| trading_liquidity | STABLE |
| return_momentum | PARTIALLY_STABLE |

## Interpretation

- `trading_liquidity`, `market_beta`, and `realized_volatility` are stable across their tested windows.
- `downside_drawdown_risk` is partially stable because downside volatility is stable but max drawdown changes meaningfully between 60d and 120d.
- `return_momentum` is partially stable: 20d and 60d rankings are close, but 120d introduces a longer-cycle component. This is expected and should be preserved as multi-window information rather than collapsed prematurely.
