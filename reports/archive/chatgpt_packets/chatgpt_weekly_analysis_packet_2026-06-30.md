# ChatGPT / Main 分析包：A 股 ETF 双周期模拟盘周报

> 本报告用于研究分析，不是交易指令。
> 安全边界：不接券商 API、不真实下单、不读取真实账户、不保存密码/token。
> adjusted preview / shadow / profit protection / high_beta / broad base balance 均为观察层，不接执行层。

---

# 一、本周核心结论

- 正式模拟仓总资产 10140.51，总盈亏 140.51，总收益率 1.41%。
- 当前盈亏主要来自未实现浮盈/浮亏，不足以证明策略成熟。
- 当前持仓结构：宽基占比 0.00%，科技成长 55.54%，金融地产 44.46%。
- REVIEW/REDUCE 观察：REDUCE_CANDIDATE=1，REVIEW_2=2。
- 浮盈保护：PROFIT_WATCH=0，PROFIT_LOCK_CANDIDATE=0，不自动止盈。
- high_beta：状态 HB_WATCH，high_beta 占持仓 18.26%，不自动减仓。
- 宽基平衡：BROAD_BASE_MISSING / THEME_CONCENTRATED，候选 159901 深100ETF、510500 中证500ETF、512100 中证1000ETF。
- shadow 模型 evidence_level=insufficient，ready_for_preview=False，ready_for_execution=False。
- 本周最需要判断：512800 是否继续 REDUCE_CANDIDATE、515000 是否需要浮盈保护升级、512880 high_beta 是否升高、宽基候选是否继续观察。
- 数据更新状态为 up_to_date，需要确认最新数据是否足够。

---

# 二、数据与系统状态

- ETF 数据文件数量：183
- 最新数据日：2026-06-30
- 本周数据更新状态：up_to_date
- 数据健康：up_to_date
- 估值日期：2026-06-30
- 价格警告数量：0
- dashboard 更新时间：2026-06-30 18:20:48
- App / dashboard 是否同步：是

---

# 三、正式模拟仓账户

- 当前现金：7058.11
- 当前持仓市值：3082.40
- 当前总资产：10140.51
- 总盈亏：140.51
- 总收益率：1.41%
- 已实现盈亏：-73.59
- 未实现盈亏：214.10
- 最大回撤：-1.03%
- 交易次数：7
- 胜率：50.00%
- 原始权益曲线条数：15
- 回填权益曲线条数：15
- 当前盈利来源判断：当前盈亏主要来自未实现浮盈/浮亏，不足以证明策略成熟。

---

# 四、当前持仓与观察状态

| 代码 | 名称 | 组别 | 类型 | 市值 | 权重 | mid_trend | short_swing | review_state | profit_protection_state | high_beta_risk_state | recommended_review_action | 是否允许执行 |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 512800 | 银行ETF | 金融地产 | sector | 807.40 | 8.07% | BUY | BUY | REDUCE_CANDIDATE | NO_PROFIT | N/A | 减仓候选观察：条件叠加，但不触发自动交易。 | false |
| 515000 | 科技ETF | 科技成长 | unknown | 1712.00 | 17.12% | BUY | BUY | REVIEW_2 | PROFIT_PROTECTION_REVIEW | N/A | 重点复核：禁止加仓，次日继续观察。 | false |
| 512880 | 证券ETF | 金融地产 | high_beta | 563.00 | 5.63% | BUY | BUY | REVIEW_2 | NO_PROFIT | HB_CAUTION | 重点复核：禁止加仓，次日继续观察。 | false |

---

# 五、本周交易记录

- 本周无模拟交易。

- 是否真实交易：否。

---

# 六、BUY Ranking 与 adjusted preview

## 原始 BUY ranking Top 10

| rank | code | name | group | mid | short | rank_score |
| ---: | --- | --- | --- | --- | --- | ---: |
| 1 | 515070 | AIETF | 科技成长 | BUY | BUY | 91.6195 |
| 2 | 159819 | 人工智能ETF | 科技成长 | BUY | BUY | 91.1866 |
| 3 | 512880 | 证券ETF | 金融地产 | BUY | BUY | 89.5771 |
| 4 | 159901 | 深100ETF | 宽基 | BUY | BUY | 88.3903 |
| 5 | 515880 | 证券公司ETF | 金融地产 | BUY | BUY | 88.3333 |
| 6 | 515050 | 5GETF | 科技成长 | WATCH | BUY | 74.3727 |
| 7 | 512010 | 医药ETF | 消费医药 | WATCH | BUY | 73.6436 |
| 8 | 512070 | 非银ETF | 金融地产 | BUY | WATCH | 67.8455 |
| 9 | 512170 | 医疗ETF | 消费医药 | WATCH | BUY | 65.8922 |
| 10 | 159929 | 医药ETF | 消费医药 | WATCH | BUY | 65.5805 |

## adjusted preview Top 10

| adjusted_rank | code | name | group | original_score | adjusted_score | execution_status |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 1 | 159901 | 深100ETF | 宽基 | 88.3903 | 91.3903 | preview_only_not_executed |
| 2 | 515070 | AIETF | 科技成长 | 91.6195 | 89.6195 | preview_only_not_executed |
| 3 | 159819 | 人工智能ETF | 科技成长 | 91.1866 | 89.1866 | preview_only_not_executed |
| 4 | 512880 | 证券ETF | 金融地产 | 89.5771 | 85.5771 | preview_only_not_executed |
| 5 | 515880 | 证券公司ETF | 金融地产 | 88.3333 | 81.3333 | preview_only_not_executed |
| 6 | 512010 | 医药ETF | 消费医药 | 73.6436 | 73.6436 | preview_only_not_executed |
| 7 | 515050 | 5GETF | 科技成长 | 74.3727 | 69.3727 | preview_only_not_executed |
| 8 | 512170 | 医疗ETF | 消费医药 | 65.8922 | 65.8922 | preview_only_not_executed |
| 9 | 159929 | 医药ETF | 消费医药 | 65.5805 | 65.5805 | preview_only_not_executed |
| 10 | 512070 | 非银ETF | 金融地产 | 67.8455 | 63.8455 | preview_only_not_executed |

- preview_only_not_executed 数量：11
- 是否过度集中在主题/行业：THEME_CONCENTRATED
- 宽基/准宽基候选：159901 深100ETF、510500 中证500ETF、512100 中证1000ETF、159915 创业板ETF、510300 沪深300ETF
- 是否接执行层：否。

---

# 七、卖出复核与减仓候选

- REVIEW_1：无
- REVIEW_2：515000 科技ETF、512880 证券ETF
- REDUCE_CANDIDATE：512800 银行ETF
- REDUCE：无
- SELL：无
- REDUCE_CANDIDATE 只是观察状态，不自动卖出。

---

# 八、浮盈保护 Preview

- PROFIT_WATCH：无
- PROFIT_PROTECTION_REVIEW：515000 科技ETF
- PROFIT_LOCK_CANDIDATE：无
- 515000 当前状态：PROFIT_PROTECTION_REVIEW
- 515000 当前浮盈：285.57
- 515000 峰值浮盈：285.57
- 515000 峰值回撤：0.00 / 0.00%
- 是否自动止盈：否。

---

# 九、high_beta 风险观察

- high_beta 持仓数量：1
- high_beta 占总资产比例：5.55%
- high_beta 占持仓市值比例：18.26%
- 金融地产组暴露：总资产 13.51% / 持仓 44.46%
- 512880 当前状态：HB_CAUTION
- 是否 HB_CAUTION / HB_ELEVATED：是
- 是否自动减仓：否。

---

# 十、宽基平衡 Preview

- 当前宽基占比：0.00%
- 行业/主题占比：100.00%
- 金融地产组占比：44.46%
- 科技成长组占比：55.54%
- high_beta 占比：18.26%
- Top 宽基候选：159901 深100ETF、510500 中证500ETF、512100 中证1000ETF、159915 创业板ETF、510300 沪深300ETF
- 588000 状态：WATCH/N/A，rank=9，raw=65.4032，adjusted=65.4032
- 159915 状态：WATCH/WATCH，rank=4，raw=74.8952，adjusted=74.8952
- 510300 状态：WATCH/N/A，rank=5，raw=70.9905，adjusted=70.9905
- 500 元 hypothetic preview 改善：宽基到 13.96%，金融地产到 38.25%，科技成长到 47.79%，high_beta 到 15.72%。
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
- 是否有数据健康问题：up_to_date
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
