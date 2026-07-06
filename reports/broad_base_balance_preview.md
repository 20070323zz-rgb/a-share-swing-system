# 宽基平衡 adjusted preview 观察报告 2026-07-04 00:03:54

本报告只做宽基平衡 preview，不自动买入、不自动调仓、不修改 paper_trades.csv / paper_positions.csv，不接券商 API。

## 摘要结论
- 当前宽基占比：0.00%
- 当前行业/主题占比：100.00%
- 金融地产组占比：47.51%
- 科技成长组占比：52.49%
- high_beta 占比：19.61%
- 组合状态：BROAD_BASE_MISSING, THEME_CONCENTRATED, HB_WATCH
- 候选数量：10
- preview 假设加入金额：500.00
- adjusted preview 是否接入执行层：false

## 当前判断
- 当前正式模拟仓宽基占比为 0，缺少宽基平衡层。当前持仓主要集中在科技成长与金融地产，主题集中度偏高。当前优先观察候选：588000 科创50ETF、510180 上证180ETF、510500 中证500ETF。
- BUY ranking 当前仍偏证券、科技、科创、AI；宽基平衡层只用于观察候选，不替代原始 BUY ranking。
- 若后续要进入正式规则，需要至少经过 shadow tracking、回测和人工确认。

## 宽基平衡候选
| rank | symbol | name | type | mid | short | raw_rank | raw_score | adjusted_rank | adjusted_score | balance_score | 当前持有 | data_quality | reason |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | 588000 | 科创50ETF | quasi_broad_base | BUY | WATCH | 5 | 76.6456 | 3 | 79.6456 | 91.7127 | 否 | ok | 当前组合缺少宽基，加入后可补齐组合底仓观察层。；成长宽基/准宽基，能补宽基但仍偏成长风格。；mid_trend 为 BUY，短周期仍需观察。；B1 adjusted preview 已给宽基平衡加分。 |
| 2 | 510180 | 上证180ETF | broad_index | BUY | WATCH | 12 | 68.8625 | 8 | 71.8625 | 84.3778 | 否 | ok | 当前组合缺少宽基，加入后可补齐组合底仓观察层。；传统宽基，更适合降低行业/主题集中度。；mid_trend 为 BUY，短周期仍需观察。；B1 adjusted preview 已给宽基平衡加分。 |
| 3 | 510500 | 中证500ETF | broad_index | WATCH | N/A |  | 68.4508 |  | 68.4508 | 59.8043 | 否 | ok | 当前组合缺少宽基，加入后可补齐组合底仓观察层。；传统宽基，更适合降低行业/主题集中度。 |
| 4 | 512100 | 中证1000ETF | broad_index | WATCH | N/A |  | 68.4317 |  | 68.4317 | 59.7986 | 否 | ok | 当前组合缺少宽基，加入后可补齐组合底仓观察层。；传统宽基，更适合降低行业/主题集中度。 |
| 5 | 510050 | 上证50ETF | broad_index | WATCH | N/A |  | 64.6667 |  | 64.6667 | 58.6691 | 否 | ok | 当前组合缺少宽基，加入后可补齐组合底仓观察层。；传统宽基，更适合降低行业/主题集中度。 |
| 6 | 588080 | 科创创业50ETF | quasi_broad_base | WATCH | N/A |  | 72.5651 |  | 72.5651 | 58.0386 | 否 | ok | 当前组合缺少宽基，加入后可补齐组合底仓观察层。；成长宽基/准宽基，能补宽基但仍偏成长风格。 |
| 7 | 510300 | 沪深300ETF | broad_index | WATCH | N/A |  | 0 |  | 0 | 39.2691 | 否 | ok | 当前组合缺少宽基，加入后可补齐组合底仓观察层。；传统宽基，更适合降低行业/主题集中度。 |
| 8 | 159915 | 创业板ETF | quasi_broad_base | WATCH | N/A |  | 0 |  | 0 | 36.2691 | 否 | ok | 当前组合缺少宽基，加入后可补齐组合底仓观察层。；成长宽基/准宽基，能补宽基但仍偏成长风格。 |
| 9 | 159901 | 深100ETF | quasi_broad_base | WATCH | N/A |  | 0 |  | 0 | 36.2691 | 否 | ok | 当前组合缺少宽基，加入后可补齐组合底仓观察层。；成长宽基/准宽基，能补宽基但仍偏成长风格。 |
| 10 | 159949 | 创业板50ETF | quasi_broad_base | WATCH | N/A |  | 0 |  | 0 | 36.2691 | 否 | ok | 当前组合缺少宽基，加入后可补齐组合底仓观察层。；成长宽基/准宽基，能补宽基但仍偏成长风格。 |

## 500 元假设情景
以下只是假设情景，不修改现金、不修改持仓、不写交易流水、不作为买入信号。

| symbol | new_broad_base_weight | new_finance_real_estate_weight | new_tech_growth_weight | new_high_beta_weight | concentration_change |
| --- | ---: | ---: | ---: | ---: | ---: |
| 588000 | 14.51% | 40.61% | 44.87% | 16.76% | 7.62% |
| 510180 | 14.51% | 40.61% | 44.87% | 16.76% | 7.62% |
| 510500 | 14.51% | 40.61% | 44.87% | 16.76% | 7.62% |
| 512100 | 14.51% | 40.61% | 44.87% | 16.76% | 7.62% |
| 510050 | 14.51% | 40.61% | 44.87% | 16.76% | 7.62% |
| 588080 | 14.51% | 40.61% | 44.87% | 16.76% | 7.62% |
| 510300 | 14.51% | 40.61% | 44.87% | 16.76% | 7.62% |
| 159915 | 14.51% | 40.61% | 44.87% | 16.76% | 7.62% |

## 重点观察标的
- 588000 科创50ETF：mid=BUY，short=WATCH，raw_score=76.6456，adjusted_score=79.6456，balance_rank=1。
- 159915 创业板ETF：mid=WATCH，short=N/A，raw_score=0，adjusted_score=0，balance_rank=8。
- 510300 沪深300ETF：mid=WATCH，short=N/A，raw_score=0，adjusted_score=0，balance_rank=7。

## 为什么不能自动执行
- 本模块是 adjusted preview / observation，不是正式买入规则。
- 宽基平衡是否有效，需要后续 shadow tracking 和回测验证。
- 当前组合仍有 REVIEW、HB_WATCH 等观察状态，不能绕过人工复核。
- 任何正式规则变化都需要单独回到规则层确认。

## 安全边界
- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不修改 paper_trade_engine.py。
- 不修改 paper_trades.csv / paper_positions.csv。
- adjusted preview 未接入执行层。
