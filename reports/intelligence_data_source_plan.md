# 情报数据抓取规划 2026-06-21 20:14:02

本规划只用于研究层，不接入正式交易执行。

## 数据类型
| 类型 | 可能来源 | 初期用途 | 风险 |
| --- | --- | --- | --- |
| 行业新闻 | AKShare/东方财富/财联社/官方媒体 | 解释层、风险提醒 | 噪声、重复、滞后 |
| 政策事件 | 交易所/证监会/部委官网/新闻源 | 事件标记、人工复核 | 发布时间和可得时间错配 |
| 资金流/成交热度 | AKShare/Tushare/公开数据 | 风险过滤、拥挤度观察 | 接口稳定性和口径变化 |
| ETF 溢价/QDII 信息 | 交易所/基金公告/公开行情 | QDII 自动交易禁用或降权 | 缺少实时溢价易误判 |
| 主题关键词 | 本地关键词库 + 新闻标题 | 主题热度衰减研究 | 小作文和追涨风险 |

## 初期接入原则
- 先做 explanation/risk_filter，不做 BUY 主因子。
- 每条情报必须记录 `publish_time`、`fetch_time`、`available_date`、`source`、`url/title/hash`。
- 同一标题/正文 hash 去重，低可信来源降权。
- 收盘后生成的信号只能使用当时已可得的信息。
- 对主题 ETF 只生成 `positive / neutral / negative / noisy / event_risk` 标签。

## 推荐落地顺序
1. 建立本地 `data/intelligence_staging/`，只存研究样本。
2. 用 AKShare/Tushare 做低频接口可用性测试。
3. 按 ETF group 维护关键词映射，不直接驱动交易。
4. 在 dashboard 展示情报标签和风险，不改 paper_trade_engine。
5. 至少积累 1-3 个月 shadow tracking 后再评估是否降权接入。