# PR #1 Final Hygiene Audit

审计日期：2026-07-12

分支：`agent/project-checkpoint-july-2026`

范围：PR #1 相对 `origin/main` 的 whitespace、生成器、临时文件、数据语义与受保护边界治理。

## 结论

- PR #1 Hygiene Cleanup：`COMPLETE`
- Diff Check：`CLEAN`
- Local Temporary Artifacts：`RESOLVED`
- PR #1：`READY_FOR_FINAL_MERGE_DECISION`
- Main Branch Merge：`NOT_EXECUTED`
- Tushare Staging / PIT：`NOT_STARTED`
- Formal Execution Logic：`UNCHANGED`

## 初始告警

`git diff --check origin/main...HEAD` 的初始输出为 3016 行。每条 trailing-whitespace 告警包含“位置行 + 内容行”，因此真实告警数为 1518，而不是 3016。

| 指标 | 数量 |
| --- | ---: |
| 原始输出行数 | 3016 |
| 真实告警 | 1518 |
| 涉及文件 | 60 |
| trailing whitespace | 1498 |
| new blank line at EOF | 20 |
| space before line ending | 1468（CSV CRLF，被 Git 识别为尾空白） |
| 其他类型 | 0 |

按文件类别：

| 类别 | 告警数 |
| --- | ---: |
| CSV_DATA | 1468 |
| GENERATED_JSON | 0 |
| GENERATED_MARKDOWN | 45 |
| SOURCE_CODE | 4 |
| TEST | 1 |
| DOCUMENTATION | 0 |
| OTHER | 0 |

全部 1518 条都位于相对 `origin/main` 的 PR 新增文件；主分支历史文件被整文件变化带入的告警为 0。可重复生成的告警为 1482 条：1468 条来自三个 CSV writer 的默认 CRLF，14 条来自 ChatGPT 周报生成器中的尾随双空格。其余 36 条是新增 Markdown、源码和测试文件中的一次性尾空白或 EOF 多余空行。

## 逐文件告警

以下 26 个 `data/manual_import/*.csv` 各 2 条，共 52 条：

```text
159736 159755 159819 159857 159869 159995 159996
512480 512980
515050 515070 515170 515230 515260 515630 515700 515790
516020 516080 516110 516160 516360 516510 516720 516800
588200
```

以下 6 个周报归档各 2 条，共 12 条：

```text
reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-06-26.md
reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-06-29.md
reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-06-30.md
reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-07-01.md
reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-07-03.md
reports/archive/chatgpt_packets/chatgpt_weekly_analysis_packet_2026-07-09.md
```

其余文件：

| 文件 | 告警数 |
| --- | ---: |
| `reports/file_classification_plan.csv` | 1065 |
| `reports/archive_candidate_list.csv` | 351 |
| `reports/chatgpt_weekly_analysis_packet_latest.md` | 2 |
| `reports/exposure_candidate_matrix.md` | 1 |
| `reports/exposure_data_contract.md` | 1 |
| `reports/exposure_gap_analysis.md` | 1 |
| `reports/exposure_phase_c_readiness.md` | 1 |
| `reports/exposure_point_in_time_rules.md` | 1 |
| `reports/exposure_taxonomy_design.md` | 1 |
| `reports/frontend_css_cleanup_audit.md` | 1 |
| `reports/multi_benchmark_framework.md` | 1 |
| `reports/paper_execution_freshness_gate_summary.md` | 2 |
| `reports/project_weekly_report_2026-07-10.md` | 2 |
| `reports/report_taxonomy_feasibility_study.md` | 3 |
| `reports/shadcn_card_density_audit.md` | 2 |
| `reports/shadcn_ui_compatibility_audit.md` | 2 |
| `reports/shadcn_ui_migration_phase1.md` | 1 |
| `reports/shadcn_ui_migration_phase2.md` | 2 |
| `reports/style_fit_failure_attribution.md` | 1 |
| `reports/style_fit_failure_postmortem.md` | 1 |
| `reports/style_fit_failure_tree.md` | 1 |
| `reports/trading_weekly_report_2026-07-10.md` | 4 |
| `reports/ui_visual_calibration_monochrome.md` | 2 |
| `scripts/run_exposure_prototype.py` | 1 |
| `src/execution/__init__.py` | 1 |
| `src/exposure/__init__.py` | 1 |
| `src/exposure/exposure_config.py` | 1 |
| `tests/paper_gate_test_utils.py` | 1 |

## 生成源修复

- `scripts/project_hygiene_audit.py`：`csv.DictWriter` 固定 `lineterminator="\n"`。
- `scripts/archive_low_risk_reports.py`：`csv.DictWriter` 固定 `lineterminator="\n"`。
- `scripts/download_manual_etf_history.py`：新增 `write_history_csv()`，固定 LF，同时继续使用原字段顺序和 DictWriter 序列化。
- `src/chatgpt_weekly_packet.py`：生成 Markdown 前统一删除无语义行尾空白并保留单一终止换行；模板不再写入尾随双空格。
- 新增回归测试覆盖三类 CSV writer 和 Markdown normalizer；定向测试 5 passed，全量测试 23 passed、8 subtests passed。

## CSV 数据语义一致性

清理严格限制为行尾 CR 删除，没有通过 pandas/csv 重新序列化既有文件。

- `reports/file_classification_plan.csv`：1065 行、8 列，header、UTF-8 编码和逐字段 canonical SHA-256 `9962e57d7626e12a0d414b3cb0095f463576a0f2f0dc48c6bb57e4503f1b6047` 前后相同。
- `reports/archive_candidate_list.csv`：351 行、10 列，header、UTF-8 编码和逐字段 canonical SHA-256 `231ca88b3347a5ff6a2c534b66dc7d03a691ee2bcdafa44dd67a265085a20ad8` 前后相同。
- 26 个 `data/manual_import` 单日文件均保持 2 行、7 列、同一 header、UTF-8 编码、日期 2026-07-08、逐字段 canonical SHA-256 前后相同。
- `python3 scripts/validate_manual_csv.py --all-etf`：52 valid，0 failed。
- `data/etf_daily/` 的 183 个 ETF CSV 未修改；未创建第二套同构行情库。

## 本地临时文件处置

17 个 Baostock batch/probe JSON 均为 `scripts/update_etf_data.py` 的可再生本地状态快照，不含唯一业务数据，不需要隔离，已删除：

```text
reports/data_update_status.baostock_20260710_batch_1.json
reports/data_update_status.baostock_20260710_batch_2.json
reports/data_update_status.baostock_20260710_batch_3.json
reports/data_update_status.baostock_20260710_batch_4.json
reports/data_update_status.baostock_20260710_batch_5.json
reports/data_update_status.baostock_20260710_batch_6.json
reports/data_update_status.baostock_20260710_full_batch_1.json
reports/data_update_status.baostock_20260710_full_batch_2.json
reports/data_update_status.baostock_20260710_full_batch_3.json
reports/data_update_status.baostock_20260710_full_batch_4.json
reports/data_update_status.baostock_batch_1.json
reports/data_update_status.baostock_batch_2.json
reports/data_update_status.baostock_batch_3.json
reports/data_update_status.baostock_batch_4.json
reports/data_update_status.baostock_batch_5.json
reports/data_update_status.baostock_probe.json
reports/data_update_status.baostock_probe_20260710.json
```

`reports/report_taxonomy_feasibility_study_副本.md` 与正式文件逐字节相同，不含唯一内容，已删除。隔离文件：无。

`.gitignore` 新增精确规则：

```gitignore
reports/data_update_status.baostock_*batch*.json
reports/data_update_status.baostock_probe*.json
reports/report_taxonomy_feasibility_study_副本.md
```

这些规则不会忽略正式的 `reports/data_update_status.baostock_fallback.json`。

## 验证

- full PR diff check：0 warnings。
- Python：23 passed，8 subtests passed；仅保留 2 个既有 Pytest collection warnings。
- Dashboard build：PASS。
- Frontend production build：PASS。
- App release check：PASS。
- Context validation/bootstrap：`VALID_WITH_WARNINGS`；唯一警告为既有 2026-07-06 Regime stale snapshot。
- 敏感信息与私人绝对路径扫描：无新增泄露。
- ETF 文件数：183；`data/etf_daily/` 未修改。
- 未处理 whitespace 例外：无。

## 受保护边界

本批次前后 SHA-256：

```text
src/paper_trade_engine.py  93b7a1ae87412838362463a7c23c233f5232a3363e554827a350999baa394926
data/paper_trades.csv       db853bee499bdb6f0245658fffb97d1ad5d133395604d9cf971ce3e5576481b5
data/paper_positions.csv    a031acb292a4d636603dfb95049005f11e7ae2663814e159880eee97832e4906
```

三份文件哈希不变。未修改 Formal Execution、Ranking、Score、策略逻辑或模拟账本。
