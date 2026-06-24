# JQData 日常主源升级与本轮补齐报告 2026-06-17 00:58:39

本报告记录本轮行情数据源改造和补齐结果。任务只涉及行情数据、报告和看板；不接券商 API，不真实下单，不读取真实账户，不保存密码/token。

## 结论

- 主源配置：JQData 已配置并可认证。
- 实际本轮正式补齐数据源：baostock
- fallback_triggered：True
- jqdata_status：PENDING_SOURCE_UPDATE
- baostock_status：FALLBACK_USED
- 新增行数：178
- ETF 正式数据文件数：183
- 最新日期分布：{'2026-06-16': 183}
- 失败数：0
- BaoStock 实际调用：178，低于 50000 上限。

## 发现的问题

1. JQData 可以登录，但本轮请求 2026-06-16 日线时未返回新行；如果系统把空返回当 OK，看板会误判数据已更新。
2. 旧逻辑中 dry-run 会覆盖正式 data_update_status / data_source_status，导致看板可能显示验证结果而不是真实补齐结果。
3. BaoStock fallback 全池补齐耗时较长，但最终可完成；前端和自动化必须以状态文件落盘为准。

## 已完成修复

- update_etf_data.py 默认 source=auto，优先 JQData，失败或 pending 时 fallback BaoStock。
- 新增 JQData source 和 source router，账号只从环境变量或本地 .env 读取。
- JQData 登录输出已静默，避免第三方库把敏感信息写入日志。
- JQData 空返回标记为 PENDING_SOURCE_UPDATE，不再误报 OK。
- daily_close dry-run 改为写 reports/data_update_status.dryrun.json，并恢复正式状态文件，避免污染看板。
- App 一键日更/补齐任务接入 source auto。
- dashboard_data.json、dashboard/index.html、React App 均同步显示主源、实际源、fallback 状态。

## 本轮正式补齐结果

- 请求区间：2026-06-16 到 2026-06-16。
- Universe：183 个 ETF CSV。
- 实际新增：178 行。
- 结果：所有正式 ETF 文件最新日期均为 2026-06-16。
- 失败 ETF：none。

## 安全边界

- 未接券商 API。
- 未真实下单。
- 未读取真实账户。
- 未保存或输出 JQData 密码/token。
- 未修改交易策略核心逻辑。
- 正式数据合并保持本地原行优先。
