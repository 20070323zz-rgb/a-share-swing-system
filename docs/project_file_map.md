# Project File Map

生成时间：2026-06-29 16:08:04

## 目录职责

- `app/`：动态 App，FastAPI + React/Vite。
- `dashboard/`：静态只读看板生成和输出。
- `data/`：ETF 日线、模拟盘账本、staging 和派生跟踪数据。
- `reports/`：所有最新报告、研究报告、审计报告和历史归档候选。
- `scripts/`：运行脚本、数据维护脚本、App 启动脚本。
- `src/`：核心模型、报告、研究、风险观察和组合分析模块。
- `docs/`：用户指南、规则和技术说明。
- `dist/`、`desktop/`、`assets/`：桌面 App 包装器和图标资源。
- `logs/`：本地自动化日志。

## 文件移动原则

- 先审计，后配置化，再迁移。
- latest/current 报告先不移动。
- 模拟盘账本和正式 ETF 日线不移动。
- App / dashboard / launchd 入口不移动。
- 日期版历史报告可以作为第一批归档候选。

## 详细清单

- 结构审计：`reports/project_structure_audit.md`
- 路径依赖：`reports/path_dependency_audit.md`
- 文件分类：`reports/file_classification_plan.csv`
- 整理路线：`reports/project_cleanup_roadmap.md`

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
