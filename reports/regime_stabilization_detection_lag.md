# Regime Stabilization Detection Lag

Detection lag 按 raw regime segment 计算；未回填第一天，严格 point-in-time。

| candidate | average_detection_lag | median_detection_lag | p90_detection_lag | missed_segment_count | missed_segment_ratio |
| --- | --- | --- | --- | --- | --- |
| RAW | 0 | 0 | 0 | 0 | 0 |
| CONFIRM_2D | 0.714286 | 1 | 1 | 10 | 0.222222 |
| CONFIRM_3D | 1.259259 | 2 | 2 | 18 | 0.4 |
| ASYMMETRIC_CONFIRM | 0.818182 | 1 | 2 | 12 | 0.266667 |