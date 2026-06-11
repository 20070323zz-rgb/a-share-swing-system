# 手工下载 ETF CSV 批量验证报告

- 验证对象：`data/manual_import/` 中 watchlist ETF CSV
- 验证通过：26
- 验证失败：50
- 存在日期重叠的 ETF 数量：3
- 后续导入重叠处理规则：保留 `data/etf_daily/` 原有数据，避免覆盖 BaoStock 数据。
- 券商 API：未使用
- 账号密码：未读取
- 真实下单：未执行
- 自动交易：未执行
- 策略逻辑：未修改

| 代码 | 名称 | group | pool | 文件存在 | 有效 | 行数 | 日期范围 | 必需字段 | amount | 日期错误 | 重复日期 | OHLC异常 | high<low | volume异常 | volume最长连续0 | amount异常 | 现有日期范围 | 重叠日期数 | 重叠范围 | 说明 |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |
| 510300 | 沪深300ETF | 宽基 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2022-01-04 to 2026-06-03 | 969 | 2022-01-04 to 2025-12-31 | ok |
| 510500 | 中证500ETF | 宽基 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 512100 | 中证1000ETF | 宽基 | trade_pool | 是 | 是 | 968 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 159915 | 创业板ETF | 宽基 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2022-01-04 to 2026-06-03 | 969 | 2022-01-04 to 2025-12-31 | ok |
| 588000 | 科创50ETF | 宽基 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 510050 | 上证50ETF | 宽基 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 510180 | 上证180ETF | 宽基 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 159901 | 深100ETF | 宽基 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 159949 | 创业板50ETF | 宽基 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 588080 | 科创创业50ETF | 宽基 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 512880 | 证券ETF | 金融地产 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 512800 | 银行ETF | 金融地产 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 512200 | 房地产ETF | 金融地产 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 510230 | 金融ETF | 金融地产 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 159940 | 金融ETF | 金融地产 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 512070 | 非银ETF | 金融地产 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 515880 | 证券公司ETF | 金融地产 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 512010 | 医药ETF | 消费医药 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 159929 | 医药ETF | 消费医药 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 512170 | 医疗ETF | 消费医药 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 512690 | 酒ETF | 消费医药 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 159928 | 消费ETF | 消费医药 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 515650 | 消费50ETF | 消费医药 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 159996 | 家电ETF | 消费医药 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 515170 | 食品饮料ETF | 消费医药 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159736 | 食品ETF | 消费医药 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159766 | 旅游ETF | 消费医药 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 516110 | 汽车ETF | 消费医药 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 512480 | 半导体ETF | 科技成长 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 512760 | 芯片ETF | 科技成长 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2026-01-05 to 2026-06-03 | 0 |  to  | ok |
| 159995 | 芯片ETF | 科技成长 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 588200 | 科创芯片ETF | 科技成长 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 515050 | 5GETF | 科技成长 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 515000 | 科技ETF | 科技成长 | trade_pool | 是 | 是 | 969 | 2022-01-04 to 2025-12-31 | 是 | 是 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2022-01-04 to 2026-06-03 | 969 | 2022-01-04 to 2025-12-31 | ok |
| 515230 | 软件ETF | 科技成长 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159819 | 人工智能ETF | 科技成长 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 515070 | AIETF | 科技成长 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159869 | 游戏ETF | 科技成长 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 516510 | 云计算ETF | 科技成长 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 512980 | 传媒ETF | 科技成长 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 515790 | 光伏ETF | 新能源制造 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159857 | 光伏ETF | 新能源制造 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 516160 | 新能源ETF | 新能源制造 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 515700 | 新能源车ETF | 新能源制造 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159755 | 电池ETF | 新能源制造 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 516390 | 新能源汽车ETF | 新能源制造 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 516800 | 智能制造ETF | 新能源制造 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 512660 | 军工ETF | 新能源制造 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 512670 | 国防ETF | 新能源制造 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159806 | 新能源车电池ETF | 新能源制造 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 512400 | 有色ETF | 周期资源 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 516780 | 稀土ETF | 周期资源 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 515220 | 煤炭ETF | 周期资源 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159930 | 能源ETF | 周期资源 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 510410 | 资源ETF | 周期资源 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159865 | 养殖ETF | 周期资源 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159825 | 农业ETF | 周期资源 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159876 | 有色金属ETF | 周期资源 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 510880 | 红利ETF | 防御风格 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 512890 | 红利低波ETF | 防御风格 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 515080 | 中证红利ETF | 防御风格 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159905 | 深红利ETF | 防御风格 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 518880 | 黄金ETF | 防御风格 | trade_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 513500 | 标普500ETF | QDII观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 513100 | 纳指ETF | QDII观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 513180 | 恒生科技ETF | QDII观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159920 | 恒生ETF | QDII观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 513050 | 中概互联网ETF | QDII观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 513060 | 恒生医疗ETF | QDII观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159941 | 纳指ETF | QDII观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 511010 | 国债ETF | 债券货币观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 511260 | 十年国债ETF | 债券货币观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 511880 | 银华日利ETF | 债券货币观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 511990 | 华宝添益ETF | 债券货币观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 511360 | 短融ETF | 债券货币观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
| 159001 | 货币ETF | 债券货币观察 | observe_pool | 否 | 否 | 0 |  to  | 否 | 否 | 0 | 0 | 0 | 0 | 0 | 0 |  |  to  | 0 |  to  | manual CSV not found |
