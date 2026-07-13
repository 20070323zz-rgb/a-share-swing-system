# Codex New Thread Prompt Template

Use this template when starting a new Codex thread for this project.

```text
项目路径：
<project_root>

这是已有长期项目，不是新项目。

Repository context is authoritative.
不要依赖旧 thread 记忆猜测项目状态。

开始任何实质性修改前：

1. 读取 AGENTS.md
2. 读取 docs/project_context_manifest.json
3. 按 manifest 的 bootstrap_read_order 读取全部 required context
4. 运行：
   python3 scripts/context/bootstrap_codex_context.py
5. 读取：
   reports/project_context_validation_latest.md
6. 读取 current_phase_status 指向的 current phase report / decision
7. 用中文先汇总：
   - main phase
   - phase status
   - current batch
   - resume_from
   - completed batches
   - selected shadow candidate
   - latest known snapshot date
   - readiness gates
   - protected files
   - validation status
   - warnings/conflicts
8. 如果 validation INVALID 或 blocking conflict：
   停止修改，先报告。
9. 如果有效：
   只从 resume_from 指定 Batch 继续。
10. 不依赖旧 thread 记忆猜测项目状态。
```

Notes:

- `VALID_WITH_WARNINGS` 不等于 `INVALID`。
- snapshot stale 时必须带日期表述，不得说成 live current。
- protected files 默认只读，除非当前任务明确授权 Formal Execution Change。
