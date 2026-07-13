# Path Dependency Audit

生成时间：2026-06-29 16:08:04

> 扫描范围：`src/`、`scripts/`、`dashboard/`、`app/backend/`、`app/frontend/src/`。本报告用于判断哪些路径不能贸然移动。

## 扫描摘要

- 命中总数：1091
- 命中文件数：76
- 搜索模式：`reports/`, `data/`, `dashboard/`, `app/`, `paper_trades.csv`, `paper_positions.csv`, `dashboard_data.json`, `chatgpt_weekly_analysis_packet_latest`, `paper_performance_summary`, `portfolio_exposure`, `position_review_state`, `profit_protection_preview`, `high_beta_risk_watch`, `broad_base_balance_preview`

## 按模式统计

- `reports/`: 547
- `data/`: 100
- `portfolio_exposure`: 92
- `paper_positions.csv`: 59
- `paper_trades.csv`: 51
- `dashboard/`: 41
- `position_review_state`: 35
- `broad_base_balance_preview`: 35
- `high_beta_risk_watch`: 30
- `profit_protection_preview`: 28
- `app/`: 21
- `dashboard_data.json`: 19
- `chatgpt_weekly_analysis_packet_latest`: 18
- `paper_performance_summary`: 15

## 路径依赖最多的文件

- `dashboard/build_dashboard.py`: 413
- `dashboard/index.html`: 218
- `src/chatgpt_weekly_packet.py`: 27
- `app/backend/safe_tasks.py`: 20
- `src/position_review_state.py`: 19
- `src/paper_trade_engine.py`: 18
- `src/model_research_quality_review.py`: 17
- `app/backend/readers.py`: 17
- `src/high_beta_risk_watch.py`: 15
- `src/next_stage_strategy_research.py`: 15
- `src/strategy_enhancement_preview.py`: 14
- `scripts/check_app_release.sh`: 14
- `src/paper_equity_backfill.py`: 13
- `src/broad_base_balance_preview.py`: 13
- `src/valuation_consistency_audit.py`: 12
- `scripts/check_app_env.sh`: 12
- `src/ranking_model_v2_backtest.py`: 11
- `src/data_source_architecture_audit.py`: 10
- `src/profit_protection_preview.py`: 10
- `src/persistence_breakout_shadow.py`: 10
- `scripts/run_daily_close.sh`: 10
- `src/strategy_preview_tracking.py`: 8
- `scripts/import_manual_csv.py`: 8
- `src/automation_nodes.py`: 7
- `scripts/build_etf_expansion_plan.py`: 7
- `dashboard/README.md`: 7
- `src/trade_review.py`: 6
- `src/paper_portfolio.py`: 6
- `src/sell_signal_review.py`: 6
- `src/portfolio_exposure.py`: 6
- `src/paper_performance.py`: 6
- `scripts/run_etf_expansion_data_pipeline.py`: 6
- `scripts/test_qmt_xtdata.py`: 6
- `src/tushare_staging_check.py`: 5
- `src/main.py`: 5
- `src/missed_opportunity_tracker.py`: 5
- `scripts/import_jqdata_staging.py`: 5
- `scripts/run_weekly_review.sh`: 5
- `src/shadow_observation_weekly.py`: 4
- `src/backtest_engine.py`: 4

## 不能移动的路径

- data/paper_trades.csv
- data/paper_positions.csv
- data/etf_daily/
- reports/dashboard_data.json
- latest_* reports
- dashboard/index.html
- app/backend/main.py
- scripts/run_daily_close.sh
- scripts/run_weekly_review.sh

## 可以配置化后再移动的路径

- `src/` 模块：需要先整理 import 和入口脚本。
- `scripts/` 维护脚本：需要先更新 README、launchd、App safe task 白名单。
- `reports/` 研究类报告：需要先更新 `dashboard/build_dashboard.py` 的 report links 和 App readers。
- `data/` 派生文件：需要先明确是正式账本、shadow 账本还是临时 staging。

## Dashboard / App 固定读取重点

- `reports/dashboard_data.json`
- `reports/paper_performance_summary.json`
- `reports/portfolio_exposure.json`
- `reports/position_review_state.json`
- `reports/profit_protection_preview.json`
- `reports/high_beta_risk_watch.json`
- `reports/broad_base_balance_preview.json`
- `reports/chatgpt_weekly_analysis_packet_latest.json`

## Weekly Review 固定链路重点

- `scripts/run_weekly_review.sh`
- `src/main.py --weekly`
- `src/automation_nodes.py --node weekly_full_review`
- `src/holding_period_research.py`
- `src/exit_rule_research.py`
- `src/parameter_sweep.py`
- `src/persistence_breakout_shadow.py`
- `src/missed_opportunity_tracker.py`
- `src/shadow_observation_weekly.py`
- `src/trade_review.py`
- `src/chatgpt_weekly_packet.py`
- `dashboard/build_dashboard.py`
