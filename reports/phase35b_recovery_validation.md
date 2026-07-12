# Phase 3.5B Recovery Validation

Validation timestamp: 2026-07-08

Scope: repository-only recovery validation. This report did not use prior conversation history, did not rerun robustness analysis, did not start Phase 3.5C, and did not modify Formal, shadow, preview, or execution logic.

## A. Artifact Inventory

Phase 3.5B engineering output is present as a dedicated research-only decision module plus report artifacts. The repository currently has a large pre-existing dirty worktree; most Phase 3.5B artifacts are untracked, so Git tracking status alone is not a reliable completeness test.

| Artifact | Type | Role | Status |
| --- | --- | --- | --- |
| `src/style_fit_evidence_qualification.py` | source | Phase 3.5B research-only generator and context updater | present |
| `reports/style_fit_robustness_evidence_integrity_audit.json` | json | source/integrity gate for Phase 3.5B | present |
| `reports/style_fit_robustness_evidence_integrity_audit.md` | markdown | human integrity summary | present |
| `reports/style_regime_evidence_qualification_matrix.csv` | csv | full 36-cell evidence qualification table | present |
| `reports/style_regime_evidence_qualification_matrix.json` | json | machine-readable full matrix, rules, and rows | present |
| `reports/style_regime_evidence_qualification_matrix.md` | markdown | human-readable full matrix | present |
| `reports/style_fit_high_beta_theme_qualification.json` | json | HIGH_BETA_THEME final treatment and cells | present |
| `reports/style_fit_high_beta_theme_qualification.md` | markdown | HIGH_BETA_THEME summary | present |
| `reports/style_fit_commodity_cyclical_qualification.json` | json | COMMODITY_CYCLICAL final treatment and cells | present |
| `reports/style_fit_commodity_cyclical_qualification.md` | markdown | COMMODITY_CYCLICAL summary | present |
| `reports/style_fit_incremental_signal_final_decision.json` | json | final incremental-signal decision | present |
| `reports/style_fit_incremental_signal_final_decision.md` | markdown | incremental-signal summary | present |
| `reports/style_fit_future_preview_research_scope.json` | json | future preview research scope and hard blocks | present |
| `reports/style_fit_future_preview_research_scope.md` | markdown | future preview scope summary | present |
| `reports/style_fit_evidence_qualification_summary.json` | json | aggregate counts and top cells | present |
| `reports/style_fit_evidence_qualification_summary.md` | markdown | aggregate summary | present |
| `reports/regime_layer_phase3_5b_decision.json` | json | final Phase 3.5B decision | present |
| `reports/regime_layer_phase3_5b_decision.md` | markdown | final Phase 3.5B decision summary | present |
| `docs/current_project_state.md` | state doc | project state updated from Phase 3.5B | present |
| `docs/current_phase_status.json` | state json | current batch/status updated to Phase 3.5C pending | present |
| `PROJECT_INDEX.md` | project index | changed, but diff shows context-continuity section rather than Phase 3.5B-specific conclusions | present |

Upstream evidence dependencies used by Phase 3.5B are also present, including Phase 3 style-regime outputs and Phase 3.5A robustness outputs. They are inputs, not newly produced Phase 3.5B conclusions.

## B. Research Recovery

Recovery source priority: `reports/regime_layer_phase3_5b_decision.json`, `reports/style_regime_evidence_qualification_matrix.json`, `reports/style_fit_evidence_qualification_summary.json`, special-style qualification JSON files, future preview scope JSON, and current state files.

### 1. Evidence Qualification Framework

Recovered framework:

- `QUALIFIED_SUPPORT`: positive Phase 3 evidence confirmed by ETF-level/core horizon/time evidence, without direction reversal or major sample/concentration warning.
- `CONDITIONAL_SUPPORT`: positive direction remains usable, but robustness is partial or confidence is capped by concentration, limited sample, weak excess, or sample dependence.
- `DESCRIPTIVE_ONLY`: label remains descriptive and is not eligible for future score-adjustment research.
- `UNSTABLE`: direction reversal or core instability blocks use in future adjusted-preview research.
- `QUALIFIED_CONFLICT`: Phase 3 conflict evidence confirmed by negative ETF-level/core horizon evidence without major caveats.
- `CONDITIONAL_CONFLICT`: weak negative research evidence only.
- `INSUFFICIENT`: effective sample or Phase 3 cell evidence is insufficient.

Confidence levels are `HIGH`, `MEDIUM`, `LOW`, and `INSUFFICIENT`. Future positive filter research is limited to `QUALIFIED_SUPPORT` and `CONDITIONAL_SUPPORT`; future negative filter research is limited to `QUALIFIED_CONFLICT` and `CONDITIONAL_CONFLICT`.

### 2. Evidence Categories

Recovered counts:

| Category | Count |
| --- | ---: |
| `QUALIFIED_SUPPORT` | 1 |
| `CONDITIONAL_SUPPORT` | 6 |
| `DESCRIPTIVE_ONLY` | 11 |
| `UNSTABLE` | 2 |
| `QUALIFIED_CONFLICT` | 1 |
| `CONDITIONAL_CONFLICT` | 3 |
| `INSUFFICIENT` | 12 |
| Total cells | 36 |

### 3. Qualified Evidence Cells

Qualified support:

- `COMMODITY_CYCLICAL` x `DEFENSIVE`: `QUALIFIED_SUPPORT`, confidence `HIGH`.

Qualified conflict:

- `SECTOR_DEFENSIVE` x `DEFENSIVE`: `QUALIFIED_CONFLICT`, confidence `HIGH`.

### 4. Conditional Cells

Conditional support:

- `BOND` x `NEUTRAL`
- `COMMODITY_CYCLICAL` x `OFFENSIVE`
- `CORE_MID_CAP` x `DEFENSIVE`
- `CORE_MID_CAP` x `OFFENSIVE`
- `HIGH_BETA_THEME` x `DEFENSIVE`
- `HIGH_BETA_THEME` x `OFFENSIVE`

Conditional conflict:

- `HIGH_BETA_THEME` x `NEUTRAL`
- `SECTOR_CYCLICAL` x `NEUTRAL`
- `SECTOR_DEFENSIVE` x `OFFENSIVE`

### 5. Descriptive-Only Cells

- `BOND` x `DEFENSIVE`
- `COMMODITY_CYCLICAL` x `NEUTRAL`
- `CORE_LARGE_CAP` x `DEFENSIVE`
- `CORE_LARGE_CAP` x `NEUTRAL`
- `CORE_LARGE_CAP` x `OFFENSIVE`
- `CORE_MID_CAP` x `NEUTRAL`
- `DIVIDEND` x `DEFENSIVE`
- `DIVIDEND` x `NEUTRAL`
- `DIVIDEND` x `OFFENSIVE`
- `SECTOR_CYCLICAL` x `DEFENSIVE`
- `SECTOR_CYCLICAL` x `OFFENSIVE`

### 6. Unstable Cells

- `BOND` x `OFFENSIVE`
- `SECTOR_DEFENSIVE` x `NEUTRAL`

### Additional Insufficient Cells

These are not research-usable:

- `GROWTH_BROAD` x `DEFENSIVE`, `NEUTRAL`, `OFFENSIVE`
- `GROWTH_THEME` x `DEFENSIVE`, `NEUTRAL`, `OFFENSIVE`
- `LOW_VOL` x `DEFENSIVE`, `NEUTRAL`, `OFFENSIVE`
- `QDII_OBSERVATION` x `DEFENSIVE`, `NEUTRAL`, `OFFENSIVE`

### 7. HIGH_BETA_THEME Final Treatment

Recovered conclusion: `MULTI_REGIME_SUPPORT_NOT_QUALIFIED`.

Recovered details:

- flags: `SAMPLE_DEPENDENCE_RISK`
- no `QUALIFIED_SUPPORT` cell exists
- `DEFENSIVE` and `OFFENSIVE` are `CONDITIONAL_SUPPORT`
- `NEUTRAL` is `CONDITIONAL_CONFLICT`
- eligible for future positive filter research: true
- eligible for future negative filter research: true

### 8. COMMODITY_CYCLICAL Final Treatment

Recovered conclusion: `CONDITIONAL_MULTI_REGIME_SUPPORT`.

Recovered details:

- flags: `TRUE_MULTI_REGIME_BEHAVIOR`
- `DEFENSIVE` is `QUALIFIED_SUPPORT`
- `OFFENSIVE` is `CONDITIONAL_SUPPORT`
- `NEUTRAL` is `DESCRIPTIVE_ONLY`
- eligible for future positive filter research: true
- eligible for future negative filter research: false

### 9. Incremental Signal Value

Recovered conclusion: `style_fit_has_incremental_signal_value = true`.

The final answer is `YES_WITH_ROBUSTNESS_CAVEAT`; robustness is `PARTIALLY_ROBUST`. Supporting views are pooled, time split, ETF-level, segment-level, and horizon checks, but the decision is downgraded because ETF-level overall robustness is `CONFLICTING`, one core aggregation comparison has direction reversal, and the major robustness warning remains active.

### 10. Fit Shadow Observation Readiness

Recovered conclusion: `ready_for_fit_shadow_observation = true`.

### 11. Adjusted Preview Research Readiness

Recovered conclusion: `ready_for_adjusted_preview_research = true`.

This means future research scope is defined. It does not mean adjusted preview scoring is authorized.

### 12. Preview Block

Recovered conclusion: preview remains blocked.

Evidence:

- `ready_for_preview = false`
- `ready_for_execution = false`
- `execution_allowed = false`
- `score_bonus_allowed = false`
- `score_penalty_allowed = false`
- `raw_ranking_must_remain_unchanged = true`

No requested conclusion required `RECOVERY_INCOMPLETE`.

## C. Consistency Audit

Mechanical cross-checks found no contradictions among the Phase 3.5B decision JSON, qualification summary JSON, full matrix JSON, special-style JSON files, future preview scope JSON, Markdown summaries, `docs/current_project_state.md`, and `docs/current_phase_status.json`.

Consistency results:

- Matrix counts equal summary counts and decision counts.
- HIGH_BETA_THEME interpretation matches between special-style JSON and Phase 3.5B decision JSON.
- COMMODITY_CYCLICAL interpretation matches between special-style JSON and Phase 3.5B decision JSON.
- Incremental-signal robustness and final answer match between incremental decision JSON and Phase 3.5B decision JSON.
- Readiness and execution-safety flags match between `docs/current_phase_status.json` and `reports/regime_layer_phase3_5b_decision.json`.
- Markdown summaries contain the same key readiness and safety values as JSON.
- `docs/current_phase_status.json` marks `last_completed_batch = Phase 3.5B`, `current_batch = Phase 3.5C`, and `current_batch_status = PENDING`, which is consistent with Phase 3.5B completion without starting Phase 3.5C.

Notable non-contradiction:

- `docs/current_project_state.md` says the broader Phase 3.5 track is still `IN_PROGRESS` while Phase 3.5B is `COMPLETE`. This is consistent because Phase 3.5C and Phase 3.5D remain pending.

## D. Recovery Assessment

Classification: `FULL_RECOVERY`

Justification:

- All expected Phase 3.5B engineering artifacts are present.
- The full 36-cell research matrix is recoverable in CSV, JSON, and Markdown.
- Aggregate counts, special-style treatments, readiness flags, and execution blocks are explicitly encoded.
- No target conclusion from the validation request required `RECOVERY_INCOMPLETE`.
- Current project state is internally consistent and safe to continue from repository context.

This is full recovery of Phase 3.5B conclusions, not full recovery of every private reasoning step that may have occurred during the previous thread.

## E. Missing Research Memory

The repository preserves the formal conclusions and concise qualification reasons, but it does not fully preserve all possible reasoning context. The following are not recoverable beyond what the artifacts explicitly say:

- rejected hypotheses considered during Phase 3.5B, if any;
- alternative interpretations that were discussed but not selected;
- detailed reasoning behind each downgrade beyond the stored `qualification_reason` strings and robustness flags;
- why some future research directions were preferred over other possible designs;
- any conversational confidence calibration that did not become a report, JSON field, or state-file note.

These gaps do not block recovery of the Phase 3.5B decision state.

## Final Chinese Summary

1. Phase 3.5B 是否完全可恢复：可以。以仓库为唯一来源，Phase 3.5B 的工程产物、36 个 style-regime cell 的证据分级、最终决策、preview 阻断状态和 Phase 3.5C pending 状态都能恢复。

2. 已保存的研究记忆：证据分级框架、全部 cell 的最终分级、HIGH_BETA_THEME 与 COMMODITY_CYCLICAL 的最终处理、增量信号价值的保留但降级结论、shadow observation 与 adjusted preview research 的 readiness，以及 preview/execution 仍被禁止的安全边界。

3. 已丢失或不可从仓库确认的研究记忆：被否决的假设、未写入报告的解释路径、每个降级背后的更细推理、未来研究方向选择背后的对比讨论。不要补写这些内容。

4. 是否可以安全进入 Phase 3.5C：可以。仓库状态显示 `ready_for_phase_3_5c = true`，`current_batch = Phase 3.5C`，`current_batch_status = PENDING`。但 Phase 3.5C 仍不能创建 adjusted preview，不能改 BUY ranking，不能接执行。

5. 长期研究上下文持久化建议：后续每个研究批次应继续保存机器可读 JSON、人工可读 Markdown、完整 cell-level matrix、关键 downgrade rationale、rejected-hypotheses/alternatives 小节，以及 state-file 的 batch boundary。这样即使对话丢失，Main 也能从仓库完整恢复结论和主要推理。
