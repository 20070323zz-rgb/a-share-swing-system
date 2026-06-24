# 本地数据覆盖报告 2026-06-24 23:04:49

本报告只检查本地 CSV 覆盖情况，不联网，不接券商 API，不下单。

## 摘要
- ETF/观察池总数：78
- ETF 总数：76
- ETF 数据缺失数量：0
- 个股观察缺失数量：2
- 有效数据数量：76
- 缺失或无效数据数量：2
- 数据过期数量：0
- trade_pool 覆盖率：63/63 = 100.00%
- observe_pool 覆盖率：13/15 = 86.67%
- research_only 覆盖率：0/0 = 0.00%
- observe_pool 总缺失数量：2
- research_only 总缺失数量：0

## 明细
| 代码 | 名称 | 类型 | pool | group | 文件 | 行数 | 起始日期 | 结束日期 | 必要字段 | 是否有效 | 是否过期 | 说明 |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 510300 | 沪深300ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_510300.csv | 1081 | 2022-01-04 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 510500 | 中证500ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_510500.csv | 112 | 2026-01-05 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512100 | 中证1000ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_512100.csv | 112 | 2026-01-05 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159915 | 创业板ETF | ETF | trade_pool | 宽基 | data/etf_daily/sz_159915.csv | 1081 | 2022-01-04 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 588000 | 科创50ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_588000.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 510050 | 上证50ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_510050.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 510180 | 上证180ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_510180.csv | 112 | 2026-01-05 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159901 | 深100ETF | ETF | trade_pool | 宽基 | data/etf_daily/sz_159901.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159949 | 创业板50ETF | ETF | trade_pool | 宽基 | data/etf_daily/sz_159949.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 588080 | 科创创业50ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_588080.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512880 | 证券ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_512880.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512800 | 银行ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_512800.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512200 | 房地产ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_512200.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 510230 | 金融ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_510230.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159940 | 金融ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sz_159940.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512070 | 非银ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_512070.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 515880 | 证券公司ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_515880.csv | 112 | 2026-01-05 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512010 | 医药ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_512010.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159929 | 医药ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159929.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512170 | 医疗ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_512170.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512690 | 酒ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_512690.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159928 | 消费ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159928.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 515650 | 消费50ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_515650.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159996 | 家电ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159996.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 515170 | 食品饮料ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_515170.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159736 | 食品ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159736.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159766 | 旅游ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159766.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 516110 | 汽车ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_516110.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512480 | 半导体ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_512480.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512760 | 芯片ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_512760.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159995 | 芯片ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sz_159995.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 588200 | 科创芯片ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_588200.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 515050 | 5GETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_515050.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 515000 | 科技ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_515000.csv | 1081 | 2022-01-04 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 515230 | 软件ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_515230.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159819 | 人工智能ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sz_159819.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 515070 | AIETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_515070.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159869 | 游戏ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sz_159869.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 516510 | 云计算ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_516510.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512980 | 传媒ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_512980.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 515790 | 光伏ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_515790.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159857 | 光伏ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sz_159857.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 516160 | 新能源ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_516160.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 515700 | 新能源车ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_515700.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159755 | 电池ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sz_159755.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 516390 | 新能源汽车ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_516390.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 516800 | 智能制造ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_516800.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512660 | 军工ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_512660.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512670 | 国防ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_512670.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159806 | 新能源车电池ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sz_159806.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512400 | 有色ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sh_512400.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 516780 | 稀土ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sh_516780.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 515220 | 煤炭ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sh_515220.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159930 | 能源ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sz_159930.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 510410 | 资源ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sh_510410.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159865 | 养殖ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sz_159865.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159825 | 农业ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sz_159825.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159876 | 有色金属ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sz_159876.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 510880 | 红利ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sh_510880.csv | 112 | 2026-01-05 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 512890 | 红利低波ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sh_512890.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 515080 | 中证红利ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sh_515080.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159905 | 深红利ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sz_159905.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 518880 | 黄金ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sh_518880.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 513500 | 标普500ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513500.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 513100 | 纳指ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513100.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 513180 | 恒生科技ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513180.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159920 | 恒生ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sz_159920.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 513050 | 中概互联网ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513050.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 513060 | 恒生医疗ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513060.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159941 | 纳指ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sz_159941.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 511010 | 国债ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511010.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 511260 | 十年国债ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511260.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 511880 | 银华日利ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511880.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 511990 | 华宝添益ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511990.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 511360 | 短融ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511360.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 159001 | 货币ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sz_159001.csv | 319 | 2025-03-03 | 2026-06-24 | 是 | 是 | 否 | 有效 |
| 600519 | 贵州茅台 | STOCK | observe_pool | 个股观察 |  | 0 |  |  | 否 | 否 | 否 | 缺少本地 CSV |
| 300750 | 宁德时代 | STOCK | observe_pool | 个股观察 |  | 0 |  |  | 否 | 否 | 否 | 缺少本地 CSV |