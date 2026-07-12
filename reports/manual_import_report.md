# 手工 CSV 导入报告

- 模式：正式导入
- 预计成功：6
- 失败：15
- 数据来源：`data/manual_import/`
- 写入目录：`data/etf_daily/`
- 合并规则：日期重复时保留 `data/etf_daily/` 原有行，避免覆盖 BaoStock 近期数据。
- 正式导入：已写入 `data/etf_daily/`
- 券商 API：未使用
- 账号密码：未读取
- 真实下单：未执行
- 自动交易：未执行
- 策略逻辑：未修改

| 代码 | 名称 | group | pool | 状态 | 原行数 | 手工行数 | 重叠日期数 | 合并后行数 | 原日期范围 | 手工日期范围 | 合并后日期范围 | 目标文件 | 说明 |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 515260 |  |  |  | imported | 328 | 1 | 0 | 329 | 2025-03-03 to 2026-07-07 | 2026-07-08 to 2026-07-08 | 2025-03-03 to 2026-07-08 | `data/etf_daily/sh_515260.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 515630 |  |  |  | imported | 328 | 1 | 0 | 329 | 2025-03-03 to 2026-07-07 | 2026-07-08 to 2026-07-08 | 2025-03-03 to 2026-07-08 | `data/etf_daily/sh_515630.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 516020 |  |  |  | imported | 328 | 1 | 0 | 329 | 2025-03-03 to 2026-07-07 | 2026-07-08 to 2026-07-08 | 2025-03-03 to 2026-07-08 | `data/etf_daily/sh_516020.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 516080 |  |  |  | imported | 328 | 1 | 0 | 329 | 2025-03-03 to 2026-07-07 | 2026-07-08 to 2026-07-08 | 2025-03-03 to 2026-07-08 | `data/etf_daily/sh_516080.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 516360 |  |  |  | imported | 328 | 1 | 0 | 329 | 2025-03-03 to 2026-07-07 | 2026-07-08 to 2026-07-08 | 2025-03-03 to 2026-07-08 | `data/etf_daily/sh_516360.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 516720 |  |  |  | imported | 328 | 1 | 0 | 329 | 2025-03-03 to 2026-07-07 | 2026-07-08 to 2026-07-08 | 2025-03-03 to 2026-07-08 | `data/etf_daily/sh_516720.csv` | existing data wins on duplicate dates; no overlapping dates found |
| 516750 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_516750.csv` | manual CSV not found |
| 520550 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_520550.csv` | manual CSV not found |
| 560510 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_560510.csv` | manual CSV not found |
| 561360 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_561360.csv` | manual CSV not found |
| 561560 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_561560.csv` | manual CSV not found |
| 562500 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_562500.csv` | manual CSV not found |
| 562550 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_562550.csv` | manual CSV not found |
| 562920 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_562920.csv` | manual CSV not found |
| 563360 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_563360.csv` | manual CSV not found |
| 563800 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_563800.csv` | manual CSV not found |
| 588030 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_588030.csv` | manual CSV not found |
| 588120 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_588120.csv` | manual CSV not found |
| 588190 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_588190.csv` | manual CSV not found |
| 588220 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_588220.csv` | manual CSV not found |
| 588800 |  |  |  | failed | 0 | 0 | 0 | 0 |  to  |  to  |  to  | `data/etf_daily/sh_588800.csv` | manual CSV not found |
