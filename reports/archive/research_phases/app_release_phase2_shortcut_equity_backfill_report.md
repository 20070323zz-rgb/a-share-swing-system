# App Release Phase 2 桌面快捷图标与权益曲线回填报告

生成时间：2026-06-22 23:25

## 目标

本轮完成两个本地正式版体验升级：

1. 为量化研究控制台创建更像普通 Mac App 的本地快捷入口。
2. 基于模拟交易流水和本地 ETF 历史收盘价，回填模拟仓历史权益曲线。

本轮没有接券商 API，没有真实下单，没有读取真实账户，没有修改交易规则。

## 快捷图标 / App 包装器

- App 包装器：`dist/量化研究控制台.app`
- 启动脚本：`scripts/run_app.sh`
- 生成脚本：`scripts/create_app_shortcut.sh`
- 图标 SVG：`assets/app_icon.svg`
- 图标 PNG：`assets/app_icon.png`
- 图标 ICNS：`dist/量化研究控制台.app/Contents/Resources/app_icon.icns`
- 日志路径：`logs/app_server.log`

使用方式：

1. 双击 `dist/量化研究控制台.app`。
2. 或双击 `打开量化研究控制台.command` 作为 fallback。
3. 可将 `dist/量化研究控制台.app` 拖到桌面或 Dock。

该 `.app` 只是本地启动包装器，不打包账号密码，不读取 `.env` 到前端，不接券商，不真实交易。

## 历史权益曲线记录较少的原因

早期模拟盘主要记录：

- `data/paper_trades.csv`
- `data/paper_positions.csv`

当时没有每天持续保存完整账户快照，因此原始 `data/paper_equity_curve.csv` 记录较少。历史权益曲线需要每日现金、持仓市值、总资产等快照数据；缺失快照后，只能通过交易流水和历史行情进行估算重建。

详细说明已生成：

- `reports/paper_equity_curve_gap_explanation.md`

## 回填结果

- 回填脚本：`src/paper_equity_backfill.py`
- 回填 CSV：`data/paper_equity_curve_backfilled.csv`
- 回填报告：`reports/paper_equity_curve_backfilled.md`
- 回填审计：`reports/paper_equity_curve_backfill_audit.md`

回填摘要：

- 原始权益曲线记录数：9
- 回填权益曲线记录数：15
- 回填起始日期：2026-06-08
- 回填结束日期：2026-06-22
- 初始本金：10,000 元
- 质量标记：
  - `estimated_good`：10 条
  - `estimated_carry_forward`：5 条

说明：

- 正式模拟仓权益曲线使用 10,000 元初始本金口径。
- 研究/回测默认 20,000 元不适用于当前正式模拟仓回填。
- 回填数据是估算数据，不是真实每日账户快照。
- 非交易日或缺价日会沿用最近可用 close，并标记 `estimated_carry_forward`。

## App / Dashboard 同步

已更新：

- `reports/dashboard_data.json`
- `dashboard/index.html`
- `app/backend/readers.py`
- `app/frontend/src/pages/Home.jsx`
- `app/frontend/src/pages/Portfolio.jsx`
- `app/frontend/src/pages/SettingsSafety.jsx`

App 行为：

- 如果 `data/paper_equity_curve_backfilled.csv` 存在且记录数更多，历史盈亏视图优先显示回填曲线。
- 页面明确标注“历史回填数据（估算）”。
- 首页显示本地 App 图标启动状态。
- 设置与安全页显示 `.app` 路径、启动器路径、日志路径和权益回填说明。

## daily_close

已确认并接入：

- `scripts/run_daily_close.sh` 会运行 `src/paper_performance.py`。
- 后续收盘链路会持续生成 `data/paper_equity_curve.csv`。
- 如果绩效生成失败，只记录 warning，不触碰真实交易，不中断核心报告链路。

## 新增安全任务

已加入 App 白名单任务：

- `run_paper_equity_backfill`：回填模拟仓历史权益曲线。
- `create_app_shortcut`：创建本地 App 快捷图标。

两者均为本地工具/研究任务，不接券商，不真实交易，不修改模拟交易流水和持仓。

## 验证

已通过：

- `python3 -m py_compile src/paper_equity_backfill.py dashboard/build_dashboard.py app/backend/readers.py app/backend/main.py app/backend/safe_tasks.py`
- `python3 src/paper_equity_backfill.py`
- `bash -n scripts/create_app_shortcut.sh`
- `bash scripts/create_app_shortcut.sh`
- `python3 dashboard/build_dashboard.py`
- `npm run build`
- `bash -n scripts/run_daily_close.sh`
- `bash scripts/check_app_release.sh`

## 关键文件指纹

- `data/paper_trades.csv`：`e3c43a6aee418666fb19460a7bb7ddeb846ced2220b8ab4030bda0d373666425`
- `data/paper_positions.csv`：`1ea405dc2e7bd7eaf1a98bd5b519f45fa1882c8657b66a84e083bee6654ff734`
- `src/paper_trade_engine.py`：`b51f30fc60777d6cb53ccf8bacc460d05082e55fa5b94f2d35a8bc7abddb9d2d`

## 安全边界

- 不接券商 API。
- 不真实下单。
- 不读取真实账户。
- 不读取券商 App。
- 不修改 `src/paper_trade_engine.py`。
- 不修改模型规则。
- 不把 shadow 模型接入正式模拟盘。
- 不扩池。
- 不显示 token / 密码 / 密钥。
- 不读取 `.env` 到前端。
- 不新增真实交易按钮。
- 不破坏原始 `paper_trades.csv` 和 `paper_positions.csv`。

结论：App Release Phase 2 已完成，本地 App 入口和模拟仓历史权益曲线展示能力均已升级，并保持 L2 安全边界不变。
