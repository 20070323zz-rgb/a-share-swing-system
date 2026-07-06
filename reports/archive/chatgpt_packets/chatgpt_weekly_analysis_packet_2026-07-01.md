# ChatGPT / Main 分析包：A 股 ETF 双周期模拟盘周报

> 本报告用于研究分析，不是交易指令。  
> 安全边界：不接券商 API、不真实下单、不读取真实账户、不保存密码/token。  
> adjusted preview / shadow / profit protection / high_beta / broad base balance 均为观察层，不接执行层。

---

# 一、本周核心结论

- 正式模拟仓总资产 10126.81，总盈亏 126.81，总收益率 1.27%。
- 当前盈亏主要来自未实现浮盈/浮亏，不足以证明策略成熟。
- 当前持仓结构：宽基占比 0.00%，科技成长 54.42%，金融地产 45.58%。
- REVIEW/REDUCE 观察：REDUCE_CANDIDATE=1，REVIEW_2=0。
- 浮盈保护：PROFIT_WATCH=2，PROFIT_LOCK_CANDIDATE=0，不自动止盈。
- high_beta：状态 HB_WATCH，high_beta 占持仓 19.16%，不自动减仓。
- 宽基平衡：BROAD_BASE_MISSING / THEME_CONCENTRATED，候选 588000 科创50ETF、510500 中证500ETF、510180 上证180ETF。
- shadow 模型 evidence_level=insufficient，ready_for_preview=False，ready_for_execution=False。
- 本周最需要判断：512800 是否继续 REDUCE_CANDIDATE、515000 是否需要浮盈保护升级、512880 high_beta 是否升高、宽基候选是否继续观察。
- 数据更新状态为 updated，需要确认最新数据是否足够。

---

# 二、数据与系统状态

- ETF 数据文件数量：183
- 最新数据日：2026-07-01
- 本周数据更新状态：updated
- 数据健康：updated
- 估值日期：2026-07-01
- 价格警告数量：0
- dashboard 更新时间：2026-07-01 23:53:21
- App / dashboard 是否同步：是

---

# 三、正式模拟仓账户

- 当前现金：7058.11
- 当前持仓市值：3068.70
- 当前总资产：10126.81
- 总盈亏：126.81
- 总收益率：1.27%
- 已实现盈亏：-73.59
- 未实现盈亏：200.40
- 最大回撤：-1.03%
- 交易次数：7
- 胜率：50.00%
- 原始权益曲线条数：16
- 回填权益曲线条数：15
- 当前盈利来源判断：当前盈亏主要来自未实现浮盈/浮亏，不足以证明策略成熟。

---

# 四、当前持仓与观察状态

| 代码 | 名称 | 组别 | 类型 | 市值 | 权重 | mid_trend | short_swing | review_state | profit_protection_state | high_beta_risk_state | recommended_review_action | 是否允许执行 |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 512800 | 银行ETF | 金融地产 | sector | 810.70 | 8.11% | BUY | BUY | REDUCE_CANDIDATE | NO_PROFIT | N/A | 减仓候选观察：条件叠加，但不触发自动交易。 | false |
| 515000 | 科技ETF | 科技成长 | unknown | 1670.00 | 16.70% | BUY | BUY | HOLD | PROFIT_WATCH | N/A | 继续持有；跟踪浮盈回撤和 rank_score 是否连续下降。 | false |
| 512880 | 证券ETF | 金融地产 | high_beta | 588.00 | 5.88% | BUY | BUY | HOLD | PROFIT_WATCH | HB_WATCH | 继续持有；未触发分层复核条件。 | false |

---

# 五、本周交易记录

- 本周无模拟交易。

- 是否真实交易：否。

---

# 六、BUY Ranking 与 adjusted preview

## 原始 BUY ranking Top 10

| rank | code | name | group | mid | short | rank_score |
| ---: | --- | --- | --- | --- | --- | ---: |
| 1 | 512880 | 证券ETF | 金融地产 | BUY | BUY | 93.9393 |
| 2 | 512010 | 医药ETF | 消费医药 | BUY | BUY | 93.0473 |
| 3 | 515000 | 科技ETF | 科技成长 | BUY | BUY | 91.9862 |
| 4 | 159819 | 人工智能ETF | 科技成长 | BUY | BUY | 91.3092 |
| 5 | 515070 | AIETF | 科技成长 | BUY | BUY | 91.2545 |
| 6 | 512070 | 非银ETF | 金融地产 | BUY | BUY | 90.6345 |
| 7 | 159929 | 医药ETF | 消费医药 | BUY | BUY | 86.5755 |
| 8 | 588000 | 科创50ETF | 宽基 | WATCH | BUY | 79.0792 |
| 9 | 512170 | 医疗ETF | 消费医药 | WATCH | BUY | 73.8682 |
| 10 | 159869 | 游戏ETF | 科技成长 | WATCH | BUY | 66.8258 |

## adjusted preview Top 10

| adjusted_rank | code | name | group | original_score | adjusted_score | execution_status |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 1 | 512010 | 医药ETF | 消费医药 | 93.0473 | 93.0473 | preview_only_not_executed |
| 2 | 515000 | 科技ETF | 科技成长 | 91.9862 | 89.9862 | preview_only_not_executed |
| 3 | 512880 | 证券ETF | 金融地产 | 93.9393 | 89.9393 | preview_only_not_executed |
| 4 | 159819 | 人工智能ETF | 科技成长 | 91.3092 | 89.3092 | preview_only_not_executed |
| 5 | 515070 | AIETF | 科技成长 | 91.2545 | 89.2545 | preview_only_not_executed |
| 6 | 512070 | 非银ETF | 金融地产 | 90.6345 | 86.6345 | preview_only_not_executed |
| 7 | 159929 | 医药ETF | 消费医药 | 86.5755 | 86.5755 | preview_only_not_executed |
| 8 | 588000 | 科创50ETF | 宽基 | 79.0792 | 82.0792 | preview_only_not_executed |
| 9 | 512170 | 医疗ETF | 消费医药 | 73.8682 | 73.8682 | preview_only_not_executed |
| 10 | 159869 | 游戏ETF | 科技成长 | 66.8258 | 64.8258 | preview_only_not_executed |

- preview_only_not_executed 数量：11
- 是否过度集中在主题/行业：THEME_CONCENTRATED
- 宽基/准宽基候选：588000 科创50ETF、510500 中证500ETF、510180 上证180ETF、512100 中证1000ETF、510050 上证50ETF
- 是否接执行层：否。

---

# 七、卖出复核与减仓候选

- REVIEW_1：无
- REVIEW_2：无
- REDUCE_CANDIDATE：512800 银行ETF
- REDUCE：无
- SELL：无
- REDUCE_CANDIDATE 只是观察状态，不自动卖出。

---

# 八、浮盈保护 Preview

- PROFIT_WATCH：515000 科技ETF、512880 证券ETF
- PROFIT_PROTECTION_REVIEW：无
- PROFIT_LOCK_CANDIDATE：无
- 515000 当前状态：PROFIT_WATCH
- 515000 当前浮盈：243.57
- 515000 峰值浮盈：285.57
- 515000 峰值回撤：42.00 / 14.71%
- 是否自动止盈：否。

---

# 九、high_beta 风险观察

- high_beta 持仓数量：1
- high_beta 占总资产比例：5.81%
- high_beta 占持仓市值比例：19.16%
- 金融地产组暴露：总资产 13.81% / 持仓 45.58%
- 512880 当前状态：HB_WATCH
- 是否 HB_CAUTION / HB_ELEVATED：否
- 是否自动减仓：否。

---

# 十、宽基平衡 Preview

- 当前宽基占比：0.00%
- 行业/主题占比：100.00%
- 金融地产组占比：45.58%
- 科技成长组占比：54.42%
- high_beta 占比：19.16%
- Top 宽基候选：588000 科创50ETF、510500 中证500ETF、510180 上证180ETF、512100 中证1000ETF、510050 上证50ETF
- 588000 状态：WATCH/BUY，rank=1，raw=79.0792，adjusted=82.0792
- 159915 状态：WATCH/N/A，rank=6，raw=66.6349，adjusted=66.6349
- 510300 状态：WATCH/N/A，rank=9，raw=0，adjusted=0
- 500 元 hypothetic preview 改善：宽基到 14.01%，金融地产到 39.19%，科技成长到 46.80%，high_beta 到 16.48%。
- 是否自动买入：否。

---

# 十一、Shadow / 研究模型状态

- 当前阶段：Shadow Observation Period
- evidence_level：insufficient
- ready_for_preview：false
- ready_for_execution：false
- persistence_breakout_v2 最新 selected：1
- missed opportunity 数量：49
- matured forward return 样本：0
- 是否允许放宽过滤：false
- 是否允许接执行层：false
- 推荐动作：continue_observation

---

# 十二、系统口径与风险提示

- 估值口径一致性：PASS
- paper_performance vs portfolio_exposure 差异：0.00
- 是否有价格警告：否
- 是否有数据健康问题：updated
- dashboard 是否可能误导：当前已分离正式模拟仓、观察层、shadow 和回填估算；仍需人工理解观察层不等于执行层。
- 正式模拟仓与研究预览是否分离展示：是。

---

# 十三、需要 ChatGPT / Main 判断的问题

## A. 正式模拟仓

1. 当前持仓是否继续观察？
2. 是否有持仓需要升级复核？
3. 512800 是否仍为 REDUCE_CANDIDATE？
4. 515000 是否需要进入浮盈保护复核？
5. 512880 high_beta 风险是否升高？

## B. 组合结构

1. 当前是否过度主题集中？
2. 是否应继续观察宽基平衡候选？
3. 588000 / 159915 / 510300 谁更值得观察？
4. 是否应维持 adjusted preview 不接执行层？

## C. 模型研究

1. shadow 模型是否仍 evidence insufficient？
2. 是否有足够 forward return 样本？
3. 是否可以放宽过滤？
4. 是否可以进入 preview？
5. 是否可以接 paper_trade_engine？

## D. 系统工程

1. 是否还有口径差异？
2. 是否需要优化 App 展示？
3. 是否需要更新报告字段？
4. 是否需要加入新的观察指标？


---

# 十四、禁止误读

- 本项目是模拟盘和量化学习系统。
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不保存密码/token。
- adjusted preview 不接执行层。
- shadow 不接执行层。
- REDUCE_CANDIDATE 不是减仓指令。
- PROFIT_LOCK_CANDIDATE 不是止盈指令。
- high_beta 风险观察不是卖出指令。
- 当前小幅盈利不能证明策略成熟。

## 缺失来源文件

- reports/ranking_report.csv
- reports/latest_ranking.csv
- reports/adjusted_preview.csv
