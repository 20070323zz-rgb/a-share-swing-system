# 项目状态记忆

最后更新：2026-06-03

## 项目定位

本项目是 A 股周线波段模拟盘系统，用于金融科技学习、公开行情数据处理、策略回测、模拟交易记录和复盘报告。

Codex 在本项目中的职责：

- 程序员：写代码、修 bug、整理项目结构。
- 数据工程师：下载/读取公开行情，清洗数据，检查数据质量。
- 报告员：生成每日信号、周复盘、风险报告、回测报告和候选标的说明。

重要边界：

- 不接入真实券商 API。
- 不写真实下单代码。
- 不保存账号、密码、cookie、token、银行卡信息。
- 不做融资融券、期权、杠杆、自动转账。
- 所有交易只能是 `trades.csv` 中手动记录的模拟交易。

行情源验证规则：

- 所有行情数据源可用性判断，必须以用户本机 PyCharm/.venv 环境运行结果为准。
- Codex 云端/沙盒环境的网络失败，只能记录为 Codex 环境限制，不能据此判定 AKShare、BaoStock、东方财富或其他数据源不可用。
- Codex 负责开发、修复、生成脚本和报告逻辑。
- 用户本机负责关键行情源可用性验证。
- ChatGPT/用户根据本机结果决定项目方向。
- 不要用 Codex 云端网络失败否定某个数据源。

## 当前项目进展

已经完成：

- 已创建 `a-share-swing-system` 项目结构。
- 已实现本地 CSV 行情读取。
- 已实现公开行情下载入口：`python3 src/main.py --fetch-data ...`。
- 已实现 AKShare 诊断、重试、ETF 备用接口、股票代码格式尝试和东方财富公开 K 线兜底。
- 已实现 MA20、MA60、20 日涨跌幅、成交量变化、相对强弱等指标。
- 已实现 BUY / SELL / HOLD / WATCH / NO_DATA 信号生成。
- 已实现模拟账户、现金、持仓、市值、盈亏、最大回撤和仓位建议。
- 已实现每日信号报告、周复盘报告、风险报告、数据更新日志、数据质量报告和单标的回测入口。
- 已新增 Mac 自动运行脚本，可供 cron 或 launchd 调用，只生成模拟盘报告，不会下单。
- 基础自动化运行层已完成，cron 已配置，三个脚本已手动验证通过。
- 已扩展 ETF 交易池和观察池，`watchlist.csv` 支持 `group` 和 `role` 字段。
- 已新增 `reports/latest_daily.md` 和 `reports/latest_weekly.md`。
- 已新增 `reports/model_dataset.csv`，开始积累每日横截面特征数据。
- 已新增 Codex 研究员辅助层，只生成研究 prompt，不调用 API、不改策略、不交易。
- 当前阶段已进入 ETF 横截面量化研究 + 双周期策略改进。ETF 是第一阶段主线，个股暂时只作为 observe_pool 辅助观察。

当前观察到的本地数据：

- 运行 `python3 src/main.py --fetch-data --start-date 2025-01-01 --end-date 2026-06-02` 后，行情下载结果已提升为成功 4 个、失败 1 个。
- `data/510300.csv` 已存在，字段为 `date,open,high,low,close,volume`，约 341 行。
- `data/159915.csv`、`data/512100.csv`、`data/513500.csv` 已存在。
- `data/600519.csv` 仍缺失。
- `trades.csv` 目前只有表头，说明还没有手动记录模拟成交。

2026-06-03 修复记录：

- 已确认 `data_fetcher.py` 的字段读取、`enabled` 判断、`type` 判断、日期转换、ETF AKShare 裸代码调用和中文字段映射有效。
- 下载日志显示 `159915`、`512100` 可通过 `AKShare fund_etf_hist_em` 成功。
- `513500` 可通过东方财富公开 K 线兜底成功。
- `510300` 本次接口偶发断开，但本地已有合格 CSV。
- `600519` 股票接口和东方财富公开 K 线兜底仍失败，是当前唯一剩余的数据下载问题。
- 已新增每个接口最多 3 次重试。
- 已新增“本次下载失败但已有合格本地 CSV 时保留旧数据继续使用”的逻辑。

2026-06-03 再次验证：

- 重新运行公开行情下载后，结果为成功 4 个、失败 1 个。
- 现在 ETF 数据链路已经足够进入第一周模拟盘测试。
- `600519` 个股数据可以后续单独处理，不应阻塞 ETF 模拟盘。

2026-06-03 每日信号观察：

- `reports/daily_signal_2026-06-02.md` 已正常生成。
- 当前账户仍为空仓，现金 10000 元。
- `513500` 标普500ETF 出现 BUY 信号，建议仓位约 1827.70 元 / 700 份，止损价 2.4152。
- `510300`、`159915`、`512100` 为 WATCH。
- `600519` 为 NO_DATA，原因是缺少 `data/600519.csv`。
- `510300` 回测数据读取正常，但当前交易次数为 0，说明规则没有形成完成交易，不是数据缺失。

2026-06-03 自动运行支持：

- 新增 `scripts/run_open_check.sh`：开盘前基于已有本地数据生成观察报告。
- 新增 `scripts/run_daily_close.sh`：收盘后下载公开行情并生成每日信号报告。
- 新增 `scripts/run_weekly_review.sh`：生成周复盘报告。
- 三个脚本都会激活项目 `.venv`，输出追加到 `logs/`。
- 自动运行仍然只做公开行情下载、模拟盘和报告，不接券商、不下单。
- 用户已在本机完成 cron 配置：
  - 工作日 09:20 运行开盘检查。
  - 工作日 15:30 运行收盘更新。
  - 周五 15:40 运行周复盘。
- 三个自动运行脚本已由用户手动验证通过。

2026-06-03 研究和数据层升级：

- `watchlist.csv` 字段已统一为 `code,name,type,source,enabled,benchmark_code,group,role,note`。
- 第一批 ETF 池已扩展为宽基、行业、主题、防御、QDII观察、港股观察、个股观察。
- `role=trade_pool` 且 `enabled=1` 的标的参与主交易池信号。
- `role=observe_pool` 的标的可保留观察，但默认不参与第一轮正式模拟盘。
- 每次日报会同步写入 `reports/latest_daily.md`。
- 每次周复盘会同步写入 `reports/latest_weekly.md`。
- 每次运行 `src/main.py` 会更新 `reports/model_dataset.csv`，按 `date + code` 去重。
- 新增 `scripts/run_codex_daily_research.sh`，生成 `reports/codex_daily_research_prompt.md`。
- 新增 `scripts/run_codex_weekly_research.sh`，生成 `reports/codex_weekly_research_prompt.md`。
- `scripts/run_daily_close.sh` 已优化为只运行一次 `python3 src/main.py --fetch-data ...`，避免重复生成日报。

2026-06-03 批量下载稳定性和增量更新：

- 新增下载参数：`--batch-size`、`--sleep-seconds`、`--retry`、`--fetch-code`、`--fetch-group`。
- 默认下载节奏调整为 `batch-size=5`、`sleep-seconds=2`、`retry=2`。
- 新增增量更新参数：`--incremental`、`--lookback-days`。
- 增量模式会读取 `data/<code>.csv` 最后交易日，从最后交易日前回看指定天数重新抓取，与旧 CSV 合并，按 `date` 去重并升序保存。
- 增量下载失败但本地 CSV 合格时，会继续使用本地旧数据。
- `reports/data_update_log.md` 已记录运行参数、下载模式、fresh download、cached success、failed。
- 新增 `reports/watchlist_health_report.md`，汇总 enabled trade_pool 总数、新下载成功数、本地缓存可用数、失败数和可用率。
- `scripts/run_daily_close.sh` 已改为使用增量模式：
  `python3 src/main.py --fetch-data --incremental --lookback-days 10 --batch-size 5 --sleep-seconds 3 --retry 2`
- `reports/model_dataset.csv` 已改为只记录有本地行情的 enabled 标的；无 CSV 的 NO_DATA 标的不进入模型数据集。
- 宽基分组下载测试结果：新下载成功 0 个，缓存可用 3 个，失败 2 个。
- 宽基缓存可用：`510300`、`512100`、`159915`。
- 宽基仍失败：`510500`、`588000`。
- 单标的 `510500` 下载测试结果：新下载成功 0 个，缓存可用 0 个，失败 1 个。
- 增量单标的 `510300` 测试结果：新下载成功 0 个，缓存可用 1 个，失败 0 个。
- 修复 `watchlist_health_report.md` 统计口径：现在同时显示全部 enabled trade_pool 总数和本次实际检查标的数；本次检查范围可用率与全池已缓存可用率分开计算。
- 单标的检查会明确提示“不代表全池健康度”；指定 group 检查会明确提示“不代表全池健康度”。

2026-06-03 行业 ETF 数据源诊断：

- 行业组 5 个 ETF：`512880`、`512800`、`512010`、`512690`、`159928`。
- 行业组批量下载结果：新下载成功 0 个，缓存可用 0 个，失败 5 个。
- 逐个单标的慢速下载结果：5 个全部失败，均无本地缓存。
- AKShare 原始 `fund_etf_hist_em` 测试结果：5 个全部失败。
- 当前失败不属于字段映射、watchlist 读取、enabled/type/source 判断问题。
- 当前失败集中在 AKShare 背后的东方财富公开行情源访问失败；在本环境表现为 `ConnectionError / NameResolutionError`，用户日志表现为 `ProxyError / RemoteDisconnected`。
- 已生成 `reports/industry_etf_diagnosis.md`。
- 未自动修改 `watchlist.csv`，未删除标的，未自动禁用标的。

2026-06-03 手动 CSV 导入和备用数据源：

- 确认不再围绕代理问题继续修复；no-proxy 直连后仍存在 `ConnectionError / RemoteDisconnected`，说明 AKShare / 东方财富公开行情源在当前网络环境下仍不稳定。
- 新增 `raw/` 目录，用于存放手动下载的原始 CSV。
- 新增 `scripts/normalize_csv.py`，可将手动 CSV 标准化为 `data/<code>.csv`。
- `normalize_csv.py` 支持中文字段和英文标准字段，输出 `date,open,high,low,close,volume`。
- README 已新增“如何手动导入 ETF 日线 CSV”说明。
- 新增 `reports/data_source_proposal.md`，提出手动 CSV、BaoStock、Tushare Pro 三种备用方案。
- 当前推荐优先级：先做手动 CSV 导入，再评估 BaoStock / Tushare。
- `watchlist_health_report.md` 对无缓存失败标的会建议“可通过 raw/ 手动导入 CSV 后继续参与模型数据集”。

2026-06-03 BaoStock 备用源接入：

- 已新增 `baostock` 依赖，并在 `src/data_fetcher.py` 中接入 BaoStock 免费日线行情。
- 新增命令行参数 `--fetch-source`，支持 `auto`、`akshare`、`baostock`、`tushare`。
- `watchlist.csv` 的 `source` 已调整为 `auto`，短期由系统自动选择公开行情源。
- BaoStock 代码转换规则已实现：`6`、`510/511/512/513/515/516/518/588` 开头走 `sh.<code>`；`0/3/159` 开头走 `sz.<code>`。
- Tushare Pro 已预留安全占位，只检测 `TUSHARE_TOKEN` 环境变量，不保存、不打印 token，当前不完整接入。
- README 已说明 `source` 字段、`--fetch-source` 和未来 Tushare token 使用方式。
- `reports/data_update_log.md` 和 `reports/watchlist_health_report.md` 已显示尝试数据源、最终成功源和缓存情况。
- 本机已确认 `.venv` 可导入 BaoStock。
- BaoStock 单标的测试：`512880`、`510500` 均进入 BaoStock 路径，但因 BaoStock 登录阶段网络接收错误失败，且无本地缓存。
- BaoStock 行业组测试：5 个行业 ETF 新下载成功 0 个、缓存可用 0 个、失败 5 个。
- 已生成 `reports/baostock_diagnosis.md`。
- 当前主线仍可使用已有缓存 `510300`、`159915`、`512100` 生成日报和 `model_dataset.csv`。

2026-06-03 用户本机 BaoStock 验证更新：

- 用户已在本机 PyCharm / `.venv` 环境验证 BaoStock 可用。
- BaoStock 登录成功：`error_code = 0`，`error_msg = success`。
- BaoStock 可获取股票日线数据：`sh.600519` 可返回 `date,open,high,low,close,volume`。
- BaoStock 可获取 ETF 日线数据：`sh.512880` 可返回 `date,open,high,low,close,volume`。
- `512880` 返回数据起始日期可能晚于请求日期，说明部分 ETF 历史覆盖可能不完整，但接口本身可用。
- 用户本机行业组运行结果：新下载成功 5 个，缓存可用 0 个，失败 0 个。
- 后续剩余 ETF 数据也已在用户本机补齐。
- 已生成 `reports/local_validation.md` 记录本机验证规则和结果。
- 当前应以用户本机验证结果判断 BaoStock 可用；Codex 沙盒网络失败只保留为环境限制记录。

2026-06-03 ETF 横截面排名报告：

- 新增 `reports/ranking_report.md` 和 `reports/latest_ranking.md`。
- 每次运行 `python3 src/main.py` 会自动生成 ETF 横截面强弱排名。
- 排名范围为 `enabled=1`、`role=trade_pool` 且本地有合格行情 CSV 的 ETF。
- 排名包含相对强弱、20 日涨幅、5 日涨幅、成交量改善、BUY/SELL 汇总、WATCH 最接近 BUY、group 强弱概览和数据缺失标的。
- `reports/latest_daily.md` 末尾已提示查看 `reports/latest_ranking.md`。
- Codex 每日/每周研究提示已纳入 `latest_ranking.md`。

2026-06-03 多因子评分、future returns 和因子分析：

- `reports/latest_ranking.md` 已新增 `composite_score Top 10`。
- `composite_score` 是 0-100 的辅助多因子评分，不改变 BUY / SELL / WATCH 规则。
- `watch_score` 已标准化到 0-100，用于辅助判断 WATCH 接近 BUY 程度。
- `reports/model_dataset.csv` 已新增 `composite_score`、`watch_score`、future returns 和 future rank 字段。
- future returns 字段包括：`future_5d_return`、`future_20d_return`、`future_60d_return`、`future_5d_rank`、`future_20d_rank`、`future_60d_rank`。
- future returns 只用于研究，严禁参与当日 signal、ranking、composite_score 或 watch_score 计算。
- 新增 `reports/factor_analysis_report.md` 和 `reports/latest_factor_analysis.md`。
- 当前样本只有最新截面，future returns 暂无可回填样本，因子报告会提示“样本不足，不应过度解读”。

2026-06-03 双周期 ETF 策略框架：

- 新增 `--strategy mid_trend / short_swing` 参数，默认 `mid_trend`。
- `mid_trend` 是主策略，占模拟资金 70%，目标持仓 20-60 个交易日，保留原 MA20/MA60/20 日相对强弱逻辑。
- `short_swing` 是实验策略，占模拟资金 30%，目标持仓 10-20 个交易日，使用 MA10/MA20/10 日相对强弱/成交量/距离 MA10。
- 新增 `reports/latest_short_swing.md`。
- `reports/latest_daily.md` 已加入 short_swing 短期信号和双周期共振信号。
- `reports/latest_ranking.md` 已加入 short_swing watch_score Top 10、双周期综合评分 Top 10、双周期共振 Top 10。
- 双周期决策矩阵已实现：`STRONG_RESONANCE`、`SHORT_TRIAL`、`MID_HOLD`、`RISK_ALERT`、`AVOID`、`OBSERVE`。
- 双周期共振时，short_swing 只能小仓补充；同一 ETF 合计暴露不超过总资产 35%，同一 group 总暴露不超过总资产 50%。
- 新增 `reports/strategy_compare_report.md`，支持 mid_trend 和 short_swing 回测对比。
- `backtest.py` 已支持 `--strategy mid_trend`、`--strategy short_swing`、`--all --compare-strategies`。
- 当前双周期信号中存在 `SHORT_TRIAL`：`512800` 银行ETF、`510880` 红利ETF；暂无 `STRONG_RESONANCE`。

2026-06-03 验证记录：

- `python3 -m py_compile src/*.py` 通过。
- `bash -n scripts/*.sh` 通过。
- `python3 src/main.py --fetch-data --start-date 2025-01-01 --end-date 2026-06-02` 可运行并生成数据日志、质量报告、日报、风险报告和模型数据集。
- `python3 src/main.py` 通过。
- `python3 src/main.py --weekly` 通过，并生成 `latest_weekly.md`。
- 两个 Codex 研究提示脚本均可生成 prompt 文件。
- 在 Codex 当前环境中，扩展池公开行情下载出现 DNS 失败，成功 3 个、失败 16 个；本机 cron 环境可继续验证更多标的。

## 当前阻塞

核心阻塞不再是“系统没有框架”，也不再是“行情完全下载不了”，而是“仍有部分标的行情下载失败”。

当前最需要解决的是：

1. 以用户本机 PyCharm/.venv 的 BaoStock 下载结果为准，继续维护本地 `data/*.csv`。
2. 每天优先查看 `reports/latest_daily.md` 和 `reports/latest_ranking.md`。
3. 根据 `reports/watchlist_health_report.md` 和 `reports/latest_ranking.md` 判断是否需要补数据或调整观察池。
4. 优先排查 `510500`、`588000` 这类无缓存且下载失败的宽基 ETF。
5. 根据 `reports/watchlist_health_report.md` 跟踪交易池可用率。
6. 根据 `reports/latest_daily.md` 和 `reports/codex_daily_research_prompt.md` 做第一轮 ETF 观察。

## 下一步优先级

第一优先级：开始 ETF 模拟盘测试前的报告和回测验证。

建议下一条命令：

```bash
cd /Users/dayin/Documents/量化学习/a-share-swing-system
cat reports/data_update_log.md
cat reports/data_quality_report.md
```

第二优先级：重新生成报告和回测。

```bash
python3 src/main.py
python3 src/main.py --weekly
python3 src/backtest.py --code 510300
python3 src/backtest.py --code 159915
python3 src/backtest.py --code 512100
python3 src/backtest.py --code 513500
```

第三优先级：进入第一周模拟盘测试。

- 每天收盘后运行每日信号。
- 只选择模拟交易，不真实下单。
- 如果决定模拟买入/卖出，手动写入 `trades.csv`。
- 周五生成周复盘，把报告交给 ChatGPT 做复盘分析。

## 新对话恢复方式

如果以后新开 Codex 对话，请先让 Codex 读取：

1. `PROJECT_STATE.md`
2. `DECISIONS.md`
3. `codex_tasks.md`
4. `CHATGPT_NOTES.md`
5. `reports/data_update_log.md`
6. `reports/data_quality_report.md`

然后再继续开发或跑数据。
