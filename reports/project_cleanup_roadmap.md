# Project Cleanup Roadmap

## Phase A：零风险整理

- 新增 `PROJECT_INDEX.md`、`docs/project_file_map.md`、`reports/report_index.md`。
- 保持 `data/`、`reports/latest_*`、`dashboard/`、`app/`、`scripts/run_*` 原路径。
- 只生成文件地图、路径依赖审计和归档候选清单。
- 不删除、不移动、不改 import。

## Phase B：低风险归档

- 将日期版历史报告归档到 `reports/archive/`。
- 保留所有 latest/current 报告原路径。
- 每次归档前运行 dashboard build、App build、release check。
- 仅对 `SAFE_TO_ARCHIVE` 且无依赖的文件执行。

## Phase C：结构化重构

- 先做路径配置化：统一 report/data path registry。
- 再考虑 `src/` 子包化、`scripts/` 分类、`reports/` 分类目录。
- 迁移前必须有回滚清单和自动化验证。
- 不在主策略迭代和数据更新高峰期做大规模移动。

## 禁止项

- 不移动 `data/paper_trades.csv`、`data/paper_positions.csv`。
- 不移动 `data/etf_daily/`。
- 不移动 `reports/dashboard_data.json`。
- 不改 `src/paper_trade_engine.py`。
- 不删除核心文件。
