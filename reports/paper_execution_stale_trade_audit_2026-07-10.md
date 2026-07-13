# Paper Execution Stale Trade Audit 2026-07-10

Audit mode: non-destructive. Original paper trades and positions are unchanged.

| symbol | action | quantity | original raw_close | official close | difference | status |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 512800 | SELL | 1100 | 0.761000 | 0.767000 | -0.78% | AUDITED_STALE_PRICE_NON_DESTRUCTIVE |
| 516510 | BUY | 700 | 1.805000 | 1.821000 | -0.88% | AUDITED_STALE_PRICE_NON_DESTRUCTIVE |
| 159929 | BUY | 100 | 1.259000 | 1.286000 | -2.10% | AUDITED_STALE_PRICE_NON_DESTRUCTIVE |

## Boundary

- No replacement execution was calculated or written.
- `data/paper_trades.csv` was not modified.
- `data/paper_positions.csv` was not modified.
- A future correction policy requires separate Main approval.
