# PR #1 路径脱敏审计

审计日期：2026-07-12

扫描范围：Draft PR #1 相对 `origin/main` 的全部变更文件

目标：消除个人用户目录与本机绝对路径，同时保持本地运行能力。

## 分类与处理

### A. 文档与仓库上下文路径

仓库根目录、旧目录和命令示例统一改为：

- `<project_root>`：当前 checkout 根目录；
- `<deprecated_project_root>`：仅用于标识旧位置，不代表可用路径。

涉及 `AGENTS.md`、新 thread bootstrap/prompt、current project state、local App release guide 以及历史治理报告。占位符语义已明确，不再暴露用户名或用户目录。

### B. 生产报告与运行产物

以下类型中的绝对路径已替换为 `<project_root>/...`：

- App task status 与 Dashboard snapshot；
- 数据源、更新状态、manual download、月报和绩效审计；
- Exposure/Regime manifest 与研究输出；
- context validation/recovery 和 project structure/path dependency 报告。

这些替换只改变路径表示，不改变数据值、研究结论或执行状态。

### C. 代码和运行配置

- `scripts/run_daily_close.sh`：从脚本位置动态计算 project root。
- `scripts/run_weekly_review.sh`：从脚本位置动态计算 project root。
- `scripts/create_app_shortcut.sh`：生成的 App launcher 从 bundle 相对位置计算 project root。
- `scripts/context/validate_project_context.py`：接受 `<project_root>` schema 值，并在输出中使用占位符。
- 研究报告模板中的 repository root 改为 `<project_root>`。

## 修改范围

第一轮扫描共处理 34 个已有 PR 文件、155 行；此外更新运行脚本、context validator 和 Dashboard snapshot producer，避免重新生成本机路径。

主要文件：

```text
AGENTS.md
data/research/exposure_prototype/*manifest.json
docs/codex_new_thread_bootstrap.md
docs/codex_new_thread_prompt_template.md
docs/current_phase_status.json
docs/current_project_state.md
docs/local_app_release_guide.md
reports/app_task_status.json
reports/dashboard_data.json
reports/data_provider_status.*
reports/data_update_status*.json
reports/manual_download_report.md
reports/paper_*_audit.md
reports/project_context_*
reports/project_structure_audit.*
reports/regime_*.json
scripts/create_app_shortcut.sh
scripts/run_daily_close.sh
scripts/run_weekly_review.sh
src/style_fit_evidence_qualification.py
src/style_fit_robustness.py
```

## 验收规则

合并前扫描命令必须在 PR 变更文件中返回零结果：

```bash
git diff --name-only "$(git merge-base origin/main HEAD)"..HEAD |
  while IFS= read -r file; do
    test -f "$file" && rg -n '/''Users/' "$file"
  done
```

允许 `<project_root>` 出现在报告、文档与结构化运行快照中；它是显式占位符，不是可执行的机器路径。
