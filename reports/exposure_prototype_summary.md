# Exposure Prototype Summary

## Status

- Phase: Exposure Framework Phase C - Narrow Prototype Development
- Exposure Prototype: COMPLETE
- Scope: NARROW_PRICE_LIQUIDITY_ONLY
- Universe Version: universe_v2_qualified_research
- Calculation Date: 2026-07-08
- ETF Count: 16
- Value Rows: 240
- Missing Rows: 0
- Preview Research: NOT_STARTED
- Formal Execution: BLOCKED
- Execution Allowed: false

## Approved Exposure Scope

- `market_beta`
- `realized_volatility`
- `downside_drawdown_risk`
- `trading_liquidity`
- `return_momentum`

No other exposure was calculated.

## Output Files

- Values long format: `data/research/exposure_prototype/exposure_prototype_values.csv`
- Values wide format: `data/research/exposure_prototype/exposure_prototype_wide.csv`
- Missing data: `data/research/exposure_prototype/exposure_prototype_missing_data.csv`
- Universe coverage: `data/research/exposure_prototype/exposure_prototype_universe_coverage.csv`
- Manifest: `data/research/exposure_prototype/exposure_prototype_manifest.json`

## Exposure Row Counts

| exposure_name | rows |
| --- | --- |
| downside_drawdown_risk | 64 |
| market_beta | 32 |
| realized_volatility | 32 |
| return_momentum | 48 |
| trading_liquidity | 64 |

## Confidence Distribution

| confidence_level | rows |
| --- | --- |
| HIGH | 224 |
| MEDIUM | 16 |

## Universe Coverage

| metric | value |
| --- | --- |
| coverage rows | 16 |
| current for calculation date | 16 |
| not current for calculation date | 0 |

## PIT Safety Notes

- All rolling windows end at calculation_date.
- No forward returns are read or generated.
- Benchmark beta uses only ETF and benchmark returns <= calculation_date.
- Missing data produces explicit missing rows and confidence flags.

## Boundary

- Research only: true
- ETF daily source: `data/etf_daily/`
- ETF daily copied: false
- Ranking changed: false
- Strategy changed: false
- Preview created: false
- Formal execution changed: false
