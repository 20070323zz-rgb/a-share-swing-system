# Market Regime 历史回放

Point-in-time replay：每个 T 日只使用 T 日及以前数据；forward return 只作为标签。

- replay_start_date：2025-05-30
- replay_end_date：2026-07-06
- replay_trading_days：267
- raw values：['neutral', 'risk_off', 'risk_on']
- normalized mapping：{'risk_on': 'OFFENSIVE', 'neutral': 'NEUTRAL', 'risk_off': 'DEFENSIVE'}
- realized profile：realized risk profile is recalculated per T date from <=T data; forward returns are labels only.

| date | raw_market_regime | normalized_regime | pool_size | buy_count | sell_count | buy_breadth | sell_breadth | strong_resonance_breadth | risk_pressure | benchmark_return_10d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-23 | risk_on | OFFENSIVE | 39 | 10 | 23 | 0.2564 | 0.5897 | 0.1026 | 0.5513 |  |
| 2026-06-24 | neutral | NEUTRAL | 39 | 11 | 23 | 0.2821 | 0.5897 | 0.2821 | 0.5513 |  |
| 2026-06-25 | risk_on | OFFENSIVE | 39 | 10 | 20 | 0.2564 | 0.5128 | 0.2308 | 0.5000 |  |
| 2026-06-26 | neutral | NEUTRAL | 39 | 14 | 24 | 0.3590 | 0.6154 | 0.3077 | 0.6410 |  |
| 2026-06-29 | risk_on | OFFENSIVE | 39 | 19 | 20 | 0.4872 | 0.5128 | 0.2821 | 0.5641 |  |
| 2026-06-30 | risk_on | OFFENSIVE | 39 | 14 | 18 | 0.3590 | 0.4615 | 0.2564 | 0.5256 |  |
| 2026-07-01 | risk_on | OFFENSIVE | 39 | 17 | 17 | 0.4359 | 0.4359 | 0.3333 | 0.5000 |  |
| 2026-07-02 | neutral | NEUTRAL | 39 | 13 | 20 | 0.3333 | 0.5128 | 0.3333 | 0.5513 |  |
| 2026-07-03 | neutral | NEUTRAL | 39 | 17 | 19 | 0.4359 | 0.4872 | 0.3846 | 0.5513 |  |
| 2026-07-06 | neutral | NEUTRAL | 39 | 13 | 18 | 0.3333 | 0.4615 | 0.1795 | 0.5128 |  |

## 安全边界
- 本报告不修改 market_regime / ranking / adjusted preview / paper_trade_engine / paper_trades / paper_positions。