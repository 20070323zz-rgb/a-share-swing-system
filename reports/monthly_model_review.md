# 月度模型复盘

- 检查时间：2026-07-01 23:50:06
- dry-run：no
- 模型复盘只读取本地 model_dataset.csv 与已有 ETF 池状态。
- 模型结果只用于研究，不参与当天信号，不替代人工确认。

## 已刷新研究报告
- 因子报告：/Users/dayin/Code/a-share-swing-system/reports/factor_analysis_report.md
- 模型研究报告：reports/model_research_report.md

## ETF 池质量摘要
- watchlist role 分布：{'trade_pool': 63, 'observe_pool': 15}
- 扩池候选 status 分布：{'imported': 70, 'unresolved': 21, 'failed_validation': 3}
- 扩池候选 pool 分布：{'observe_pool': 45, 'research_only': 26, 'trade_pool': 23}

## 月度检查项
- 因子 IC / Rank IC：见 reports/factor_analysis_report.md。
- 分组表现：见 reports/factor_analysis_report.md 的 group 拆分。
- ETF 池质量：关注 imported、failed_validation、unresolved 的变化。
- 参数稳定性：本轮不修改 mid_trend / short_swing 核心交易规则，只记录表现。

## 安全边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存账号、密码或 token。
- 不自动交易。
- 不修改 mid_trend / short_swing 核心交易规则。
- 所有交易相关输出仅为本地模拟盘和研究报告。