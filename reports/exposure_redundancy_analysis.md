# Exposure Redundancy Analysis

## Representative Metrics

- `market_beta`: beta_120d
- `realized_volatility`: annualized_volatility_60d
- `downside_drawdown_risk`: absolute max_drawdown_120d
- `trading_liquidity`: log(avg_amount_60d)
- `return_momentum`: past_return_60d

## Spearman Redundancy Matrix

| exposure_name | market_beta | realized_volatility | downside_drawdown_risk | trading_liquidity | return_momentum |
| --- | --- | --- | --- | --- | --- |
| market_beta | 1.000 | 0.874 | 0.232 | 0.409 | 0.594 |
| realized_volatility | 0.874 | 1.000 | 0.559 | 0.406 | 0.385 |
| downside_drawdown_risk | 0.232 | 0.559 | 1.000 | -0.038 | -0.294 |
| trading_liquidity | 0.409 | 0.406 | -0.038 | 1.000 | 0.379 |
| return_momentum | 0.594 | 0.385 | -0.294 | 0.379 | 1.000 |

## Pairwise Interpretation

| pair | spearman_corr | redundancy_level |
| --- | --- | --- |
| market_beta / realized_volatility | 0.874 | HIGH |
| market_beta / downside_drawdown_risk | 0.232 | LOW |
| market_beta / trading_liquidity | 0.409 | LOW |
| market_beta / return_momentum | 0.594 | LOW |
| realized_volatility / downside_drawdown_risk | 0.559 | LOW |
| realized_volatility / trading_liquidity | 0.406 | LOW |
| realized_volatility / return_momentum | 0.385 | LOW |
| downside_drawdown_risk / trading_liquidity | -0.038 | LOW |
| downside_drawdown_risk / return_momentum | -0.294 | LOW |
| trading_liquidity / return_momentum | 0.379 | LOW |

## Findings

- `market_beta` and `realized_volatility` are highly related in this V2 universe, which means beta partly behaves like a risk-intensity proxy rather than a pure market exposure.
- `realized_volatility` and `downside_drawdown_risk` are related but not identical. Downside volatility is highly redundant with volatility, while max drawdown adds tail-path information.
- `trading_liquidity` provides the most independent information among the five exposure families.
- `return_momentum` is moderately independent. It correlates with beta/volatility in high-beta rally conditions, but it is not fully redundant.
