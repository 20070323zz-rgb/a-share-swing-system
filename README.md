# A 股周线波段模拟盘系统

这是一个用于学习 A 股 ETF/个股波段交易、交易系统和 Python 量化研究的模拟盘项目。当前版本适合做一周左右的模拟交易测试、每日收盘复盘、本地历史回测，以及从公开行情源下载历史日线数据。

重要边界：

- 不接入真实券商 API
- 不写真实下单代码
- 不保存账号、密码、cookie、token、银行卡信息
- 不使用融资融券、期权、杠杆、自动转账
- 所有交易记录都来自 `trades.csv`，只代表模拟交易
- 行情来自公开数据源或你手动放入 `data/` 的本地 CSV
- 联网功能只下载公开历史行情，不连接任何券商交易接口

行情源验证规则：

所有行情数据源可用性判断，必须以用户本机 PyCharm/.venv 环境运行结果为准。Codex 云端/沙盒环境的网络失败，只能记录为 Codex 环境限制，不能据此判定 AKShare、BaoStock、东方财富或其他数据源不可用。

职责分工：

- Codex 负责开发、修复、生成脚本和报告逻辑。
- 用户本机负责关键行情源可用性验证。
- ChatGPT/用户根据本机结果决定项目方向。
- 不要用 Codex 云端网络失败否定某个数据源。

## 项目结构

```text
a-share-swing-system/
├── README.md
├── PROJECT_STATE.md
├── DECISIONS.md
├── CHATGPT_NOTES.md
├── strategy.md
├── risk_rules.md
├── watchlist.csv
├── trades.csv
├── codex_tasks.md
├── requirements.txt
├── data/
├── reports/
├── logs/
├── raw/
├── notebooks/
├── scripts/
└── src/
```

核心代码：

- `src/main.py`：每日信号、周复盘和风险报告入口
- `src/backtest.py`：单标的历史回测入口
- `src/signal_engine.py`：BUY / SELL / HOLD / WATCH 信号规则
- `src/portfolio.py`：模拟账户、持仓、盈亏和仓位计算
- `src/data_loader.py`：读取并校验本地 CSV
- `src/data_fetcher.py`：用本地缓存、BaoStock、AKShare/东方财富等公开行情源下载历史行情，并生成数据更新日志和质量报告
- `src/features.py`：统一计算 ETF 模型研究因子
- `src/labels.py`：生成 future returns 研究标签，不参与当日信号
- `src/data_coverage.py`：检查 ETF 池本地 CSV 覆盖情况
- `src/data_health.py`：检查本地 CSV 字段、日期、价格和成交量健康状态
- `src/factor_analysis.py`：生成因子有效性分析报告
- `src/model_research.py`：模型研究骨架，样本不足时只输出占位研究报告
- `scripts/update_etf_data.py`：用户本机 BaoStock ETF 日线下载脚本，默认保存到 `data/etf_daily/`
- `scripts/run_daily_close.sh`：收盘后自动更新公开行情并生成每日报告
- `scripts/run_open_check.sh`：开盘前基于已有本地数据生成观察报告
- `scripts/run_weekly_review.sh`：周五生成周复盘报告
- `scripts/run_codex_daily_research.sh`：生成每日 Codex 研究提示，不调用 API
- `scripts/run_codex_weekly_research.sh`：生成每周 Codex 研究提示，不调用 API
- `scripts/normalize_csv.py`：把手动下载的 CSV 标准化导入到 `data/`

## 项目记忆文件

为了减少新对话时丢上下文，本项目保留三份固定记忆文件：

- `PROJECT_STATE.md`：当前进展、阻塞、下一步优先级。新对话优先读它。
- `DECISIONS.md`：已经定下来的安全边界、账户参数、策略规则和输出约定。
- `CHATGPT_NOTES.md`：保存你和 ChatGPT 讨论出的策略想法，方便 Codex 落地。
- `docs/trading_rules.md`：项目交易研究规则，包括标的范围和个股仓位上限。

如果以后新开 Codex 对话，可以先说：

```text
请先阅读 PROJECT_STATE.md、DECISIONS.md、codex_tasks.md 和 CHATGPT_NOTES.md，再继续这个量化项目。
```

## 安装依赖

进入项目目录后运行：

```bash
pip install -r requirements.txt
```

## 准备行情数据

系统读取本地日线 CSV，不使用真实交易接口。本地 `data/<code>.csv` 是所有外部下载失败时的兜底缓存。你可以手动把数据放入 `data/` 文件夹，文件名使用证券代码：

```text
data/510300.csv
data/513500.csv
data/159915.csv
data/512100.csv
data/600519.csv
```

CSV 至少包含这些列：

```text
date,open,high,low,close,volume
```

也兼容部分中文列名：

```text
日期,开盘,最高,最低,收盘,成交量
```

日期可以是 `2026-05-29` 或 `20260529`。

至少建议准备 60 个交易日以上数据，因为系统需要计算 MA60。基准默认使用 `510300`，如果缺少基准数据，相对强弱信号会提示数据不足。

## 如何手动导入 ETF 日线 CSV

当 AKShare / 东方财富公开行情接口不稳定时，可以手动从东方财富、同花顺、Choice、券商软件或其他行情软件导出日线 CSV，再导入本系统。

原始 CSV 放入：

```text
raw/
```

例如：

```text
raw/512880.csv
```

`raw/` 只用于保存手动下载的原始 CSV，不参与交易，不包含账号信息，也不会被系统当作真实下单依据。

标准输出文件放入：

```text
data/<code>.csv
```

例如：

```text
data/512880.csv
```

标准字段必须是：

```text
date,open,high,low,close,volume
```

如果原始 CSV 是中文字段，系统支持自动映射：

```text
日期 -> date
开盘 -> open
最高 -> high
最低 -> low
收盘 -> close
成交量 -> volume
```

使用标准化脚本：

```bash
python3 scripts/normalize_csv.py --input raw/512880.csv --code 512880
```

输出：

```text
data/512880.csv
```

脚本会：

- 自动识别中文字段和英文标准字段
- 只保留 `date,open,high,low,close,volume`
- 把日期转成 `YYYY-MM-DD`
- 按日期升序
- 按 `date` 去重，保留最后一条
- 字段缺失时给出清晰报错
- 不连接任何交易接口

## 联网下载公开行情

### 本机 BaoStock ETF 数据下载

当前 ETF 池已扩展，推荐优先使用本机 BaoStock 下载脚本。Codex 只负责写脚本，不用 Codex 云端网络判断 BaoStock 是否可用；数据源可用性以你本机 `.venv` / PyCharm 运行结果为准。

下载全部 ETF 池数据，包括 `trade_pool` 和 `observe_pool` 中的 ETF：

```bash
python3 scripts/update_etf_data.py
```

指定结束日期：

```bash
python3 scripts/update_etf_data.py --end 2026-06-02
```

只下载指定 ETF：

```bash
python3 scripts/update_etf_data.py --symbols 510300,159915
```

脚本会自动读取 `watchlist.csv`，不需要手工复制 ETF 代码。默认保存到：

```text
data/etf_daily/
```

文件名格式：

```text
data/etf_daily/sh_510300.csv
data/etf_daily/sz_159915.csv
```

如果已有 CSV，脚本会同时检查两端缺口：

- 本地起始日期晚于 `--start` 时，自动向前补齐历史数据。
- 本地结束日期早于 `--end` 时，自动向后增量更新。
- 最后合并、按 `date` 去重并升序保存。

如果没有 CSV，默认从 `2018-01-01` 全量下载。默认使用前复权 `adjustflag=2`。

补齐到 2022 年以来的数据：

```bash
python3 scripts/update_etf_data.py --start 2022-01-01 --end 2026-06-03 --adjustflag 2
```

输出字段至少包括：

```text
date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST
```

下载完成后生成：

```text
reports/data_download_report.md
```

本项目读取行情时会按优先级兼容：

```text
data/etf_daily/
data/raw/
data/
```

并兼容以下文件名：

```text
sh_510300.csv
sh.510300.csv
510300.SH.csv
510300.csv
```

### 原有公开行情下载入口

安装依赖后，可以下载 `watchlist.csv` 中 `enabled=1` 的 ETF/股票历史日线。当前数据源优先级为：

1. 本地 `data/<code>.csv` 作为失败兜底缓存
2. BaoStock 免费行情源
3. AKShare / 东方财富公开接口
4. 手动 CSV 导入提示
5. Tushare Pro 预留位

正常更新时仍会尝试外部数据源；如果外部数据源失败但本地 CSV 合格，系统会继续使用缓存，不阻塞日报、模型数据集和模拟盘报告。

```bash
python3 src/main.py --fetch-data --start-date 2025-01-01 --end-date 2026-06-02
```

批量下载建议使用分批、限速和较少重试，降低公开行情源断开概率：

```bash
python3 src/main.py --fetch-data --start-date 2025-01-01 --end-date 2026-06-02 --batch-size 5 --sleep-seconds 3 --retry 2
```

参数说明：

- `--batch-size`：每批最多下载的标的数量，默认 `5`
- `--sleep-seconds`：标的之间和重试之间等待秒数，默认 `2`
- `--retry`：每个公开行情接口最多重试次数，默认 `2`
- `--fetch-code`：只下载指定代码，适合排查单个失败标的
- `--fetch-group`：只下载指定分组，例如 `宽基`、`行业`、`主题`、`防御`
- `--fetch-source`：指定数据源，可选 `auto`、`baostock`、`akshare`、`tushare`，默认 `auto`

单标的下载：

```bash
python3 src/main.py --fetch-data --fetch-code 510500 --start-date 2025-01-01 --end-date 2026-06-02 --retry 2 --sleep-seconds 3
```

指定 BaoStock 下载：

```bash
python3 src/main.py --fetch-data --fetch-code 512880 --fetch-source baostock --start-date 2025-01-01 --end-date 2026-06-02
```

分组下载：

```bash
python3 src/main.py --fetch-data --fetch-group 宽基 --start-date 2025-01-01 --end-date 2026-06-02 --batch-size 3 --sleep-seconds 3 --retry 2
```

收盘自动任务建议使用增量模式。已有本地 CSV 时，系统会从最后一个交易日前回看一段时间重新抓取并合并；如果增量下载失败但本地 CSV 合格，会继续使用旧数据。

```bash
python3 src/main.py --fetch-data --incremental --lookback-days 10 --batch-size 5 --sleep-seconds 3 --retry 2
```

增量参数：

- `--incremental`：启用增量更新
- `--lookback-days`：从本地最后交易日前回看的天数，默认 `10`

下载后会保存为：

```text
data/<code>.csv
```

输出字段统一为：

```text
date,open,high,low,close,volume
```

`watchlist.csv` 字段说明：

- `code`：证券代码
- `name`：名称
- `type`：`ETF` 或 `STOCK`
- `source`：数据来源，支持 `auto`、`akshare`、`baostock`；短期建议保持 `auto`，由系统自动选择公开行情源
- `enabled`：`1` 表示下载并参与信号计算，`0` 表示只保留观察、不参与模拟盘
- `benchmark_code`：基准代码，默认可用 `510300`
- `group`：分类，例如 `宽基`、`行业`、`主题`、`防御`、`QDII观察`、`港股观察`、`个股观察`
- `role`：`trade_pool` 表示交易池，`observe_pool` 表示观察池
- `note`：备注，示例不构成投资建议

当前第一轮模拟盘默认只让 `enabled=1` 且 `role=trade_pool` 的标的进入主交易池。`role=observe_pool` 的标的可以保留观察，但默认不参与第一轮正式模拟盘。

联网下载后会自动生成：

- `reports/data_update_log.md`：记录下载时间、代码、名称、日期范围、行数、成功状态和失败原因
- `reports/data_quality_report.md`：检查数据条数、空值、重复日期、价格合法性和成交量合法性
- `reports/watchlist_health_report.md`：汇总本次新下载成功、本地缓存可用、失败标的和可用率

### Tushare Pro 预留

系统预留了 Tushare Pro 行情源位置，但当前版本不强制接入完整 Tushare 下载逻辑。未来如果要启用授权行情，只通过环境变量提供 token：

```bash
export TUSHARE_TOKEN="你的token"
```

不要把 token 写入任何项目文件、报告、日志或代码。Tushare 只允许用于行情数据，不用于交易、不连接券商、不下单。

## 每天怎么看报告

- `reports/latest_daily.md`：每日交易信号入口，先看 BUY / SELL / WATCH、风控和数据问题。
- `reports/latest_brief.md`：每天最简洁入口，只看信号数量、双周期状态、Top 5、group 排序和今日状态。
- `reports/latest_ranking.md`：ETF 横截面强弱排名、`composite_score`、`watch_score`、双周期共振和分组强弱。
- `reports/latest_data_coverage.md`：本地 CSV 覆盖率、缺失数量、trade_pool / observe_pool 覆盖情况。
- `reports/latest_data_health.md`：本地 CSV 字段、日期、价格、成交量和过期情况检查。
- `reports/latest_paper_portfolio.md`：模拟盘持仓估值报告，来自 `data/paper_positions.csv`，不代表真实交易。
- `reports/latest_factor_analysis.md`：因子有效性分析，查看因子与未来收益标签的研究关系。当前样本较少，不能过度解读。
- `reports/watchlist_health_report.md`：数据池健康情况，用来看本次检查范围、缓存可用率和缺失数据建议。
- `reports/model_dataset.csv`：未来模型训练数据雏形，记录每天 enabled 且有本地行情标的的横截面特征、辅助评分和 future returns 研究标签。
- `reports/latest_model_research.md`：模型研究骨架输出，样本不足时不训练或只做演示。
- `reports/strategy_compare_report.md`：中期策略与短期策略回测对比。

## 模拟盘持仓记录

模拟盘文件位于：

```text
data/paper_positions.csv
data/paper_trades.csv
reports/latest_paper_portfolio.md
```

`data/paper_positions.csv` 用于手工记录模拟持仓，核心字段包括：

```text
symbol,name,strategy_source,position_type,entry_date,entry_price,quantity,cost,stop_loss,reason
```

系统每次运行 `python3 src/main.py` 时，会根据最新本地收盘价更新当前价、市值、浮盈浮亏、持仓天数和风险提醒。它只做本地模拟记录和报告，不接券商 API，不真实下单，不读取账号密码。

## 双周期 ETF 策略

当前主线仍然是 ETF，不主攻个股。个股保留在 `observe_pool` 中辅助观察，不进入第一阶段正式 ETF 交易池。

`mid_trend` 是主策略：

- 模拟资金：7000 元，占 70%。
- 目标持仓：20-60 个交易日。
- 使用 MA20、MA60、20 日相对强弱、成交量和移动止盈逻辑。
- 当前 BUY / WATCH / SELL 规则保持稳定。

`short_swing` 是实验策略：

- 模拟资金：3000 元，占 30%。
- 目标持仓：10-20 个交易日。
- 使用 MA10、MA20、5 日涨幅、10 日相对强弱、成交量和距离 MA10。
- 不替代 `mid_trend` 主策略。

运行示例：

```bash
python3 src/main.py --strategy mid_trend
python3 src/main.py --strategy short_swing
```

双周期共振规则：

- `STRONG_RESONANCE`：mid_trend BUY + short_swing BUY，双周期强共振。
- `SHORT_TRIAL`：mid_trend WATCH + short_swing BUY，只允许短期账户小仓试探。
- `MID_HOLD`：mid_trend BUY + short_swing WATCH，中期趋势确认，短期不追。
- `RISK_ALERT`：mid_trend BUY + short_swing SELL，中期仍在但短期转弱。
- `AVOID`：中期 SELL 后的短期反弹或双周期走弱。
- `OBSERVE`：双周期都未形成明确动作。

双周期共振时，短期账户可以小仓补充，但不能重仓；short_swing 单只 ETF 共振补充仓建议不超过短期账户资金的 20%-30%，同一 ETF 的 mid_trend + short_swing 合计风险暴露不超过总资产 35%，同一 group 总暴露不超过总资产 50%。

`composite_score` 是辅助多因子评分，不是交易指令。`watch_score` 是 WATCH 接近 BUY 的辅助评分，不是买入指令。future returns 只用于研究，不参与信号生成、排名评分或任何当日决策。当前所有内容都是模拟盘和学习用途。

## 运行每日信号

```bash
python3 src/main.py
```

这个命令只会读取本地 CSV 和手工模拟交易记录，不会连接券商，也不会下单。

指定日期：

```bash
python3 src/main.py --date 2026-05-29
```

强制生成周复盘：

```bash
python3 src/main.py --date 2026-05-29 --weekly
```

如果你的电脑已经把 `python` 指向 Python 3，也可以把上面的 `python3` 换成 `python`。

## 运行历史回测

回测单个标的：

```bash
python3 src/backtest.py --code 510300
```

指定基准：

```bash
python3 src/backtest.py --code 159915 --benchmark-code 510300
```

回测会复用 `src/signal_engine.py` 的信号规则，只读取 `data/` 中的本地 CSV，不连接券商、不下单。

## macOS launchd 定时任务

项目提供了三个 Mac 自动运行脚本。它们只会下载公开行情、读取本地数据、生成模拟盘报告，不会连接券商，不会真实下单，也不会读取任何账号、密码或验证码。

此前用过简单定时配置做验证，但在 macOS 上长期稳定运行更适合使用 launchd。简单定时方式容易受环境、权限和触发机制影响；launchd 是 macOS 原生任务调度方式，更适合登录用户下的长期自动运行。

不建议把长期自动化项目放在 `Documents` / `文稿` 目录中，因为 macOS 可能对该目录做额外隐私权限拦截，导致 launchd 无法进入目录或执行脚本。建议放在：

```text
/Users/dayin/Code/a-share-swing-system
```

或类似的 `~/projects` 目录。安装 launchd 前，请先确认项目实际路径与脚本、plist 中的路径一致。

三个定时任务：

- 周一到周五 09:20：开盘前观察，只基于已有本地数据生成报告。
- 周一到周五 15:30：收盘后更新本机 ETF 数据并生成每日信号报告。
- 周五 15:40：生成周复盘报告。

安装 launchd 任务：

```bash
cd /Users/dayin/Code/a-share-swing-system
bash scripts/install_launchd_jobs.sh
```

卸载 launchd 任务：

```bash
bash scripts/uninstall_launchd_jobs.sh
```

手动测试：

```bash
bash scripts/test_scheduled_jobs.sh
```

launchd 任务标签：

```text
com.dayin.a-share.open-check
com.dayin.a-share.daily-close
com.dayin.a-share.weekly-review
```

日志位置：

```text
logs/open_check.log
logs/daily_close.log
logs/weekly_review.log
logs/launchd_open_check.out.log
logs/launchd_open_check.err.log
logs/launchd_daily_close.out.log
logs/launchd_daily_close.err.log
logs/launchd_weekly_review.out.log
logs/launchd_weekly_review.err.log
```

查看日志：

```bash
tail -n 80 logs/open_check.log
tail -n 80 logs/daily_close.log
tail -n 80 logs/weekly_review.log
tail -n 80 logs/launchd_open_check.err.log
```

确认报告是否生成：

```bash
ls reports/daily_signal_*.md
ls reports/weekly_review_*.md
cat reports/latest_daily.md
cat reports/latest_weekly.md
cat reports/data_update_log.md
cat reports/data_quality_report.md
```

`scripts/run_daily_close.sh` 会先运行本机 BaoStock ETF 下载脚本，再运行 `python3 src/main.py` 生成每日信号、风险报告、模型数据集、数据覆盖报告和数据健康报告。

查看 launchd 任务：

```bash
launchctl print gui/$(id -u)/com.dayin.a-share.open-check
launchctl print gui/$(id -u)/com.dayin.a-share.daily-close
launchctl print gui/$(id -u)/com.dayin.a-share.weekly-review
```

手动触发 launchd 任务：

```bash
launchctl kickstart -k gui/$(id -u)/com.dayin.a-share.open-check
launchctl kickstart -k gui/$(id -u)/com.dayin.a-share.daily-close
launchctl kickstart -k gui/$(id -u)/com.dayin.a-share.weekly-review
```

注意事项：

- Mac 必须开机。
- 用户需要已登录，当前使用的是 `~/Library/LaunchAgents/`，不是 root 级 LaunchDaemons。
- Mac 睡眠时任务可能不会准时执行，可以用系统节能设置或 `caffeinate` 保持唤醒。
- PyCharm 不需要打开。
- 不需要手动激活 `.venv`，脚本使用项目内 Python 绝对路径。
- 不建议把 launchd 长期任务放在 `Documents` / `文稿` 目录。若仍放在该目录，可能需要额外授予 Terminal、shell 或相关进程访问权限。
- 本系统仍然只生成报告和模拟盘记录，不真实下单。

## Codex 研究提示

项目提供两个研究提示脚本，只负责把现有报告、模型数据和日志整理成 Markdown prompt。它们不会调用真实 Codex API，不会修改策略，不会交易。

```bash
scripts/run_codex_daily_research.sh
scripts/run_codex_weekly_research.sh
```

输出文件：

```text
reports/codex_daily_research_prompt.md
reports/codex_weekly_research_prompt.md
```

你可以手动把这些 prompt 交给 Codex 或 ChatGPT 做研究分析。脚本里的问题会要求只写 proposal，不直接改主策略。

## 输出文件

运行后会生成：

- `reports/daily_signal_YYYY-MM-DD.md`
- `reports/latest_daily.md`
- `reports/weekly_review_YYYY-MM-DD.md`，周五或使用 `--weekly` 时生成
- `reports/latest_weekly.md`
- `reports/risk_report.md`
- `reports/data_update_log.md`
- `reports/data_quality_report.md`
- `reports/data_download_report.md`
- `reports/data_coverage_report.md`
- `reports/latest_data_coverage.md`
- `reports/data_health_report.md`
- `reports/latest_data_health.md`
- `reports/account_status.csv`
- `reports/signals.csv`
- `reports/model_dataset.csv`
- `reports/backtest_result.csv`
- `reports/backtest_summary.md`
- `trades.csv`，你手动维护的模拟成交记录

各文件用途：

- `daily_signal_YYYY-MM-DD.md`：每日收盘后查看候选买入、候选卖出、观望原因和明日计划
- `latest_daily.md`：始终指向最近一次每日信号内容，方便每天固定打开
- `weekly_review_YYYY-MM-DD.md`：每周五或手动 `--weekly` 生成一周复盘
- `latest_weekly.md`：始终指向最近一次周复盘内容
- `risk_report.md`：查看现金比例、持仓比例、单一标的是否超限、止损预计亏损
- `data_update_log.md`：查看公开行情下载是否成功
- `data_quality_report.md`：查看下载后的 CSV 是否满足基础质量要求
- `data_download_report.md`：查看本机 BaoStock ETF 下载结果
- `latest_data_coverage.md`：查看 ETF 池本地数据覆盖率
- `latest_data_health.md`：查看本地 CSV 健康检查结果
- `account_status.csv`：保存每日账户总资产、现金、市值和回撤
- `signals.csv`：保存每日每个标的的信号和原因
- `model_dataset.csv`：保存每日横截面特征，用于后续模型研究；暂不包含未来收益标签
- `backtest_result.csv`：保存回测每笔交易明细
- `backtest_summary.md`：保存回测收益率、最大回撤、胜率、交易次数和持仓天数

## 如何记录模拟交易

当你决定按信号进行模拟买入或卖出时，手动在 `trades.csv` 增加一行。例如：

```text
2026-05-29,159915,创业板ETF,ETF,BUY,2.000,1000,2000,0,模拟买入,cash_after,position_after,true
```

系统下次运行会读取 `trades.csv` 并重建模拟账户。

如果 `trades.csv` 不存在，系统会自动生成模板；如果字段、日期、价格或数量有问题，程序不会崩溃，会在每日信号报告中提示。

## 适合复制给 ChatGPT 的内容

每日和每周 Markdown 报告都按复盘格式输出，可以直接复制给 ChatGPT，询问：

- 今天哪些信号值得执行？
- 哪些标的违反风控？
- 下周应该观察哪些标的？
- 我的模拟交易记录有什么问题？
