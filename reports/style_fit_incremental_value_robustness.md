# Style Fit Incremental Value Robustness

- classification: PARTIAL_SUPPORT
- research_only: True
- execution_allowed: False

| analysis_method | period_or_group | horizon | supported_count | conflict_count | median_diff | excess_diff | direction | incremental_value_supported |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pooled ETF-day | ALL | 5d | 437 | 484 | 0.0075 | 0.004294 | SUPPORTED_BEATS_CONFLICT | True |
| Pooled ETF-day | ALL | 10d | 425 | 479 | 0.017213 | 0.01399 | SUPPORTED_BEATS_CONFLICT | True |
| Pooled ETF-day | ALL | 20d | 414 | 462 | 0.033904 | 0.017171 | SUPPORTED_BEATS_CONFLICT | True |
| Calendar / Chronological Time Split | CALENDAR_YEAR:2025 | 5d | 297 | 274 | 0.001526 | -0.003537 | NEUTRAL | False |
| Calendar / Chronological Time Split | CALENDAR_YEAR:2025 | 10d | 297 | 274 | 0.006403 | 0.005785 | SUPPORTED_BEATS_CONFLICT | True |
| Calendar / Chronological Time Split | CALENDAR_YEAR:2025 | 20d | 297 | 274 | 0.008773 | -0.001703 | NEUTRAL | False |
| Calendar / Chronological Time Split | CALENDAR_YEAR:2026 | 5d | 140 | 210 | 0.016157 | 0.012553 | SUPPORTED_BEATS_CONFLICT | True |
| Calendar / Chronological Time Split | CALENDAR_YEAR:2026 | 10d | 128 | 205 | 0.051669 | 0.035746 | SUPPORTED_BEATS_CONFLICT | True |
| Calendar / Chronological Time Split | CALENDAR_YEAR:2026 | 20d | 117 | 188 | 0.076291 | 0.052592 | SUPPORTED_BEATS_CONFLICT | True |
| Calendar / Chronological Time Split | CHRONOLOGICAL_HALF:EARLY | 5d | 284 | 248 | 0.002842 | -0.004085 | NEUTRAL | False |
| Calendar / Chronological Time Split | CHRONOLOGICAL_HALF:EARLY | 10d | 284 | 248 | 0.009169 | 0.006271 | SUPPORTED_BEATS_CONFLICT | True |
| Calendar / Chronological Time Split | CHRONOLOGICAL_HALF:EARLY | 20d | 284 | 248 | 0.008095 | -0.002888 | NEUTRAL | False |
| Calendar / Chronological Time Split | CHRONOLOGICAL_HALF:LATE | 5d | 153 | 236 | 0.013775 | 0.012861 | SUPPORTED_BEATS_CONFLICT | True |
| Calendar / Chronological Time Split | CHRONOLOGICAL_HALF:LATE | 10d | 141 | 231 | 0.048088 | 0.032484 | SUPPORTED_BEATS_CONFLICT | True |
| Calendar / Chronological Time Split | CHRONOLOGICAL_HALF:LATE | 20d | 130 | 214 | 0.071878 | 0.052046 | SUPPORTED_BEATS_CONFLICT | True |
| ETF-Level Aggregation | ALL | 5d | 437 | 484 | 0.010021 | 0.005056 | SUPPORTED_BEATS_CONFLICT | True |
| Regime-Segment Aggregation | ALL | 5d | 437 | 484 | -0.001457 | 0.008338 | CONFLICT_BEATS_SUPPORTED | False |
| ETF-Level Aggregation | ALL | 10d | 425 | 479 | 0.040103 | 0.014117 | SUPPORTED_BEATS_CONFLICT | True |
| Regime-Segment Aggregation | ALL | 10d | 425 | 479 | 0.01058 | 0.012225 | SUPPORTED_BEATS_CONFLICT | True |
| ETF-Level Aggregation | ALL | 20d | 414 | 462 | 0.05914 | 0.020188 | SUPPORTED_BEATS_CONFLICT | True |
| Regime-Segment Aggregation | ALL | 20d | 414 | 462 | 0.036706 | 0.032394 | SUPPORTED_BEATS_CONFLICT | True |
| Horizon | ALL | 5d | 437 | 484 | 0.0075 | 0.004294 | SUPPORTED_BEATS_CONFLICT | True |
| Horizon | ALL | 10d | 425 | 479 | 0.017213 | 0.01399 | SUPPORTED_BEATS_CONFLICT | True |
| Horizon | ALL | 20d | 414 | 462 | 0.033904 | 0.017171 | SUPPORTED_BEATS_CONFLICT | True |