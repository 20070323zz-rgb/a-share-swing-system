# Exit Rule Parameters by ETF Type 2026-06-18 16:01:13

以下为参数搜索范围，不是固定执行规则；所有范围都需要正式回测验证。

| ETF 类型 | 样本数 | 年化波动中位数 | ATR14 中位数 | 初始止损搜索 | 移动止盈搜索 | 时间止损搜索 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| broad_index | 22 | 23.62% | 2.54% | 5%-8%, 8%-12%, 2.0-4.0x ATR | profit start 5%-10%, trail 4%-8% or 2.5-5.0x ATR | 20-60 days, avoid too-short capital-efficiency exit | 宽基更适合趋势/ranking 出口，止损不宜过紧。 |
| sector | 15 | 18.67% | 2.04% | 4%-6%, 6%-10%, 1.8-3.5x ATR | profit start 4%-8%, trail 3%-7% or 2.0-4.5x ATR | 10-30 days, combine with ranking drop | 行业 ETF 对风格切换敏感，ranking 掉队和趋势破坏应重点测试。 |
| theme | 18 | 32.54% | 3.78% | 4%-6%, 6%-10%, 1.5-3.5x ATR | profit start 3%-8%, trail 2.5%-6% or 2.0-4.0x ATR | 5-20 days, hotspot decay review | 主题 ETF 容易拥挤和退潮，移动止盈与 ranking 连续掉队值得回测。 |
| high_beta | 3 | 23.20% | 2.42% | 4%-6%, 6%-9%, 1.5-3.0x ATR | profit start 3%-8%, trail 2.5%-6% | 5-20 days, short_swing weakening review | 高 beta ETF 不适合宽止损无限持有，需更重视短周期衰减。 |
| commodity_resource | 20 | 29.36% | 3.06% | 4%-8%, 6%-10%, 1.8-3.5x ATR | profit start 5%-10%, trail 4%-8% | 10-45 days, commodity cycle review | 周期资源可能趋势延续，也可能政策/价格冲击反转，ATR 与趋势破坏应组合测试。 |
| defensive | 5 | 15.20% | 1.54% | 4%-8%, 2.0-4.0x ATR | profit start 6%-12%, trail 4%-8% | 20-60 days, allow slower trend | 防御/红利 ETF 更偏慢趋势，过紧止盈可能降低防守价值。 |
| bond_cash | 12 | 0.95% | 0.04% | 0.5%-2.5%, duration/credit event review | not primary | 30-90 days, liquidity/carry review | 债券/货币 ETF 需单独规则，不套权益 ETF 止盈止损。 |
| qdii | 15 | 27.34% | 2.61% | observe only | observe only | 10-45 days after premium/fx checks | QDII 自动交易前必须补溢价、汇率、海外交易日和申赎状态。 |
| unknown | 73 | 24.24% | 2.83% | do not auto trade | do not auto trade | manual classification first | unknown 分类先不进入自动交易回测池。 |

## 特别说明
- 宽基 ETF：更适合 ranking exit + 趋势破坏，止损不宜过紧。
- 行业/周期/主题 ETF：更需要移动止盈和 ranking 连续掉队检测。
- 高 beta ETF：应更关注 short_swing 转弱、profit giveback 和高波动风险。
- 债券/货币 ETF：单独规则，不套权益 ETF 参数。
- QDII ETF：暂不建议进入自动交易规则。
- unknown：必须先人工分类。
