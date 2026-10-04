# 展示证据索引

[返回项目首页](../../../README.md) · [主研究案例](../daily-vs-weekly.md)

整理日期：2026-10-04。此目录保存本次展示引用的原报告与数值摘要快照。原文件按字节复制，未重写其研究结果；来源路径、SHA-256 与图表数据关系见 [source-manifest.json](source-manifest.json)。

这里提供研究阅读与证据核查资料，不包含完整实验代码、原始数据及全部执行日志，不承诺下载复现。报告中的内部路径用于说明原研究来源，并不表示相应文件已全部公开同步。

## 主案例证据链

| 阶段 | 报告 | 数值摘要 |
| --- | --- | --- |
| 含分红的四情景历史回放 | [TR-003](res_freq_tr_003_screen_2026-09-26.md) | [JSON](res_freq_tr_003_summary_2026-09-26.json) |
| 目标反复与周频确认诊断 | [PM-002A](res_freq_pm_002a_mechanism_2026-09-27.md) | [JSON](res_freq_pm_002a_summary_2026-09-27.json) |
| 三分支局部反事实 | [PM-002B](res_freq_pm_002b_pnl_attribution_2026-09-27.md) | [JSON](res_freq_pm_002b_summary_2026-09-27.json) |
| 样本内统计稳健性 | [PM-002C1](res_freq_pm_002c1_robustness_2026-09-28.md) | [JSON](res_freq_pm_002c1_summary_2026-09-28.json) |
| 前瞻协议冻结 | [OOS-001](res_freq_oos_001_freeze_2026-10-02.md) | 状态截至该报告日期 |
| 合成执行工程验收 | [OOS-ENG-001B](res_freq_oos_eng_001b_readiness_2026-10-04.md) | 合成测试，真实账户尚未启动 |

报告按研究发生的阶段保留。例如早期 TR-003 中“机制诊断未启动”是该报告当时的状态，后来由 PM-002A / B / C1 继续推进；不要将早期报告的下一步建议当作当前进度。当前整理状态见[进展与限制](../project-status.md)。

## 其他研究

[P2 风险调整动量报告](p2_risk_adjusted_momentum_robustness_2026-07-19_report.md)及[冻结决策](p2_risk_adjusted_momentum_robustness_2026-07-19_decision.json)保留不支持相对 RET20 增量优势的判断。适用范围按原报告限定。

## 图表和派生结果

| 资料 | 说明 |
| --- | --- |
| [历史研究账户权益](historical-account-equity.csv) | 从 TR-003 既有逐日结果精确选取 scenario、date、research_equity 三列；保留全部四情景 |
| [局部反事实分组统计](res_freq_pm_002b_group_stats_2026-09-27.csv) | 原研究表按字节复制 |
| [权益与回撤图](../figures/equity-and-drawdown.png) | 基础成本两组；回撤按各自历史权益最高点计算，与摘要核对 |
| [频率与成本图](../figures/frequency-and-cost.png) | TR-003 基础成本的目标事件、成交订单及假设总成本 |
| [机制与重采样图](../figures/mechanism-robustness.png) | PM-002C1 原样本中位差及自助抽样分位区间 |

图表只整理既有结果，没有新增回测、收益实验、参数搜索或策略规则。展示更新不替代原始研究归档，也不改变正式模拟账户或执行权限。
