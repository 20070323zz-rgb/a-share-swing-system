# 本地数据健康报告 2026-07-04 00:03:20

本报告只检查本地 CSV，不联网，不接券商 API，不下单。
QDII观察、债券货币观察、个股观察只做提醒，避免用过严规则误判。

## 摘要
- 检查标的总数：78
- 正常：71
- 提醒：5
- 异常：0
- 缺失：2

## 明细
| 代码 | 名称 | 类型 | pool | group | 文件 | 行数 | 最近日期 | 状态 | 硬问题 | 提醒 |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| 510300 | 沪深300ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_510300.csv | 1088 | 2026-07-03 | 正常 |  |  |
| 510500 | 中证500ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_510500.csv | 119 | 2026-07-03 | 正常 |  |  |
| 512100 | 中证1000ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_512100.csv | 119 | 2026-07-03 | 正常 |  |  |
| 159915 | 创业板ETF | ETF | trade_pool | 宽基 | data/etf_daily/sz_159915.csv | 1088 | 2026-07-03 | 正常 |  |  |
| 588000 | 科创50ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_588000.csv | 326 | 2026-07-03 | 正常 |  |  |
| 510050 | 上证50ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_510050.csv | 326 | 2026-07-03 | 正常 |  |  |
| 510180 | 上证180ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_510180.csv | 119 | 2026-07-03 | 正常 |  |  |
| 159901 | 深100ETF | ETF | trade_pool | 宽基 | data/etf_daily/sz_159901.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159949 | 创业板50ETF | ETF | trade_pool | 宽基 | data/etf_daily/sz_159949.csv | 326 | 2026-07-03 | 正常 |  |  |
| 588080 | 科创创业50ETF | ETF | trade_pool | 宽基 | data/etf_daily/sh_588080.csv | 326 | 2026-07-03 | 正常 |  |  |
| 512880 | 证券ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_512880.csv | 326 | 2026-07-03 | 正常 |  |  |
| 512800 | 银行ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_512800.csv | 326 | 2026-07-03 | 正常 |  |  |
| 512200 | 房地产ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_512200.csv | 326 | 2026-07-03 | 正常 |  |  |
| 510230 | 金融ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_510230.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159940 | 金融ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sz_159940.csv | 326 | 2026-07-03 | 正常 |  |  |
| 512070 | 非银ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_512070.csv | 326 | 2026-07-03 | 正常 |  |  |
| 515880 | 证券公司ETF | ETF | trade_pool | 金融地产 | data/etf_daily/sh_515880.csv | 119 | 2026-07-03 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 512010 | 医药ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_512010.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159929 | 医药ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159929.csv | 326 | 2026-07-03 | 正常 |  |  |
| 512170 | 医疗ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_512170.csv | 326 | 2026-07-03 | 正常 |  |  |
| 512690 | 酒ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_512690.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159928 | 消费ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159928.csv | 326 | 2026-07-03 | 正常 |  |  |
| 515650 | 消费50ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_515650.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159996 | 家电ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159996.csv | 326 | 2026-07-03 | 正常 |  |  |
| 515170 | 食品饮料ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_515170.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159736 | 食品ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159736.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159766 | 旅游ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sz_159766.csv | 326 | 2026-07-03 | 正常 |  |  |
| 516110 | 汽车ETF | ETF | trade_pool | 消费医药 | data/etf_daily/sh_516110.csv | 326 | 2026-07-03 | 正常 |  |  |
| 512480 | 半导体ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_512480.csv | 326 | 2026-07-03 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 512760 | 芯片ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_512760.csv | 326 | 2026-07-03 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 159995 | 芯片ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sz_159995.csv | 326 | 2026-07-03 | 正常 |  |  |
| 588200 | 科创芯片ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_588200.csv | 326 | 2026-07-03 | 正常 |  |  |
| 515050 | 5GETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_515050.csv | 326 | 2026-07-03 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 515000 | 科技ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_515000.csv | 1088 | 2026-07-03 | 正常 |  |  |
| 515230 | 软件ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_515230.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159819 | 人工智能ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sz_159819.csv | 326 | 2026-07-03 | 正常 |  |  |
| 515070 | AIETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_515070.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159869 | 游戏ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sz_159869.csv | 326 | 2026-07-03 | 正常 |  |  |
| 516510 | 云计算ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_516510.csv | 326 | 2026-07-03 | 正常 |  |  |
| 512980 | 传媒ETF | ETF | trade_pool | 科技成长 | data/etf_daily/sh_512980.csv | 326 | 2026-07-03 | 正常 |  |  |
| 515790 | 光伏ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_515790.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159857 | 光伏ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sz_159857.csv | 326 | 2026-07-03 | 正常 |  |  |
| 516160 | 新能源ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_516160.csv | 326 | 2026-07-03 | 正常 |  |  |
| 515700 | 新能源车ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_515700.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159755 | 电池ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sz_159755.csv | 326 | 2026-07-03 | 正常 |  |  |
| 516390 | 新能源汽车ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_516390.csv | 326 | 2026-07-03 | 正常 |  |  |
| 516800 | 智能制造ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_516800.csv | 326 | 2026-07-03 | 正常 |  |  |
| 512660 | 军工ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_512660.csv | 326 | 2026-07-03 | 正常 |  |  |
| 512670 | 国防ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sh_512670.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159806 | 新能源车电池ETF | ETF | trade_pool | 新能源制造 | data/etf_daily/sz_159806.csv | 326 | 2026-07-03 | 正常 |  |  |
| 512400 | 有色ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sh_512400.csv | 326 | 2026-07-03 | 正常 |  |  |
| 516780 | 稀土ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sh_516780.csv | 326 | 2026-07-03 | 提醒 |  | 存在单日涨跌幅极端异常 abs(pct_change)>0.25：1 次，仅提示不删除 |
| 515220 | 煤炭ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sh_515220.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159930 | 能源ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sz_159930.csv | 326 | 2026-07-03 | 正常 |  |  |
| 510410 | 资源ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sh_510410.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159865 | 养殖ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sz_159865.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159825 | 农业ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sz_159825.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159876 | 有色金属ETF | ETF | trade_pool | 周期资源 | data/etf_daily/sz_159876.csv | 326 | 2026-07-03 | 正常 |  |  |
| 510880 | 红利ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sh_510880.csv | 119 | 2026-07-03 | 正常 |  |  |
| 512890 | 红利低波ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sh_512890.csv | 326 | 2026-07-03 | 正常 |  |  |
| 515080 | 中证红利ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sh_515080.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159905 | 深红利ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sz_159905.csv | 326 | 2026-07-03 | 正常 |  |  |
| 518880 | 黄金ETF | ETF | trade_pool | 防御风格 | data/etf_daily/sh_518880.csv | 326 | 2026-07-03 | 正常 |  |  |
| 513500 | 标普500ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513500.csv | 326 | 2026-07-03 | 正常 |  |  |
| 513100 | 纳指ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513100.csv | 326 | 2026-07-03 | 正常 |  |  |
| 513180 | 恒生科技ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513180.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159920 | 恒生ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sz_159920.csv | 326 | 2026-07-03 | 正常 |  |  |
| 513050 | 中概互联网ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513050.csv | 326 | 2026-07-03 | 正常 |  |  |
| 513060 | 恒生医疗ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sh_513060.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159941 | 纳指ETF | ETF | observe_pool | QDII观察 | data/etf_daily/sz_159941.csv | 326 | 2026-07-03 | 正常 |  |  |
| 511010 | 国债ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511010.csv | 326 | 2026-07-03 | 正常 |  |  |
| 511260 | 十年国债ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511260.csv | 326 | 2026-07-03 | 正常 |  |  |
| 511880 | 银华日利ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511880.csv | 326 | 2026-07-03 | 正常 |  |  |
| 511990 | 华宝添益ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511990.csv | 326 | 2026-07-03 | 正常 |  |  |
| 511360 | 短融ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sh_511360.csv | 326 | 2026-07-03 | 正常 |  |  |
| 159001 | 货币ETF | ETF | observe_pool | 债券货币观察 | data/etf_daily/sz_159001.csv | 326 | 2026-07-03 | 正常 |  |  |
| 600519 | 贵州茅台 | STOCK | observe_pool | 个股观察 |  | 0 |  | 缺失 |  | 缺少本地 CSV |
| 300750 | 宁德时代 | STOCK | observe_pool | 个股观察 |  | 0 |  | 缺失 |  | 缺少本地 CSV |