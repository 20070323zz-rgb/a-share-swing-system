# ChatGPT / Main 分析包：A 股 ETF 双周期模拟盘周报

> 本报告用于研究分析，不是交易指令。
> 安全边界：不接券商 API、不真实下单、不读取真实账户、不保存密码/token。
> adjusted preview / shadow / profit protection / high_beta / broad base balance 均为观察层，不接执行层。

---

# 一、本周核心结论

- 正式模拟仓总资产 10619.84，总盈亏 619.84，总收益率 6.20%。
- 当前盈亏主要来自未实现浮盈/浮亏，不足以证明策略成熟。
- 当前持仓结构：宽基占比 0.00%，科技成长 52.49%，金融地产 47.51%。
- REVIEW/REDUCE 观察：REDUCE_CANDIDATE=1，REVIEW_2=1。
- 浮盈保护：PROFIT_WATCH=0，PROFIT_LOCK_CANDIDATE=1，不自动止盈。
- high_beta：状态 HB_WATCH，high_beta 占持仓 19.61%，不自动减仓。
- 宽基平衡：BROAD_BASE_MISSING / THEME_CONCENTRATED，候选 588000 科创50ETF、510180 上证180ETF、510500 中证500ETF。
- shadow 模型 evidence_level=insufficient，ready_for_preview=False，ready_for_execution=False。
- 本周最需要判断：512800 是否继续 REDUCE_CANDIDATE、515000 是否需要浮盈保护升级、512880 high_beta 是否升高、宽基候选是否继续观察。
- 数据更新状态为 updated，需要确认最新数据是否足够。

---

# 二、数据与系统状态

- ETF 数据文件数量：183
- 最新数据日：2026-07-09
- 本周数据更新状态：updated
- 数据健康：updated
- 估值日期：2026-07-09
- 价格警告数量：0
- dashboard 更新时间：2026-07-10 16:28:13
- App / dashboard 是否同步：是

---

# 三、正式模拟仓账户

- 当前现金：7608.44
- 当前持仓市值：3011.40
- 当前总资产：10619.84
- 总盈亏：619.84
- 总收益率：6.20%
- 已实现盈亏：-133.28
- 未实现盈亏：185.15
- 最大回撤：-1.68%
- 交易次数：11
- 胜率：25.00%
- 原始权益曲线条数：22
- 回填权益曲线条数：29
- 当前盈利来源判断：当前盈亏主要来自未实现浮盈/浮亏，不足以证明策略成熟。

---

# 四、当前持仓与观察状态

| 代码 | 名称 | 组别 | 类型 | 市值 | 权重 | mid_trend | short_swing | review_state | profit_protection_state | high_beta_risk_state | recommended_review_action | 是否允许执行 |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 515000 | 科技ETF | 科技成长 | unknown | 1622.00 | 16.22% | BUY | WATCH | REVIEW_2 | PROFIT_LOCK_CANDIDATE | N/A | 重点复核：禁止加仓，次日继续观察。 | false |
| 516510 | 云计算ETF | 科技成长 | theme | 1263.50 | 12.63% | BUY | BUY | N/A | N/A | N/A | HOLD | false |
| 159929 | 医药ETF | 消费医药 | sector | 125.90 | 1.26% | BUY | BUY | N/A | N/A | N/A | HOLD | false |

---

# 五、本周交易记录

| 日期 | 代码 | 名称 | 动作 | 金额 | 原因 | 本地模拟 | 真实交易 |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| 2026-07-09 | 512880 | 证券ETF | SELL | 555.33 | REDUCE two consecutive days | 是 | 否 |
| 2026-07-10 | 512800 | 银行ETF | SELL | 836.85 | max_holding_days reached without signal recovery | 是 | 否 |
| 2026-07-10 | 516510 | 云计算ETF | BUY | 1263.88 | paper_rule_validation; rank=1; rank_score=88.861036; mid_trend=BUY; short_swing=BUY; amount=1263.88 | 是 | 否 |
| 2026-07-10 | 159929 | 医药ETF | BUY | 125.94 | paper_rule_validation; rank=2; rank_score=86.216237; mid_trend=BUY; short_swing=BUY; amount=125.94 | 是 | 否 |

- 是否真实交易：否。

---

# 六、BUY Ranking 与 adjusted preview

## 原始 BUY ranking Top 10

| rank | code | name | group | mid | short | rank_score |
| ---: | --- | --- | --- | --- | --- | ---: |
| 1 | 516510 | 云计算ETF | 科技成长 | BUY | BUY | 88.861 |
| 2 | 159929 | 医药ETF | 消费医药 | BUY | BUY | 86.2162 |
| 3 | 515000 | 科技ETF | 科技成长 | BUY | WATCH | 77.0373 |
| 4 | 512760 | 芯片ETF | 科技成长 | WATCH | BUY | 75.6699 |
| 5 | 159869 | 游戏ETF | 科技成长 | WATCH | BUY | 71.7119 |
| 6 | 510500 | 中证500ETF | 宽基 | BUY | WATCH | 71.5314 |
| 7 | 159865 | 养殖ETF | 周期资源 | WATCH | BUY | 67.0231 |

## adjusted preview Top 10

| adjusted_rank | code | name | group | original_score | adjusted_score | execution_status |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 1 | 516510 | 云计算ETF | 科技成长 | 88.861 | 86.861 | preview_only_not_executed |
| 2 | 159929 | 医药ETF | 消费医药 | 86.2162 | 84.2162 | preview_only_not_executed |
| 3 | 515000 | 科技ETF | 科技成长 | 77.0373 | 75.0373 | preview_only_not_executed |
| 4 | 510500 | 中证500ETF | 宽基 | 71.5314 | 74.5314 | preview_only_not_executed |
| 5 | 512760 | 芯片ETF | 科技成长 | 75.6699 | 70.6699 | preview_only_not_executed |
| 6 | 159869 | 游戏ETF | 科技成长 | 71.7119 | 69.7119 | preview_only_not_executed |
| 7 | 159865 | 养殖ETF | 周期资源 | 67.0231 | 67.0231 | preview_only_not_executed |

- preview_only_not_executed 数量：7
- 是否过度集中在主题/行业：THEME_CONCENTRATED
- 宽基/准宽基候选：588000 科创50ETF、510180 上证180ETF、510500 中证500ETF、512100 中证1000ETF、510050 上证50ETF
- 是否接执行层：否。

---

# 七、卖出复核与减仓候选

- REVIEW_1：无
- REVIEW_2：515000 科技ETF
- REDUCE_CANDIDATE：512800 银行ETF
- REDUCE：无
- SELL：无
- REDUCE_CANDIDATE 只是观察状态，不自动卖出。

---

# 八、浮盈保护 Preview

- PROFIT_WATCH：无
- PROFIT_PROTECTION_REVIEW：512880 证券ETF
- PROFIT_LOCK_CANDIDATE：515000 科技ETF
- 515000 当前状态：PROFIT_LOCK_CANDIDATE
- 515000 当前浮盈：119.57
- 515000 峰值浮盈：285.57
- 515000 峰值回撤：166.00 / 58.13%
- 是否自动止盈：否。

---

# 九、high_beta 风险观察

- high_beta 持仓数量：1
- high_beta 占总资产比例：5.77%
- high_beta 占持仓市值比例：19.61%
- 金融地产组暴露：总资产 13.99% / 持仓 47.51%
- 512880 当前状态：HB_CAUTION
- 是否 HB_CAUTION / HB_ELEVATED：是
- 是否自动减仓：否。

---

# 十、宽基平衡 Preview

- 当前宽基占比：0.00%
- 行业/主题占比：100.00%
- 金融地产组占比：47.51%
- 科技成长组占比：52.49%
- high_beta 占比：19.61%
- Top 宽基候选：588000 科创50ETF、510180 上证180ETF、510500 中证500ETF、512100 中证1000ETF、510050 上证50ETF
- 588000 状态：BUY/WATCH，rank=1，raw=76.6456，adjusted=79.6456
- 159915 状态：WATCH/N/A，rank=8，raw=0，adjusted=0
- 510300 状态：WATCH/N/A，rank=7，raw=0，adjusted=0
- 500 元 hypothetic preview 改善：宽基到 14.51%，金融地产到 40.61%，科技成长到 44.87%，high_beta 到 16.76%。
- 是否自动买入：否。

---

# 十一、Shadow / 研究模型状态

- 当前阶段：Shadow Observation Period
- evidence_level：insufficient
- ready_for_preview：false
- ready_for_execution：false
- persistence_breakout_v2 最新 selected：1
- missed opportunity 数量：123
- matured forward return 样本：49
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
