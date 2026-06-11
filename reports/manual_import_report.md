# 手工 CSV 导入报告

- 模式：dry-run
- 预计成功：26
- 失败：50
- 数据来源：`data/manual_import/`
- 写入目录：`data/etf_daily/`
- 合并规则：日期重复时保留 `data/etf_daily/` 原有行，避免覆盖 BaoStock 近期数据。
- dry-run：不写入 `data/etf_daily/`
- 券商 API：未使用
- 账号密码：未读取
- 真实下单：未执行
- 自动交易：未执行
- 策略逻辑：未修改

| 代码 | 名称 | group | pool | 状态 | 原行数 | 手工行数 | 重叠日期数 | 合并后行数 | 原日期范围 | 手工日期范围 | 合并后日期范围 | 目标文件 | 说明 |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 510300 | 沪深300ETF | 宽基 | trade_pool | dry_run_ok | 1067 | 969 | 969 | 1067 | 2022-01-04 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_510300.csv` | existing data wins on duplicate dates |
| 510500 | 中证500ETF | 宽基 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_510500.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 512100 | 中证1000ETF | 宽基 | trade_pool | dry_run_ok | 98 | 968 | 0 | 1066 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_512100.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 159915 | 创业板ETF | 宽基 | trade_pool | dry_run_ok | 1067 | 969 | 969 | 1067 | 2022-01-04 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sz_159915.csv` | existing data wins on duplicate dates |
| 588000 | 科创50ETF | 宽基 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_588000.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 510050 | 上证50ETF | 宽基 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_510050.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 510180 | 上证180ETF | 宽基 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_510180.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 159901 | 深100ETF | 宽基 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sz_159901.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 159949 | 创业板50ETF | 宽基 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sz_159949.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 588080 | 科创创业50ETF | 宽基 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_588080.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 512880 | 证券ETF | 金融地产 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_512880.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 512800 | 银行ETF | 金融地产 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_512800.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 512200 | 房地产ETF | 金融地产 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_512200.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 510230 | 金融ETF | 金融地产 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_510230.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 159940 | 金融ETF | 金融地产 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sz_159940.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 512070 | 非银ETF | 金融地产 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_512070.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 515880 | 证券公司ETF | 金融地产 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_515880.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 512010 | 医药ETF | 消费医药 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_512010.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 159929 | 医药ETF | 消费医药 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sz_159929.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 512170 | 医疗ETF | 消费医药 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_512170.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 512690 | 酒ETF | 消费医药 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_512690.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 159928 | 消费ETF | 消费医药 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sz_159928.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 515650 | 消费50ETF | 消费医药 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_515650.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 159996 | 家电ETF | 消费医药 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159996.csv` | manual CSV not found |
| 515170 | 食品饮料ETF | 消费医药 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_515170.csv` | manual CSV not found |
| 159736 | 食品ETF | 消费医药 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159736.csv` | manual CSV not found |
| 159766 | 旅游ETF | 消费医药 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sz_159766.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 516110 | 汽车ETF | 消费医药 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_516110.csv` | manual CSV not found |
| 512480 | 半导体ETF | 科技成长 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_512480.csv` | manual CSV not found |
| 512760 | 芯片ETF | 科技成长 | trade_pool | dry_run_ok | 98 | 969 | 0 | 1067 | 2026-01-05 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_512760.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 159995 | 芯片ETF | 科技成长 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159995.csv` | manual CSV not found |
| 588200 | 科创芯片ETF | 科技成长 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_588200.csv` | manual CSV not found |
| 515050 | 5GETF | 科技成长 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_515050.csv` | manual CSV not found |
| 515000 | 科技ETF | 科技成长 | trade_pool | dry_run_ok | 1067 | 969 | 969 | 1067 | 2022-01-04 to 2026-06-03 | 2022-01-04 to 2025-12-31 | 2022-01-04 to 2026-06-03 | `data/etf_daily/sh_515000.csv` | existing data wins on duplicate dates |
| 515230 | 软件ETF | 科技成长 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_515230.csv` | manual CSV not found |
| 159819 | 人工智能ETF | 科技成长 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159819.csv` | manual CSV not found |
| 515070 | AIETF | 科技成长 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_515070.csv` | manual CSV not found |
| 159869 | 游戏ETF | 科技成长 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159869.csv` | manual CSV not found |
| 516510 | 云计算ETF | 科技成长 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_516510.csv` | manual CSV not found |
| 512980 | 传媒ETF | 科技成长 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_512980.csv` | manual CSV not found |
| 515790 | 光伏ETF | 新能源制造 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_515790.csv` | manual CSV not found |
| 159857 | 光伏ETF | 新能源制造 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159857.csv` | manual CSV not found |
| 516160 | 新能源ETF | 新能源制造 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_516160.csv` | manual CSV not found |
| 515700 | 新能源车ETF | 新能源制造 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_515700.csv` | manual CSV not found |
| 159755 | 电池ETF | 新能源制造 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159755.csv` | manual CSV not found |
| 516390 | 新能源汽车ETF | 新能源制造 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_516390.csv` | manual CSV not found |
| 516800 | 智能制造ETF | 新能源制造 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_516800.csv` | manual CSV not found |
| 512660 | 军工ETF | 新能源制造 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_512660.csv` | manual CSV not found |
| 512670 | 国防ETF | 新能源制造 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_512670.csv` | manual CSV not found |
| 159806 | 新能源车电池ETF | 新能源制造 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159806.csv` | manual CSV not found |
| 512400 | 有色ETF | 周期资源 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_512400.csv` | manual CSV not found |
| 516780 | 稀土ETF | 周期资源 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_516780.csv` | manual CSV not found |
| 515220 | 煤炭ETF | 周期资源 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_515220.csv` | manual CSV not found |
| 159930 | 能源ETF | 周期资源 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159930.csv` | manual CSV not found |
| 510410 | 资源ETF | 周期资源 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_510410.csv` | manual CSV not found |
| 159865 | 养殖ETF | 周期资源 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159865.csv` | manual CSV not found |
| 159825 | 农业ETF | 周期资源 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159825.csv` | manual CSV not found |
| 159876 | 有色金属ETF | 周期资源 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159876.csv` | manual CSV not found |
| 510880 | 红利ETF | 防御风格 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_510880.csv` | manual CSV not found |
| 512890 | 红利低波ETF | 防御风格 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_512890.csv` | manual CSV not found |
| 515080 | 中证红利ETF | 防御风格 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_515080.csv` | manual CSV not found |
| 159905 | 深红利ETF | 防御风格 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159905.csv` | manual CSV not found |
| 518880 | 黄金ETF | 防御风格 | trade_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_518880.csv` | manual CSV not found |
| 513500 | 标普500ETF | QDII观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_513500.csv` | manual CSV not found |
| 513100 | 纳指ETF | QDII观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_513100.csv` | manual CSV not found |
| 513180 | 恒生科技ETF | QDII观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_513180.csv` | manual CSV not found |
| 159920 | 恒生ETF | QDII观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159920.csv` | manual CSV not found |
| 513050 | 中概互联网ETF | QDII观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_513050.csv` | manual CSV not found |
| 513060 | 恒生医疗ETF | QDII观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_513060.csv` | manual CSV not found |
| 159941 | 纳指ETF | QDII观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159941.csv` | manual CSV not found |
| 511010 | 国债ETF | 债券货币观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_511010.csv` | manual CSV not found |
| 511260 | 十年国债ETF | 债券货币观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_511260.csv` | manual CSV not found |
| 511880 | 银华日利ETF | 债券货币观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_511880.csv` | manual CSV not found |
| 511990 | 华宝添益ETF | 债券货币观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_511990.csv` | manual CSV not found |
| 511360 | 短融ETF | 债券货币观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_511360.csv` | manual CSV not found |
| 159001 | 货币ETF | 债券货币观察 | observe_pool | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sz_159001.csv` | manual CSV not found |
