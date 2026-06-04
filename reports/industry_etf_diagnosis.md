# 行业 ETF 数据源诊断报告 2026-06-03

本报告只诊断公开行情下载可用性，不包含任何券商接口、真实下单、账号密码、验证码、token、融资融券、杠杆或自动交易功能。

## 诊断范围

本次诊断行业组 5 个 ETF：

| 代码 | 名称 | group | role | enabled |
| --- | --- | --- | --- | --- |
| 512880 | 证券ETF | 行业 | trade_pool | 1 |
| 512800 | 银行ETF | 行业 | trade_pool | 1 |
| 512010 | 医药ETF | 行业 | trade_pool | 1 |
| 512690 | 酒ETF | 行业 | trade_pool | 1 |
| 159928 | 消费ETF | 行业 | trade_pool | 1 |

## 现有日志结论

`reports/data_update_log.md` 和 `reports/watchlist_health_report.md` 显示：

- 本次行业组下载参数：`--fetch-group 行业 --batch-size 3 --sleep-seconds 5 --retry 2`
- 本次实际检查标的数：5
- 新下载成功数：0
- 本地缓存可用数：0
- 失败数：5
- 本次检查范围可用率：0.00%
- 失败原因主要为：`RemoteDisconnected`
- 5 个行业 ETF 均没有本地合格 CSV 缓存

## 单标的慢速下载诊断

逐个运行：

```bash
python3 src/main.py --fetch-data --fetch-code <code> --start-date 2025-01-01 --end-date 2026-06-02 --batch-size 1 --sleep-seconds 8 --retry 2
```

结果：

| 代码 | 名称 | 单标的是否成功 | 本地缓存 | 失败原因 | 初步判断 |
| --- | --- | --- | --- | --- | --- |
| 512880 | 证券ETF | 否 | 无 | RemoteDisconnected | 单标的仍失败，不只是批量过密 |
| 512800 | 银行ETF | 否 | 无 | RemoteDisconnected | 单标的仍失败，不只是批量过密 |
| 512010 | 医药ETF | 否 | 无 | RemoteDisconnected | 单标的仍失败，不只是批量过密 |
| 512690 | 酒ETF | 否 | 无 | RemoteDisconnected | 单标的仍失败，不只是批量过密 |
| 159928 | 消费ETF | 否 | 无 | RemoteDisconnected | 单标的仍失败，不只是批量过密 |

## AKShare 原始接口诊断

对 5 个标的直接测试：

```python
akshare.fund_etf_hist_em(
    symbol="<code>",
    period="daily",
    start_date="20250101",
    end_date="20260602",
    adjust=""
)
```

结果：

| 代码 | 名称 | AKShare 原始接口是否成功 | 原始异常 |
| --- | --- | --- | --- |
| 512880 | 证券ETF | 否 | ConnectionError / NameResolutionError，无法解析 push2his.eastmoney.com |
| 512800 | 银行ETF | 否 | ConnectionError / NameResolutionError，无法解析 push2his.eastmoney.com |
| 512010 | 医药ETF | 否 | ConnectionError / NameResolutionError，无法解析 push2his.eastmoney.com |
| 512690 | 酒ETF | 否 | ConnectionError / NameResolutionError，无法解析 push2his.eastmoney.com |
| 159928 | 消费ETF | 否 | ConnectionError / NameResolutionError，无法解析 push2his.eastmoney.com |

## 结论

- 5 个行业 ETF 单标的慢速下载均失败。
- 5 个行业 ETF 原始 AKShare 接口均失败。
- 失败不属于字段映射问题。
- 失败不属于 `watchlist.csv` 读取问题。
- 失败不属于 `enabled/type/source` 判断问题。
- 在当前运行环境中，问题集中在 AKShare 背后的东方财富公开行情源访问失败。
- 单标的慢速下载仍失败，说明这次不能简单归因于批量请求过密。

## 标的处理建议

| 代码 | 名称 | 是否建议保留 | 是否建议暂时禁用 | 是否建议替换代码 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 512880 | 证券ETF | 是 | 可考虑 | 可考虑 | 建议先保留并分时段重试；如果多日失败，再考虑 `enabled=0` 暂时禁用 |
| 512800 | 银行ETF | 是 | 可考虑 | 可考虑 | 建议先保留并分时段重试；如果多日失败，再考虑 `enabled=0` 暂时禁用 |
| 512010 | 医药ETF | 是 | 可考虑 | 可考虑 | 建议先保留并分时段重试；如果多日失败，再考虑 `enabled=0` 暂时禁用 |
| 512690 | 酒ETF | 是 | 可考虑 | 可考虑 | 建议先保留并分时段重试；如果多日失败，再考虑 `enabled=0` 暂时禁用 |
| 159928 | 消费ETF | 是 | 可考虑 | 可考虑 | 建议先保留并分时段重试；如果多日失败，再考虑 `enabled=0` 暂时禁用 |

不要自动删除任何标的。若确认某些 ETF 长期无法抓取，只建议在 `watchlist.csv` 中将 `enabled=0` 暂时禁用，由用户人工确认后执行。

## 替代 ETF proposal

以下只是候选 proposal，必须人工确认代码、流动性、跟踪指数和数据源可用性后再决定是否加入 `watchlist.csv`。

| 原分组 | 原标的 | 替代候选 | 说明 |
| --- | --- | --- | --- |
| 证券 | 512880 证券ETF | 512000 / 159841 / 159993 | 需人工确认 |
| 银行 | 512800 银行ETF | 512700 / 515020 | 需人工确认 |
| 医药 | 512010 医药ETF | 159929 / 512170 / 512660 | 需人工确认 |
| 白酒消费 | 512690 酒ETF | 可继续查找同类消费/酒类 ETF | 需人工确认 |
| 主要消费 | 159928 消费ETF | 可继续查找主要消费 ETF | 需人工确认 |

## 下一步建议

1. 不继续扩大标的池。
2. 在网络较稳定的时段，对行业 ETF 用 `--fetch-code` 单个重试。
3. 若连续多日同一标的失败，先把该标的列入“待人工确认”，不要自动改策略。
4. 如需替换 ETF，先单独测试候选代码的 AKShare 原始接口和 `src/main.py --fetch-code`。
5. 数据可用前，不把行业 ETF 纳入正式模拟盘决策。
