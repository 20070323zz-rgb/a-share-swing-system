# Market Breadth 与 Regime 分析

本报告检查当前 regime 是否真正区分市场宽度，避免局部热点被误读为全市场 risk_on。

| normalized_regime | sample_count | buy_breadth_mean | sell_breadth_mean | strong_resonance_breadth_mean | risk_pressure_mean |
| --- | --- | --- | --- | --- | --- |
| DEFENSIVE | 58 | 0.2613 | 0.5933 | 0.2480 | 0.4929 |
| NEUTRAL | 55 | 0.3841 | 0.4620 | 0.3040 | 0.3998 |
| OFFENSIVE | 154 | 0.4462 | 0.2999 | 0.3137 | 0.2448 |

- OFFENSIVE buy breadth - DEFENSIVE buy breadth：0.1849
- DEFENSIVE sell breadth - OFFENSIVE sell breadth：0.2934
- OFFENSIVE buy breadth 是否明显更高：True
- DEFENSIVE sell breadth 是否明显更高：True
- 局部热点误判 risk_on 风险：False
- strong resonance breadth：needs forward-return confirmation; breadth is descriptive in this phase