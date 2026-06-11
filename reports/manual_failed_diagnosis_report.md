# 手工 ETF 下载失败诊断报告

- 诊断范围：`reports/manual_import_report.md` 中 dry-run 失败的 ETF
- 失败总数：50
- 抽样 curl -4 测试数量：10
- 写入 data/etf_daily：否
- 正式导入：未运行
- 券商 API：未使用
- 账号密码：未读取
- 真实下单：未执行
- 自动交易：未执行
- 策略逻辑：未修改

## 按 group 统计
| group | failed_count |
|---|---:|
| 科技成长 | 10 |
| 新能源制造 | 10 |
| 周期资源 | 8 |
| QDII观察 | 7 |
| 债券货币观察 | 6 |
| 防御风格 | 5 |
| 消费医药 | 4 |

## 按 pool 统计
| pool | failed_count |
|---|---:|
| trade_pool | 37 |
| observe_pool | 13 |

## 按错误类型统计
| error_type | count |
|---|---:|
| manual CSV not found / no recent curl error recorded | 40 |
| Remote end closed connection without response | 10 |

## 抽样 curl -4 结果统计
| curl_result | count |
|---|---:|
| empty reply | 10 |

## 失败标的清单
| symbol | name | group | pool | market/secid | QDII | 债券货币 | 行业ETF | 上次失败原因 |
|---|---|---|---|---|---|---|---|---|
| 159996 | 家电ETF | 消费医药 | trade_pool | 0.159996 | 否 | 否 | 是 | Remote end closed connection without response |
| 515170 | 食品饮料ETF | 消费医药 | trade_pool | 1.515170 | 否 | 否 | 是 | Remote end closed connection without response |
| 159736 | 食品ETF | 消费医药 | trade_pool | 0.159736 | 否 | 否 | 是 | Remote end closed connection without response |
| 516110 | 汽车ETF | 消费医药 | trade_pool | 1.516110 | 否 | 否 | 是 | Remote end closed connection without response |
| 512480 | 半导体ETF | 科技成长 | trade_pool | 1.512480 | 否 | 否 | 是 | Remote end closed connection without response |
| 159995 | 芯片ETF | 科技成长 | trade_pool | 0.159995 | 否 | 否 | 是 | Remote end closed connection without response |
| 588200 | 科创芯片ETF | 科技成长 | trade_pool | 1.588200 | 否 | 否 | 是 | Remote end closed connection without response |
| 515050 | 5GETF | 科技成长 | trade_pool | 1.515050 | 否 | 否 | 是 | Remote end closed connection without response |
| 515230 | 软件ETF | 科技成长 | trade_pool | 1.515230 | 否 | 否 | 是 | Remote end closed connection without response |
| 159819 | 人工智能ETF | 科技成长 | trade_pool | 0.159819 | 否 | 否 | 是 | Remote end closed connection without response |
| 515070 | AIETF | 科技成长 | trade_pool | 1.515070 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 159869 | 游戏ETF | 科技成长 | trade_pool | 0.159869 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 516510 | 云计算ETF | 科技成长 | trade_pool | 1.516510 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 512980 | 传媒ETF | 科技成长 | trade_pool | 1.512980 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 515790 | 光伏ETF | 新能源制造 | trade_pool | 1.515790 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 159857 | 光伏ETF | 新能源制造 | trade_pool | 0.159857 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 516160 | 新能源ETF | 新能源制造 | trade_pool | 1.516160 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 515700 | 新能源车ETF | 新能源制造 | trade_pool | 1.515700 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 159755 | 电池ETF | 新能源制造 | trade_pool | 0.159755 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 516390 | 新能源汽车ETF | 新能源制造 | trade_pool | 1.516390 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 516800 | 智能制造ETF | 新能源制造 | trade_pool | 1.516800 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 512660 | 军工ETF | 新能源制造 | trade_pool | 1.512660 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 512670 | 国防ETF | 新能源制造 | trade_pool | 1.512670 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 159806 | 新能源车电池ETF | 新能源制造 | trade_pool | 0.159806 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 512400 | 有色ETF | 周期资源 | trade_pool | 1.512400 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 516780 | 稀土ETF | 周期资源 | trade_pool | 1.516780 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 515220 | 煤炭ETF | 周期资源 | trade_pool | 1.515220 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 159930 | 能源ETF | 周期资源 | trade_pool | 0.159930 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 510410 | 资源ETF | 周期资源 | trade_pool | 1.510410 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 159865 | 养殖ETF | 周期资源 | trade_pool | 0.159865 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 159825 | 农业ETF | 周期资源 | trade_pool | 0.159825 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 159876 | 有色金属ETF | 周期资源 | trade_pool | 0.159876 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 510880 | 红利ETF | 防御风格 | trade_pool | 1.510880 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 512890 | 红利低波ETF | 防御风格 | trade_pool | 1.512890 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 515080 | 中证红利ETF | 防御风格 | trade_pool | 1.515080 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 159905 | 深红利ETF | 防御风格 | trade_pool | 0.159905 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 518880 | 黄金ETF | 防御风格 | trade_pool | 1.518880 | 否 | 否 | 是 | manual CSV not found / no recent curl error recorded |
| 513500 | 标普500ETF | QDII观察 | observe_pool | 1.513500 | 是 | 否 | 否 | manual CSV not found / no recent curl error recorded |
| 513100 | 纳指ETF | QDII观察 | observe_pool | 1.513100 | 是 | 否 | 否 | manual CSV not found / no recent curl error recorded |
| 513180 | 恒生科技ETF | QDII观察 | observe_pool | 1.513180 | 是 | 否 | 否 | manual CSV not found / no recent curl error recorded |
| 159920 | 恒生ETF | QDII观察 | observe_pool | 0.159920 | 是 | 否 | 否 | manual CSV not found / no recent curl error recorded |
| 513050 | 中概互联网ETF | QDII观察 | observe_pool | 1.513050 | 是 | 否 | 否 | manual CSV not found / no recent curl error recorded |
| 513060 | 恒生医疗ETF | QDII观察 | observe_pool | 1.513060 | 是 | 否 | 否 | manual CSV not found / no recent curl error recorded |
| 159941 | 纳指ETF | QDII观察 | observe_pool | 0.159941 | 是 | 否 | 否 | manual CSV not found / no recent curl error recorded |
| 511010 | 国债ETF | 债券货币观察 | observe_pool | 1.511010 | 否 | 是 | 否 | manual CSV not found / no recent curl error recorded |
| 511260 | 十年国债ETF | 债券货币观察 | observe_pool | 1.511260 | 否 | 是 | 否 | manual CSV not found / no recent curl error recorded |
| 511880 | 银华日利ETF | 债券货币观察 | observe_pool | 1.511880 | 否 | 是 | 否 | manual CSV not found / no recent curl error recorded |
| 511990 | 华宝添益ETF | 债券货币观察 | observe_pool | 1.511990 | 否 | 是 | 否 | manual CSV not found / no recent curl error recorded |
| 511360 | 短融ETF | 债券货币观察 | observe_pool | 1.511360 | 否 | 是 | 否 | manual CSV not found / no recent curl error recorded |
| 159001 | 货币ETF | 债券货币观察 | observe_pool | 0.159001 | 否 | 是 | 否 | manual CSV not found / no recent curl error recorded |

## 抽样测试结果
| symbol | name | group | secid | curl_result | rows | message |
|---|---|---|---|---|---:|---|
| 159996 | 家电ETF | 消费医药 | 0.159996 | empty reply | 0 | curl: (52) Empty reply from server |
| 512480 | 半导体ETF | 科技成长 | 1.512480 | empty reply | 0 | curl: (52) Empty reply from server |
| 515790 | 光伏ETF | 新能源制造 | 1.515790 | empty reply | 0 | curl: (52) Empty reply from server |
| 512400 | 有色ETF | 周期资源 | 1.512400 | empty reply | 0 | curl: (52) Empty reply from server |
| 510880 | 红利ETF | 防御风格 | 1.510880 | empty reply | 0 | curl: (52) Empty reply from server |
| 513500 | 标普500ETF | QDII观察 | 1.513500 | empty reply | 0 | curl: (52) Empty reply from server |
| 511010 | 国债ETF | 债券货币观察 | 1.511010 | empty reply | 0 | curl: (52) Empty reply from server |
| 515170 | 食品饮料ETF | 消费医药 | 1.515170 | empty reply | 0 | curl: (52) Empty reply from server |
| 159736 | 食品ETF | 消费医药 | 0.159736 | empty reply | 0 | curl: (52) Empty reply from server |
| 516110 | 汽车ETF | 消费医药 | 1.516110 | empty reply | 0 | curl: (52) Empty reply from server |

## secid 映射检查
未发现 secid 映射错误。当前失败 ETF 均符合：5/6 开头使用 `1.xxxxxx`，0/1/3/159 开头使用 `0.xxxxxx`。

## 判断
- 是否判断为接口不稳定：否
- 是否判断为 secid 映射问题：否
- 说明：本轮抽样未同时出现成功和失败，需结合历史下载结果判断接口稳定性。

## 下一步建议
1. 不建议继续无差别高频重试。
2. 可以按 group 分批、低频、间隔更长地重试失败 symbol，并保留失败诊断。
3. 当前不建议正式导入全 ETF，因为仍有 50 个缺失。
4. 若需要推进，可只正式导入已验证通过的 26 个 ETF，导入规则继续保留 `data/etf_daily/` 原有数据优先。
5. 对持续 empty reply 的标的，可考虑增加另一个公开数据源作为后备，但仍不能使用登录、cookie、账号或券商 API。
