# 代码阅读导航

[返回项目首页](../../README.md) · [关键术语](glossary.md) · [数据与方法](data-and-methods.md)

导航更新：2026-10-05。本页按 GitHub 已提交代码核对文件和函数，只介绍阅读路径，不要求运行程序。公开代码包含较早系统实现；最新三 ETF 研究证据与本地近期工程更新分别整理，完整代码同步及复现入口暂缓。

## 先看一条较短的路径

建议先沿着“本地行情 → 指标 → 信号 → 报告”阅读，理解每一层的输入和输出，再查看研究特征、回测及界面。

| 顺序 | 文件 / 主要入口 | 阅读重点 |
| --- | --- | --- |
| 1 | [src/data_loader.py](../../src/data_loader.py)：`load_price_data`、`find_price_file` | 一只标的的 CSV 如何定位、读取并转换成行情表；名单与模拟记录如何读取 |
| 2 | [src/data_health.py](../../src/data_health.py)：`check_price_dataframe`、`write_data_health_report` | 日期、缺失、重复和价格字段怎样检查；问题如何形成报告 |
| 3 | [src/indicators.py](../../src/indicators.py)：`add_indicators`、`latest_on_or_before` | 行情表如何加入指标，指定日期怎样选择可用记录 |
| 4 | [src/signal_engine.py](../../src/signal_engine.py)：`make_signal`、`Signal` | 较早双周期规则怎样形成 BUY / WATCH / HOLD / SELL 及原因 |
| 5 | [src/reporting.py](../../src/reporting.py)：`save_signals`、`write_daily_report`、`write_brief_report` | 信号和账户信息怎样整理成表格与报告 |
| 6 | [src/main.py](../../src/main.py)：`main` | 上述模块怎样被串联；可结合导入列表回看各模块职责 |

这条路径帮助理解原系统结构。首页三 ETF 案例中的 TR20、Top2 与冻结执行约定，以[主案例](daily-vs-weekly.md)及其研究证据为准。

## 再看研究特征与验证

| 文件 / 主要入口 | 可以了解什么 | 留意什么 |
| --- | --- | --- |
| [src/features.py](../../src/features.py)：`compute_features` | 从行情计算收益、均线、波动及相对基准特征 | 这些是公开版本的研究特征，不等于最新案例的全部信号规则 |
| [src/labels.py](../../src/labels.py)：`add_future_return_labels` | 未来收益标签及横截面排名如何生成 | 标签用于事后研究评价，不能进入当日信号或评分 |
| [src/factor_analysis.py](../../src/factor_analysis.py)：`write_factor_analysis_report` | 特征与标签如何形成相关性和分组结果 | 历史统计需要结合样本、成本与比较对象解释 |
| [src/backtest.py](../../src/backtest.py)：`run_backtest` | 较早单标的回测怎样遍历行情并记录交易 | 它与当前三 ETF 频率研究回放属于不同入口，不混用结论 |

阅读时可以围绕同一组问题：函数接收什么、返回什么、是否写文件、使用的日期是什么、是否引用了之后才可获得的数据。

## 最后看数据来源与界面

| 文件 | 用途 |
| --- | --- |
| [src/data_fetcher.py](../../src/data_fetcher.py) | 较早行情获取、字段标准化、质量检查及更新报告组织；数据源说明按该公开版本理解 |
| [dashboard/build_dashboard.py](../../dashboard/build_dashboard.py) | 读取已有材料、构建快照并生成静态看板；可从 `build_snapshot`、`render_html` 入手 |
| [app/backend/main.py](../../app/backend/main.py) | 数据、信号、账户及任务接口的组织 |
| [app/backend/readers.py](../../app/backend/readers.py) | 后端怎样读取本地报告与快照 |
| [app/frontend/src/App.jsx](../../app/frontend/src/App.jsx) | 前端页面如何组织，可继续查看同目录的 `pages/` 与 `components/` |

## 最新研究材料怎样阅读

先读[主案例](daily-vs-weekly.md)，再按[证据索引](evidence/README.md)中的 TR-003 → PM-002A → PM-002B → PM-002C1 顺序核对历史比较、描述诊断、局部反事实和样本内检查。最后查看前瞻协议与合成工程验收。

原报告中的内部路径用于追溯本地研究来源，相关最新实现尚未完整同步到公开仓库。本导航仅链接当前已公开的代码，不将合成验收描述为真实前瞻账户表现。
