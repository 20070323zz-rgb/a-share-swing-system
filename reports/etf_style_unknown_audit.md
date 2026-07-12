# ETF Style UNKNOWN 审计

本报告列出仍无法自动判断 style_profile 的 ETF。系统宁可保留 UNKNOWN，也不乱猜。

- ETF 总数：183
- UNKNOWN 数量：0
- 目标 UNKNOWN <= 15
- 是否达标：True
- 原因：UNKNOWN is preserved when metadata/name/group/type cannot identify a reliable style. No guessing.

| symbol | name | group | type | pool | data_quality | classification_reason | manual_override_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

## 安全边界
- 本审计不修改 BUY ranking、market_regime、模拟仓或交易记录。