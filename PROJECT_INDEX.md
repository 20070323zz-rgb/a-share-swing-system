# A-share Swing System Project Index

生成时间：2026-06-29 16:08:04

## 当前阶段

项目处于 ETF 双周期模拟盘 + 研究观察层阶段。正式执行层仍保持模拟盘，不接券商 API，不真实下单。

## 核心入口

- App 后端：`app/backend/main.py`
- App 前端：`app/frontend/`
- 静态看板：`dashboard/index.html`
- 看板生成：`dashboard/build_dashboard.py`
- 每日收盘：`scripts/run_daily_close.sh`
- 每周复盘：`scripts/run_weekly_review.sh`
- 本地 App 启动：`打开量化研究控制台.command`

## 核心数据

- ETF 日线：`data/etf_daily/`
- 模拟交易流水：`data/paper_trades.csv`
- 模拟持仓：`data/paper_positions.csv`
- 看板数据：`reports/dashboard_data.json`

## 核心报告

- 每日摘要：`reports/latest_brief.md`
- 模拟盘：`reports/latest_paper_portfolio.md`
- BUY ranking：`reports/buy_signal_ranking.md`
- 卖出复核：`reports/sell_signal_review.md`
- 周报分析包：`reports/chatgpt_weekly_analysis_packet_latest.md`
- 数据健康：`reports/latest_data_health.md`
- 数据覆盖：`reports/latest_data_coverage.md`

## 不要随意移动

- `data/paper_trades.csv`
- `data/paper_positions.csv`
- `data/etf_daily/`
- `reports/dashboard_data.json`
- `dashboard/index.html`
- `app/backend/main.py`
- `scripts/run_daily_close.sh`
- `scripts/run_weekly_review.sh`
- `src/paper_trade_engine.py`

## 本轮审计报告

- `reports/project_structure_audit.md`
- `reports/path_dependency_audit.md`
- `reports/file_classification_plan.md`
- `reports/recommended_project_layout.md`
- `reports/project_cleanup_roadmap.md`
- `reports/report_index.md`

## 历史报告归档说明

最近一次低风险归档时间：2026-06-29 22:15:43

- 历史报告目录：`reports/archive/`
- daily 历史报告：`reports/archive/daily/`
- weekly 历史报告：`reports/archive/weekly/`
- ChatGPT/Main 历史分析包：`reports/archive/chatgpt_packets/`
- 旧阶段研究/发布报告：`reports/archive/research_phases/`
- 其他日期版历史记录：`reports/archive/legacy_misc/`
- latest/current 活跃报告仍保留在 `reports/` 根目录。
- 本轮归档移动文件数：35
