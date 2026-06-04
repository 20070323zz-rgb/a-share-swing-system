# 已定规则记忆

最后更新：2026-06-02

## 项目边界

本项目只用于量化学习、公开行情研究、模拟交易和回测。

明确禁止：

- 真实券商 API。
- 真实下单。
- 自动交易。
- 保存账号、密码、验证码、cookie、token、银行卡信息。
- 融资融券、期权、杠杆、自动转账。

允许：

- 下载公开历史行情。
- 读取本地 CSV。
- 数据清洗和质量检查。
- 策略信号生成。
- 回测。
- 模拟盘记录和复盘。

## 模拟账户参数

- 初始本金：10000 元。
- 最大总仓位：7000 元。
- 最低现金：3000 元。
- 单笔最大风险：150 元。
- 最多同时持有：2 个 ETF + 1 只个股。
- 交易周期：周线波段。
- 检查频率：每天收盘后检查一次信号。
- 周复盘：每周五收盘后生成，也可以用 `--weekly` 强制生成。

## 策略规则

候选买入倾向：

- 收盘价 > MA20。
- 收盘价 > MA60。
- MA20 向上。
- 最近 20 个交易日涨幅强于沪深 300。
- 成交量温和放大。
- 不追连续暴涨后的高位标的。

卖出/风控倾向：

- ETF 跌破买入价 7%-8% 止损。
- 个股跌破买入价 8%-10% 止损。
- 跌破 MA60 清仓。
- 盈利超过 15% 后启动移动止盈。
- 盈利后从最高点回撤 8%-10% 减仓或卖出。

## 数据约定

本地行情文件放在 `data/` 目录。

文件名：

```text
data/<code>.csv
```

标准字段：

```text
date,open,high,low,close,volume
```

默认基准：

```text
510300
```

观察池来自：

```text
watchlist.csv
```

模拟成交来自：

```text
trades.csv
```

## 报告约定

每日信号：

```text
reports/daily_signal_YYYY-MM-DD.md
```

周复盘：

```text
reports/weekly_review_YYYY-MM-DD.md
```

数据日志：

```text
reports/data_update_log.md
reports/data_quality_report.md
```

回测报告：

```text
reports/backtest_result.csv
reports/backtest_summary.md
```

账户和信号记录：

```text
reports/account_status.csv
reports/signals.csv
```

## 协作方式

- 用户负责定方向、确认模拟交易、提供 ChatGPT 策略想法。
- ChatGPT 适合做策略解释、复盘分析、学习辅导和想法扩展。
- Codex 负责把想法工程化：写代码、跑数据、修 bug、生成报告。
- 如果 ChatGPT 给出重要建议，把它粘贴到 `CHATGPT_NOTES.md` 或直接发给 Codex。
