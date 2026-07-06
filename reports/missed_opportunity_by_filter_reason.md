# Missed Opportunity By Filter Reason

按 primary_filter_reason 归因。样本未到期时结论为 pending，不得据此调整规则。

| primary_filter_reason   |   candidate_count |   forward_5d_mean |   forward_10d_mean | forward_20d_mean   |   excess_10d_mean |   missed_opportunity_count |   missed_opportunity_rate |   filter_effective_count |   filter_effective_rate | comment                                                       |
|:------------------------|------------------:|------------------:|-------------------:|:-------------------|------------------:|---------------------------:|--------------------------:|-------------------------:|------------------------:|:--------------------------------------------------------------|
| trend_not_confirmed     |                86 |          0.004064 |           0.051523 |                    |          0.073192 |                          5 |                   0.05814 |                        5 |                 0.05814 | possible over-filtering; keep observing before changing rules |
| liquidity_filtered      |                 1 |                   |                    |                    |                   |                          0 |                   0       |                        0 |                 0       | pending; forward return not mature enough                     |
