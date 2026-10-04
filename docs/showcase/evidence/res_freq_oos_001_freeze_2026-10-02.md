# TASK-RES-FREQ-OOS-001 — TEWM-v1 与 prospective OOS 协议冻结

工程 VERDICT：**PASSED_WITH_WARNINGS**。TEWM-v1 已冻结，prospective OOS 协议 ACTIVE；研究观察账户 DEFINED_NOT_STARTED，真实 signal、execution 和完整 OOS 区间均为 **0**。

Context 已按授权从 2026-09-28 同步至 **2026-09-30**。183 只 canonical ETF 文件均与 9 月 30 日成功目录事务的 after manifest 一致；更新状态的 latest_trade_date、看板和 context 同期。10 月 1 日刷新失败且未写入 SSOT，不作为 committed 日期。标准 context validator 为 VALID_WITH_WARNINGS，日期一致且 0 blocking errors；唯一警示是保留的旧 regime 快照。

## 冻结身份和信息边界

- 名称：Three-ETF Weekly Momentum v1 / TEWM-v1，version 1，用途 PROSPECTIVE_OOS_RESEARCH。
- TEWM_V1_CONTRACT_HASH：`a21a71061eda5a760e51f835ac9db03a6523deb96f4e5d0330d383d176257e34`。
- OOS_FREEZE_TIMESTAMP：**2026-10-02T11:49:24.962489+08:00**。顺序已审计：合同独占写入 → SHA-256 完成 → 记录时间 → 写 manifest 和冻结回执。
- HISTORICAL_RESEARCH_CUTOFF：**2026-09-15**。
- LATEST_COMMITTED_MARKET_DATE_AT_FREEZE：**2026-09-30**。
- **2026-09-16 至 2026-09-30 永久归为 POST_RESEARCH_PRE_FREEZE_QUARANTINE**；冻结周 9 月 28 日至 10 月 4 日排除。此前可访问的数据不能补记成 prospective OOS。

## 第一个合法观察点

规则是冻结自然周之后第一个完整自然周的最后实际交易日收盘，跳过整周休市；以官方交易日历选取，不硬编码星期五。

依据[交易所 2026 年休市公告](https://www.sse.com.cn/disclosure/announcement/general/c/c_20260915_10832273.shtml)，10 月 5—11 日为首个完整自然周，10 月 8、9 日是该周交易日。因此当前日历支持的首个 checkpoint 为 **2026-10-09 收盘**，首次计划执行为 **2026-10-12 raw open**。信号仍须等当天数据在冻结后实际可用并通过事件、TR、估值与输入哈希检查才可记录；未在当日形成的信号保持缺口，不能事后回填。

Weekly 与 Daily 在这个共同 checkpoint 各自从 12,000 元现金和零持仓开始。Daily 不提前从 10 月 8 日启动；此后每天检查，Weekly 每完整自然周的最后实际交易日检查。节假日较短交易周只要所有实际交易日完整覆盖，仍可形成完整区间。

## 冻结规则和继承

Universe 为 510300 / 510500 / 159915。TR20 要求 21 个有效观察，按 TR_INDEX(D)/TR_INDEX(D−20)−1 排序，分数降序、ETF code 升序解并列；全部负分仍选 Top2。名单变化时各冻结 45% 信号日收盘研究权益；名单不变则保持，不按权重漂移重新平衡。

执行沿用 next actual trading-day raw open、先卖后买、非负现金、合法 lot 和 odd-lot、共同比例分配。Base 成本为 commission 0.00012、最低 5 元、slippage 0.0003、stamp tax 0，标注 ASSUMED_COSTS。TR-002/TR-003 的分红登记权益、应收、支付日保守释放、数量行动和估值语义继承；执行、分红和估值合同及实现哈希均已固定并核对。

此前 PM-001B 合同中的 price-only / no-dividend 条款仅作为历史来源保留；TEWM 合同明确由 TR-002/TR-003 替代相应信号和权益口径。未修改任何旧合同。未来事件覆盖未知时必须 fail safe，不假设零分红或单位因子 1。

## 观察结构和记录要求

`reports/research_data/tewm_v1_oos/` 下已建立 signals、executions、weekly_snapshots、daily_comparator 和 audit 结构。两份 ledger_definition 固定共同规则哈希、独立初始状态和角色：Weekly 为候选，Daily 为冻结研究比较账户。

信号写入接口在生成时记录三个 score/rank、Top2、此前名单、变化状态、下一实际执行日和精确合同哈希。每次复制完整 as-known 输入快照并记录源文件路径、哈希、TR 版本、日期和可用时间；任一未来日期行或生成时尚不可用的输入拒绝。信号文件通过独占创建、只读权限和哈希链维护，重复写入拒绝。原始信号保留，修正只能另追加并引用原哈希。

执行日志引用已存在的 signal hash，检查下一实际交易日、raw-open 来源、冻结价格/成本、逐笔现金、份额和取消订单。OOS-002 负责将新输入接入继承的执行/分红/估值适配器并保留完整对账证据；本批未运行历史 replay 或未来研究交易。日志入口已可调用，未挂接调度或正式执行系统。

## Review 与后续状态

第一次正式审阅冻结在 **26 个完整、可评价的 Weekly intervals**，不是 26 个日历周。区间从一个 eligible checkpoint close 到下一个；两个研究账户和所有实际交易日均需完整，起点订单执行已计入，终点新订单未执行。未满 26 个只允许数据收集和运行审计；没有收益成功阈值、额外 benchmark 或临时新增统计检验。

只可因合同违背、未来泄漏、未解决企业行动、canonical 数据或会计不变量失败而提前 fail safe。短期盈利或亏损不改变观察期限。

HISTORICAL_PARAMETER_TUNING = CLOSED；PARAMETER_TUNING = NOT_AUTHORIZED；STRATEGY_V2 = NOT_CREATED；FORMAL_SHADOW / FORMAL_PAPER / LIVE = NOT_AUTHORIZED。NEXT_TASK_AUTHORIZED = TASK-RES-FREQ-OOS-002，仅在真正 eligible checkpoint 到来时执行，本批未启动。

## 验证与保护

**21 项合成测试通过**，所有 fixture 位于隔离临时目录。覆盖 pre-freeze/freeze-week 排除、禁止迟到回填、未来输入不可用、合同和哈希不可变、append-only、信号/执行先后、价格替代拒绝、Daily/Weekly 规则共享、独立 12,000 元起点和 26 完整区间门禁。真实 OOS 目录未产生 signal、execution 或收益记录。

OOS 冻结阶段保护 **590** 个现有文件，变化 **0**。context 同步阶段只有 docs/current_phase_status.json 为授权修改；研究、原始行情、分红/TR_INDEX、合同、正式策略、Universe、Paper、Shadow、Live 文件变化均为 0。

限制：本 verdict 仅表示协议冻结工程通过，不产生 OOS 收益或策略有效性结论。当前官方日历证据覆盖 2026 年；进入 2027 年前须以新官方证据追加日历版本，不能猜测未覆盖的交易日。Calendar 是可追溯输入数据，追加版本不能重写过去的实际交易日或更改策略规则。
