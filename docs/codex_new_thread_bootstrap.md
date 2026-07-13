# Codex New Thread Bootstrap

## Purpose

新的 Codex thread 不应依赖旧 thread 记忆。

新的 Codex 对话必须从仓库状态恢复项目，不得依赖旧对话记忆猜测当前状态。

## Required Sequence

1. 定位 repository root：`<project_root>`。
2. 读取 `AGENTS.md`。
3. 读取 `docs/project_context_manifest.json`。
4. 按 `bootstrap_read_order` 读取上下文文件。
5. 运行 context validator：

```bash
python3 scripts/context/validate_project_context.py
```

6. 读取 `reports/project_context_validation_latest.md`。
7. 读取 `docs/current_phase_status.json` 指向的 phase report / decision。
8. 汇总当前项目状态。
9. 确认 `current_batch` / `resume_from`。
10. 才允许开始当前 Batch。

## Stop Conditions

以下情况必须停止实质性改动，先报告：

- `validation_status = INVALID`
- `blocking_conflict_found = true`
- `decision_state_conflict = true`
- required context file missing
- status schema invalid
- repository root mismatch

## Warning Conditions

以下情况可以继续读取，但必须声明：

- `regime_snapshot_stale = true`
- `project_state_snapshot_stale = true`

Example wording:

```text
Latest known shadow regime as of 2026-07-06 is NEUTRAL.
This snapshot is stale relative to latest data date.
```

Do not say:

```text
Current market regime is NEUTRAL.
```

unless the snapshot date is current for the data being discussed.

## Thread Memory Rule

Thread memory / Codex Memories can assist, but cannot override repository context.

Repository context is authoritative.

## No Blind Resume

Do not do this:

```text
用户说“继续”
→ 直接修改代码
```

Always bootstrap first, then resume only from the verified `resume_from` batch.

## Helper Command

For a concise bootstrap summary:

```bash
python3 scripts/context/bootstrap_codex_context.py
```

The helper is read-only except for the validator latest report output. It does not run models, dashboard, App, trading, or automatic fixes.
