"""Style-Regime Fit evidence qualification.

Regime Layer Phase 3.5B research-only decision module. It reads Phase 3
Style-Regime Fit evidence and Phase 3.5A robustness evidence, then qualifies
each style x stable-regime cell for future research use.

It does not modify BUY ranking, raw ranking scores, market_regime,
ASYMMETRIC_CONFIRM, adjusted preview, tracking, dashboard, app, paper trades,
paper positions, or execution code.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config import PROJECT_ROOT, REPORT_DIR


PHASE3_MATRIX_CSV = REPORT_DIR / "style_regime_fit_matrix.csv"
PHASE3_MATRIX_JSON = REPORT_DIR / "style_regime_fit_matrix.json"
PHASE3_SUMMARY_JSON = REPORT_DIR / "style_regime_fit_summary.json"
PHASE3_SIGNAL_JSON = REPORT_DIR / "style_fit_signal_interaction.json"
PHASE3_DECISION_JSON = REPORT_DIR / "style_regime_fit_phase_decision.json"
PHASE3_REPORT_JSON = REPORT_DIR / "regime_layer_phase3_style_fit.json"

SOURCE_AUDIT_JSON = REPORT_DIR / "style_fit_robustness_source_audit.json"
TIME_JSON = REPORT_DIR / "style_fit_time_robustness.json"
ETF_JSON = REPORT_DIR / "style_fit_etf_level_robustness.json"
SEGMENT_JSON = REPORT_DIR / "style_fit_regime_segment_robustness.json"
HORIZON_JSON = REPORT_DIR / "style_fit_horizon_robustness.json"
HIGH_BETA_JSON = REPORT_DIR / "style_fit_high_beta_theme_audit.json"
COMMODITY_JSON = REPORT_DIR / "style_fit_commodity_cyclical_audit.json"
INCREMENTAL_JSON = REPORT_DIR / "style_fit_incremental_value_robustness.json"
CORE_SUMMARY_JSON = REPORT_DIR / "style_fit_robustness_core_summary.json"
PHASE3_5A_DECISION_JSON = REPORT_DIR / "regime_layer_phase3_5a_decision.json"

INTEGRITY_JSON = REPORT_DIR / "style_fit_robustness_evidence_integrity_audit.json"
INTEGRITY_MD = REPORT_DIR / "style_fit_robustness_evidence_integrity_audit.md"
QUAL_MATRIX_CSV = REPORT_DIR / "style_regime_evidence_qualification_matrix.csv"
QUAL_MATRIX_JSON = REPORT_DIR / "style_regime_evidence_qualification_matrix.json"
QUAL_MATRIX_MD = REPORT_DIR / "style_regime_evidence_qualification_matrix.md"
HIGH_BETA_QUAL_JSON = REPORT_DIR / "style_fit_high_beta_theme_qualification.json"
HIGH_BETA_QUAL_MD = REPORT_DIR / "style_fit_high_beta_theme_qualification.md"
COMMODITY_QUAL_JSON = REPORT_DIR / "style_fit_commodity_cyclical_qualification.json"
COMMODITY_QUAL_MD = REPORT_DIR / "style_fit_commodity_cyclical_qualification.md"
INCREMENTAL_FINAL_JSON = REPORT_DIR / "style_fit_incremental_signal_final_decision.json"
INCREMENTAL_FINAL_MD = REPORT_DIR / "style_fit_incremental_signal_final_decision.md"
PREVIEW_SCOPE_JSON = REPORT_DIR / "style_fit_future_preview_research_scope.json"
PREVIEW_SCOPE_MD = REPORT_DIR / "style_fit_future_preview_research_scope.md"
QUAL_SUMMARY_JSON = REPORT_DIR / "style_fit_evidence_qualification_summary.json"
QUAL_SUMMARY_MD = REPORT_DIR / "style_fit_evidence_qualification_summary.md"
PHASE3_5B_DECISION_JSON = REPORT_DIR / "regime_layer_phase3_5b_decision.json"
PHASE3_5B_DECISION_MD = REPORT_DIR / "regime_layer_phase3_5b_decision.md"

CORE_HORIZONS = [5, 10, 20]
REGIMES = ["OFFENSIVE", "NEUTRAL", "DEFENSIVE"]
SUPPORT_EVIDENCE = {"SUPPORTED", "WEAK_SUPPORT"}
CONFLICT_EVIDENCE = {"CONFLICT", "WEAK_CONFLICT"}
POSITIVE_QUALIFICATIONS = {"QUALIFIED_SUPPORT", "CONDITIONAL_SUPPORT"}
NEGATIVE_QUALIFICATIONS = {"QUALIFIED_CONFLICT", "CONDITIONAL_CONFLICT"}
DISALLOWED_QUALIFICATIONS = {"DESCRIPTIVE_ONLY", "UNSTABLE", "INSUFFICIENT"}
QUALIFICATIONS = POSITIVE_QUALIFICATIONS | NEGATIVE_QUALIFICATIONS | DISALLOWED_QUALIFICATIONS
CONFIDENCE_VALUES = {"HIGH", "MEDIUM", "LOW", "INSUFFICIENT"}

MIN_PHASE3_SAMPLE = 30
MIN_ETF_COUNT_FOR_FULL_CONFIDENCE = 3
QUALIFIED_EXCESS_FLOOR = 0.0
CONDITIONAL_EXCESS_FLOOR = -0.003
CONFIDENCE_RANK = {"HIGH": 4, "MEDIUM": 3, "LOW": 2, "INSUFFICIENT": 1}
FLAG_RANK = {
    "INSUFFICIENT": 0,
    "NO_MATERIAL_SHIFT": 1,
    "LOW": 1,
    "MODERATE_SHIFT": 2,
    "MODERATE": 2,
    "DIRECTION_REVERSAL": 3,
    "HIGH": 3,
}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    integrity = build_integrity_audit(inputs)
    _write_json(INTEGRITY_JSON, integrity)
    INTEGRITY_MD.write_text(render_integrity_audit(integrity), encoding="utf-8")
    if integrity["blocking_evidence_conflict_found"]:
        print("Phase 3.5B evidence integrity audit blocked qualification.")
        return

    matrix_payload = build_qualification_matrix(inputs)
    high_beta = build_special_qualification(matrix_payload, inputs, "HIGH_BETA_THEME")
    commodity = build_special_qualification(matrix_payload, inputs, "COMMODITY_CYCLICAL")
    incremental = build_incremental_final_decision(inputs)
    preview_scope = build_future_preview_scope(matrix_payload, incremental)
    summary = build_qualification_summary(matrix_payload)
    decision = build_phase3_5b_decision(
        integrity,
        matrix_payload,
        high_beta,
        commodity,
        incremental,
        preview_scope,
        summary,
    )

    write_matrix_outputs(matrix_payload)
    _write_json(HIGH_BETA_QUAL_JSON, high_beta)
    HIGH_BETA_QUAL_MD.write_text(render_special_qualification(high_beta), encoding="utf-8")
    _write_json(COMMODITY_QUAL_JSON, commodity)
    COMMODITY_QUAL_MD.write_text(render_special_qualification(commodity), encoding="utf-8")
    _write_json(INCREMENTAL_FINAL_JSON, incremental)
    INCREMENTAL_FINAL_MD.write_text(render_incremental_final_decision(incremental), encoding="utf-8")
    _write_json(PREVIEW_SCOPE_JSON, preview_scope)
    PREVIEW_SCOPE_MD.write_text(render_preview_scope(preview_scope), encoding="utf-8")
    _write_json(QUAL_SUMMARY_JSON, summary)
    QUAL_SUMMARY_MD.write_text(render_qualification_summary(summary), encoding="utf-8")
    _write_json(PHASE3_5B_DECISION_JSON, decision)
    PHASE3_5B_DECISION_MD.write_text(render_phase3_5b_decision(decision), encoding="utf-8")

    if decision["ready_for_phase_3_5c"] and not decision["blocking_methodology_issue_found"]:
        update_project_context(decision, summary, high_beta, commodity, incremental, preview_scope)

    print("style_fit_evidence_qualification Phase 3.5B complete")
    print(f"qualification cells: {summary['total_cells']}")
    print(f"ready_for_phase_3_5c: {decision['ready_for_phase_3_5c']}")
    print(f"written: {PHASE3_5B_DECISION_MD}")


def load_inputs() -> dict[str, Any]:
    return {
        "phase3_matrix_csv": _read_csv(PHASE3_MATRIX_CSV),
        "phase3_matrix": _read_json(PHASE3_MATRIX_JSON),
        "phase3_summary": _read_json(PHASE3_SUMMARY_JSON),
        "phase3_signal": _read_json(PHASE3_SIGNAL_JSON),
        "phase3_decision": _read_json(PHASE3_DECISION_JSON),
        "phase3_report": _read_json(PHASE3_REPORT_JSON),
        "source_audit": _read_json(SOURCE_AUDIT_JSON),
        "time": _read_json(TIME_JSON),
        "etf": _read_json(ETF_JSON),
        "segment": _read_json(SEGMENT_JSON),
        "horizon": _read_json(HORIZON_JSON),
        "high_beta": _read_json(HIGH_BETA_JSON),
        "commodity": _read_json(COMMODITY_JSON),
        "incremental": _read_json(INCREMENTAL_JSON),
        "core_summary": _read_json(CORE_SUMMARY_JSON),
        "phase3_5a_decision": _read_json(PHASE3_5A_DECISION_JSON),
    }


def build_integrity_audit(inputs: dict[str, Any]) -> dict[str, Any]:
    source = inputs["source_audit"]
    core = inputs["core_summary"]
    decision = inputs["phase3_5a_decision"]
    checks = {
        "source_audit_valid": bool(source) and not bool(source.get("blocking_conflict_found")),
        "future_leakage_found": bool(source.get("future_leakage_found", True)),
        "benchmark_labels_evaluation_only": bool(source.get("benchmark_labels_evaluation_only")),
        "time_evidence_available": bool(inputs["time"].get("rows")),
        "etf_level_evidence_available": bool(inputs["etf"].get("rows")),
        "segment_evidence_available": bool(inputs["segment"].get("rows")),
        "horizon_evidence_available": bool(inputs["horizon"].get("rows")),
        "high_beta_theme_audit_available": bool(inputs["high_beta"].get("rows")),
        "commodity_cyclical_audit_available": bool(inputs["commodity"].get("rows")),
        "incremental_value_evidence_available": bool(inputs["incremental"].get("rows")),
        "phase3_5a_decision_available": bool(decision),
    }
    compare_keys = [
        "time_robustness_classification",
        "etf_level_robustness_classification",
        "segment_robustness_classification",
        "horizon_robustness_classification",
        "incremental_value_robustness_preliminary",
        "major_robustness_warning_found",
        "blocking_methodology_issue_found",
        "ready_for_phase_3_5b",
        "ready_for_preview",
        "ready_for_execution",
    ]
    mismatches = {
        key: {"decision": decision.get(key), "core_summary": core.get(key)}
        for key in compare_keys
        if decision.get(key) != core.get(key)
    }
    checks["phase3_5a_decision_consistent"] = not mismatches
    checks["ready_for_phase_3_5b"] = bool(decision.get("ready_for_phase_3_5b"))
    blocking = (
        not checks["source_audit_valid"]
        or checks["future_leakage_found"]
        or not checks["benchmark_labels_evaluation_only"]
        or not all(
            checks[k]
            for k in [
                "time_evidence_available",
                "etf_level_evidence_available",
                "segment_evidence_available",
                "horizon_evidence_available",
                "high_beta_theme_audit_available",
                "commodity_cyclical_audit_available",
                "incremental_value_evidence_available",
                "phase3_5a_decision_available",
                "phase3_5a_decision_consistent",
                "ready_for_phase_3_5b",
            ]
        )
        or decision.get("ready_for_preview") is not False
        or decision.get("ready_for_execution") is not False
    )
    return {
        "evidence_integrity_version": 1,
        "generated_at": _now(),
        **checks,
        "classification_mismatches": mismatches,
        "phase3_5a_ready_for_preview": decision.get("ready_for_preview"),
        "phase3_5a_ready_for_execution": decision.get("ready_for_execution"),
        "blocking_evidence_conflict_found": bool(blocking),
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def build_qualification_matrix(inputs: dict[str, Any]) -> dict[str, Any]:
    summary_rows = inputs["phase3_summary"].get("rows", [])
    matrix_lookup = build_phase3_matrix_lookup(inputs["phase3_matrix_csv"])
    etf_lookup = build_robustness_lookup(inputs["etf"].get("rows", []), "etf")
    segment_lookup = build_robustness_lookup(inputs["segment"].get("rows", []), "segment")
    special_flags = {
        "HIGH_BETA_THEME": sorted(set(inputs["high_beta"].get("flags", []))),
        "COMMODITY_CYCLICAL": sorted(set(inputs["commodity"].get("flags", []))),
    }
    special_rows = {
        "HIGH_BETA_THEME": rows_by_regime(inputs["high_beta"].get("rows", [])),
        "COMMODITY_CYCLICAL": rows_by_regime(inputs["commodity"].get("rows", [])),
    }
    global_context = {
        "time_robustness_classification": inputs["core_summary"].get("time_robustness_classification"),
        "etf_level_robustness_classification": inputs["core_summary"].get("etf_level_robustness_classification"),
        "segment_robustness_classification": inputs["core_summary"].get("segment_robustness_classification"),
        "horizon_robustness_classification": inputs["core_summary"].get("horizon_robustness_classification"),
        "time_direction": time_direction(inputs["time"].get("rows", [])),
        "horizon_directions": inputs["core_summary"].get("horizon_directions", {}),
    }
    rows = []
    for cell in summary_rows:
        style = str(cell["style_profile"])
        regime = str(cell["regime"])
        evidence = str(cell.get("overall_fit_evidence", "INSUFFICIENT"))
        signal_group = signal_group_for_evidence(evidence)
        core = {h: matrix_lookup.get((regime, style, h), {}) for h in CORE_HORIZONS}
        etf_rows = [etf_lookup.get((regime, style, signal_group, h), {}) for h in CORE_HORIZONS]
        segment_rows = [segment_lookup.get((regime, style, signal_group, h), {}) for h in CORE_HORIZONS]
        flags = list(special_flags.get(style, []))
        special_row = special_rows.get(style, {}).get(regime, {})
        if special_row and _float(special_row.get("etf_count")) < MIN_ETF_COUNT_FOR_FULL_CONFIDENCE:
            flags.append("LIMITED_ETF_COUNT")

        phase3_sample = _maybe_float(cell.get("sample_count_10d"))
        phase3_median = _maybe_float(cell.get("median_return_10d"))
        phase3_excess = _maybe_float(cell.get("benchmark_excess_median_10d"))
        phase3_positive_rate = _maybe_float(core[10].get("positive_rate"))
        horizon_cell_directions = {h: phase3_horizon_direction(core[h].get("fit_evidence")) for h in CORE_HORIZONS}
        pooling_flag = max_flag([r.get("pooling_bias_flag") for r in etf_rows])
        segment_flag = max_flag([r.get("segment_concentration_flag") for r in segment_rows])
        etf_direction = aggregate_metric_direction(etf_rows, "etf_median_of_medians")
        segment_direction = aggregate_metric_direction(segment_rows, "segment_median_return_median")
        if segment_direction == "INSUFFICIENT":
            segment_direction = special_segment_direction(special_row)
        qualification, confidence, reason = qualify_cell(
            evidence=evidence,
            phase3_sample=phase3_sample,
            phase3_excess=phase3_excess,
            horizon_cell_directions=horizon_cell_directions,
            time_classification=global_context["time_robustness_classification"],
            etf_direction=etf_direction,
            pooling_bias_flag=pooling_flag,
            segment_direction=segment_direction,
            segment_flag=segment_flag,
            horizon_classification=global_context["horizon_robustness_classification"],
            special_flags=sorted(set(flags)),
        )
        rows.append({
            "style_profile": style,
            "stable_regime": regime,
            "phase3_evidence_level": evidence,
            "phase3_sample_count": _int_or_none(phase3_sample),
            "phase3_median_forward_return": _round(phase3_median),
            "phase3_benchmark_excess_median": _round(phase3_excess),
            "phase3_positive_rate": _round(phase3_positive_rate),
            "time_robustness_direction": global_context["time_direction"],
            "time_robustness_classification": global_context["time_robustness_classification"],
            "etf_level_direction": etf_direction,
            "etf_level_robustness_classification": global_context["etf_level_robustness_classification"],
            "pooling_bias_flag": pooling_flag,
            "segment_direction": segment_direction,
            "segment_robustness_classification": global_context["segment_robustness_classification"],
            "segment_concentration_flag": segment_flag,
            "horizon_5d_direction": horizon_cell_directions[5],
            "horizon_10d_direction": horizon_cell_directions[10],
            "horizon_20d_direction": horizon_cell_directions[20],
            "horizon_robustness_classification": global_context["horizon_robustness_classification"],
            "special_style_flags": ";".join(sorted(set(flags))),
            "final_research_qualification": qualification,
            "qualification_reason": reason,
            "eligible_for_future_positive_filter_research": qualification in POSITIVE_QUALIFICATIONS,
            "eligible_for_future_negative_filter_research": qualification in NEGATIVE_QUALIFICATIONS,
            "evidence_confidence": confidence,
            "qualification_score": qualification_score(confidence, phase3_excess, phase3_sample, qualification),
            "research_only": True,
            "shadow_only": True,
            "execution_allowed": False,
        })
    return {
        "generated_at": _now(),
        "qualification_version": 1,
        "rules": qualification_rules_payload(),
        "rows": sorted(rows, key=lambda r: (r["style_profile"], r["stable_regime"])),
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def qualify_cell(
    *,
    evidence: str,
    phase3_sample: float | None,
    phase3_excess: float | None,
    horizon_cell_directions: dict[int, str],
    time_classification: str,
    etf_direction: str,
    pooling_bias_flag: str,
    segment_direction: str,
    segment_flag: str,
    horizon_classification: str,
    special_flags: list[str],
) -> tuple[str, str, str]:
    if evidence == "INSUFFICIENT" or not phase3_sample or phase3_sample < MIN_PHASE3_SAMPLE:
        return "INSUFFICIENT", "INSUFFICIENT", "Phase 3 cell sample is insufficient."

    core_support = sum(1 for v in horizon_cell_directions.values() if v == "SUPPORTIVE")
    core_conflict = sum(1 for v in horizon_cell_directions.values() if v == "CONFLICTING")
    sample_dependence = any(flag in special_flags for flag in {"SAMPLE_DEPENDENCE_RISK", "LIMITED_ETF_COUNT"})
    high_concentration = segment_flag == "HIGH"
    moderate_concentration = segment_flag == "MODERATE"
    etf_reversal = pooling_bias_flag == "DIRECTION_REVERSAL"
    etf_full_enough = pooling_bias_flag == "NO_MATERIAL_SHIFT" and etf_direction not in {"INSUFFICIENT", "MIXED"}
    segment_readable = segment_direction not in {"INSUFFICIENT", "MIXED"}
    horizon_ok = horizon_classification == "ROBUST_SUPPORT"
    time_ok = time_classification in {"ROBUST_SUPPORT", "PARTIAL_SUPPORT"}
    segment_supportive = segment_direction in {"POSITIVE", "MIXED_POSITIVE"} or segment_flag in {"LOW", "MODERATE", "INSUFFICIENT"}
    segment_conflict = segment_direction in {"NEGATIVE", "MIXED_NEGATIVE"} or segment_flag in {"LOW", "MODERATE", "INSUFFICIENT"}

    if evidence in SUPPORT_EVIDENCE:
        if etf_reversal or etf_direction == "NEGATIVE" or high_concentration:
            return "UNSTABLE", "LOW", f"Positive Phase 3 evidence is blocked by ETF/segment instability: etf={etf_direction}, pooling={pooling_bias_flag}, segment_flag={segment_flag}."
        if core_support >= 2 and etf_direction in {"POSITIVE", "MIXED_POSITIVE"} and time_ok and horizon_ok and segment_supportive:
            if etf_full_enough and segment_readable and not sample_dependence and not moderate_concentration and (phase3_excess or 0.0) >= QUALIFIED_EXCESS_FLOOR:
                return "QUALIFIED_SUPPORT", "HIGH", "Phase 3 support is confirmed by positive ETF-level evidence, supportive core horizons, and no major concentration or sample-dependence flag."
            if (phase3_excess or 0.0) >= CONDITIONAL_EXCESS_FLOOR:
                return "CONDITIONAL_SUPPORT", "MEDIUM", "Support direction remains usable for future research, but confidence is capped by partial segment evidence, weak excess, concentration, or sample-dependence caveat."
            return "DESCRIPTIVE_ONLY", "LOW", "Positive pooled evidence is not strong enough after benchmark-excess and robustness caveats."
        if core_support >= 2 and etf_direction in {"INSUFFICIENT", "MIXED"}:
            return "DESCRIPTIVE_ONLY", "LOW", "Phase 3 support is mainly descriptive because strict ETF-level evidence is incomplete or mixed."
        return "UNSTABLE", "LOW", "Positive Phase 3 evidence does not survive cell-level robustness checks."

    if evidence in CONFLICT_EVIDENCE:
        if etf_reversal or etf_direction == "POSITIVE" or high_concentration:
            return "UNSTABLE", "LOW", f"Conflict Phase 3 evidence is blocked by ETF/segment instability: etf={etf_direction}, pooling={pooling_bias_flag}, segment_flag={segment_flag}."
        if core_conflict >= 2 and etf_direction in {"NEGATIVE", "MIXED_NEGATIVE"} and segment_conflict:
            if etf_full_enough and segment_readable and not sample_dependence and not moderate_concentration:
                return "QUALIFIED_CONFLICT", "HIGH", "Phase 3 conflict is confirmed by negative ETF-level evidence and conflict-oriented core horizons."
            return "CONDITIONAL_CONFLICT", "MEDIUM", "Conflict direction remains usable only as weak negative research evidence because robustness is partial."
        if core_conflict >= 2:
            return "CONDITIONAL_CONFLICT", "MEDIUM", "Phase 3 conflict direction is present but ETF/segment evidence is incomplete."
        return "DESCRIPTIVE_ONLY", "LOW", "Conflict label is retained as descriptive because strict robustness evidence is weak."

    return "DESCRIPTIVE_ONLY", "LOW", "Phase 3 evidence is neutral or descriptive; it is not eligible for future score-adjustment research."


def build_special_qualification(matrix_payload: dict[str, Any], inputs: dict[str, Any], style: str) -> dict[str, Any]:
    rows = [row for row in matrix_payload["rows"] if row["style_profile"] == style]
    audit = inputs["high_beta"] if style == "HIGH_BETA_THEME" else inputs["commodity"]
    by_regime = {row["stable_regime"]: row for row in rows}
    support_qualified = [
        r for r in rows
        if r["final_research_qualification"] in POSITIVE_QUALIFICATIONS
    ]
    qualified_support = [
        r for r in rows
        if r["final_research_qualification"] == "QUALIFIED_SUPPORT"
    ]
    unstable = [r for r in rows if r["final_research_qualification"] == "UNSTABLE"]
    flags = sorted(set(audit.get("flags", [])))
    if style == "HIGH_BETA_THEME":
        if not support_qualified:
            interpretation = "DESCRIPTIVE_ONLY"
        elif len(qualified_support) == 0 and {"OFFENSIVE", "DEFENSIVE"}.issubset({r["stable_regime"] for r in support_qualified}):
            interpretation = "MULTI_REGIME_SUPPORT_NOT_QUALIFIED"
        elif any(r["stable_regime"] == "OFFENSIVE" for r in qualified_support):
            interpretation = "OFFENSIVE_ONLY_QUALIFIED"
        elif any(r["stable_regime"] == "DEFENSIVE" for r in support_qualified):
            interpretation = "DEFENSIVE_SUPPORT_DOWNGRADED"
        elif unstable:
            interpretation = "MIXED_CELL_QUALIFICATION"
        else:
            interpretation = "MIXED_CELL_QUALIFICATION"
        field_name = "high_beta_theme_final_interpretation"
    else:
        off = by_regime.get("OFFENSIVE", {}).get("final_research_qualification")
        defensive = by_regime.get("DEFENSIVE", {}).get("final_research_qualification")
        if off == "QUALIFIED_SUPPORT" and defensive == "QUALIFIED_SUPPORT":
            interpretation = "QUALIFIED_MULTI_REGIME_SUPPORT"
        elif off in POSITIVE_QUALIFICATIONS and defensive in POSITIVE_QUALIFICATIONS:
            interpretation = "CONDITIONAL_MULTI_REGIME_SUPPORT"
        elif off in POSITIVE_QUALIFICATIONS:
            interpretation = "OFFENSIVE_ONLY_SUPPORT"
        elif defensive in POSITIVE_QUALIFICATIONS:
            interpretation = "DEFENSIVE_ONLY_SUPPORT"
        elif unstable:
            interpretation = "UNSTABLE"
        else:
            interpretation = "DESCRIPTIVE_ONLY"
        field_name = "commodity_cyclical_final_interpretation"
    payload = {
        "generated_at": _now(),
        "style_profile": style,
        "flags": flags,
        field_name: interpretation,
        "cells": rows,
        "qualified_support_exists": bool(qualified_support),
        "conditional_support_exists": any(r["final_research_qualification"] == "CONDITIONAL_SUPPORT" for r in rows),
        "descriptive_only_exists": any(r["final_research_qualification"] == "DESCRIPTIVE_ONLY" for r in rows),
        "unstable_cell_exists": bool(unstable),
        "future_positive_filter_research_eligibility": any(r["eligible_for_future_positive_filter_research"] for r in rows),
        "future_negative_filter_research_eligibility": any(r["eligible_for_future_negative_filter_research"] for r in rows),
        "source_audit_preliminary_explanation": audit.get("preliminary_explanation"),
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }
    return payload


def build_incremental_final_decision(inputs: dict[str, Any]) -> dict[str, Any]:
    inc = inputs["incremental"]
    core = inputs["core_summary"]
    support_keys = ["pooled_support", "time_split_support", "etf_level_support", "segment_level_support", "horizon_support"]
    supports = {key: bool(inc.get(key)) for key in support_keys}
    support_count = sum(1 for value in supports.values() if value)
    etf_overall = core.get("etf_level_robustness_classification")
    core_reversal_count = int(_float(inc.get("core_reversal_count"), 0))
    if support_count == 5 and etf_overall != "CONFLICTING" and core_reversal_count == 0:
        robustness = "ROBUST"
        answer = "YES_ROBUSTLY"
    elif support_count >= 4 and core_reversal_count <= 1:
        robustness = "PARTIALLY_ROBUST"
        answer = "YES_WITH_ROBUSTNESS_CAVEAT"
    elif support_count >= 2:
        robustness = "FRAGILE"
        answer = "YES_WITH_ROBUSTNESS_CAVEAT"
    elif support_count == 0:
        robustness = "NOT_SUPPORTED"
        answer = "NO"
    else:
        robustness = "INSUFFICIENT"
        answer = "INSUFFICIENT"
    caveats = []
    if etf_overall == "CONFLICTING":
        caveats.append("ETF-level overall robustness is CONFLICTING; pooled support cannot be called fully robust.")
    if core_reversal_count:
        caveats.append(f"{core_reversal_count} core aggregation comparison has direction reversal.")
    if core.get("major_robustness_warning_found"):
        caveats.append("Major robustness warning remains active.")
    return {
        "generated_at": _now(),
        **supports,
        "etf_level_overall_classification": etf_overall,
        "style_fit_incremental_signal_value_robustness": robustness,
        "incremental_signal_value_final_answer": answer,
        "key_supporting_evidence": [
            "Pooled ETF-day, time split, ETF-level, segment-level, and horizon checks are supportive in majority/core views."
            if support_count == 5 else
            f"{support_count} of 5 robustness views support STRONG+SUPPORTED > STRONG+CONFLICT."
        ],
        "key_robustness_caveats": caveats,
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def build_future_preview_scope(matrix_payload: dict[str, Any], incremental: dict[str, Any]) -> dict[str, Any]:
    rows = matrix_payload["rows"]
    allowed_positive = sorted({r["final_research_qualification"] for r in rows if r["final_research_qualification"] in POSITIVE_QUALIFICATIONS})
    allowed_negative = sorted({r["final_research_qualification"] for r in rows if r["final_research_qualification"] in NEGATIVE_QUALIFICATIONS})
    return {
        "generated_at": _now(),
        "preview_research_allowed": incremental["incremental_signal_value_final_answer"] in {"YES_WITH_ROBUSTNESS_CAVEAT", "YES_ROBUSTLY"},
        "allowed_positive_qualifications": allowed_positive,
        "allowed_negative_qualifications": allowed_negative,
        "disallowed_qualifications": sorted(DISALLOWED_QUALIFICATIONS),
        "score_bonus_allowed": False,
        "score_penalty_allowed": False,
        "raw_ranking_must_remain_unchanged": True,
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
        "scope_note": "Phase 3.5B only defines evidence categories eligible for future preview research; it does not authorize score changes.",
    }


def build_qualification_summary(matrix_payload: dict[str, Any]) -> dict[str, Any]:
    rows = matrix_payload["rows"]
    counts = {q: sum(1 for r in rows if r["final_research_qualification"] == q) for q in QUALIFICATIONS}
    eligible_positive = [r for r in rows if r["eligible_for_future_positive_filter_research"]]
    eligible_negative = [r for r in rows if r["eligible_for_future_negative_filter_research"]]
    return {
        "generated_at": _now(),
        "total_cells": len(rows),
        "qualified_support_count": counts["QUALIFIED_SUPPORT"],
        "conditional_support_count": counts["CONDITIONAL_SUPPORT"],
        "descriptive_only_count": counts["DESCRIPTIVE_ONLY"],
        "unstable_count": counts["UNSTABLE"],
        "qualified_conflict_count": counts["QUALIFIED_CONFLICT"],
        "conditional_conflict_count": counts["CONDITIONAL_CONFLICT"],
        "insufficient_count": counts["INSUFFICIENT"],
        "positive_filter_research_eligible_count": len(eligible_positive),
        "negative_filter_research_eligible_count": len(eligible_negative),
        "top_qualified_support_cells": top_cells(rows, "QUALIFIED_SUPPORT"),
        "top_conditional_support_cells": top_cells(rows, "CONDITIONAL_SUPPORT"),
        "top_qualified_conflict_cells": top_cells(rows, "QUALIFIED_CONFLICT"),
        "top_unstable_cells": top_cells(rows, "UNSTABLE"),
        "research_only": True,
        "shadow_only": True,
        "execution_allowed": False,
    }


def build_phase3_5b_decision(
    integrity: dict[str, Any],
    matrix_payload: dict[str, Any],
    high_beta: dict[str, Any],
    commodity: dict[str, Any],
    incremental: dict[str, Any],
    preview_scope: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    style_fit_has_historical_support = (summary["qualified_support_count"] + summary["conditional_support_count"] + summary["qualified_conflict_count"] + summary["conditional_conflict_count"]) > 0
    style_fit_has_incremental_signal_value = incremental["incremental_signal_value_final_answer"] in {"YES_WITH_ROBUSTNESS_CAVEAT", "YES_ROBUSTLY"}
    ready_shadow = bool(not integrity["future_leakage_found"] and not integrity["blocking_evidence_conflict_found"] and style_fit_has_historical_support)
    ready_adjusted = bool(
        style_fit_has_incremental_signal_value
        and (summary["qualified_support_count"] + summary["qualified_conflict_count"] > 0)
        and preview_scope["preview_research_allowed"]
        and preview_scope["disallowed_qualifications"]
        and preview_scope["raw_ranking_must_remain_unchanged"]
        and not preview_scope["score_bonus_allowed"]
        and not preview_scope["score_penalty_allowed"]
    )
    ready_35c = bool(
        not integrity["blocking_evidence_conflict_found"]
        and matrix_payload.get("rows")
        and incremental
        and preview_scope
        and summary
    )
    historical_action = "KEEP" if style_fit_has_historical_support else "REVOKE"
    incremental_action = "DOWNGRADE" if incremental["style_fit_incremental_signal_value_robustness"] == "PARTIALLY_ROBUST" else ("KEEP" if style_fit_has_incremental_signal_value else "REVOKE")
    return {
        "generated_at": _now(),
        "phase": "Regime Layer Phase 3.5B",
        "evidence_integrity_passed": not integrity["blocking_evidence_conflict_found"],
        "style_fit_has_historical_support": style_fit_has_historical_support,
        "style_fit_has_incremental_signal_value": style_fit_has_incremental_signal_value,
        "style_fit_incremental_signal_value_robustness": incremental["style_fit_incremental_signal_value_robustness"],
        "incremental_signal_value_final_answer": incremental["incremental_signal_value_final_answer"],
        "high_beta_theme_final_interpretation": high_beta["high_beta_theme_final_interpretation"],
        "commodity_cyclical_final_interpretation": commodity["commodity_cyclical_final_interpretation"],
        "qualified_support_count": summary["qualified_support_count"],
        "conditional_support_count": summary["conditional_support_count"],
        "descriptive_only_count": summary["descriptive_only_count"],
        "unstable_count": summary["unstable_count"],
        "qualified_conflict_count": summary["qualified_conflict_count"],
        "conditional_conflict_count": summary["conditional_conflict_count"],
        "insufficient_count": summary["insufficient_count"],
        "ready_for_fit_shadow_observation": ready_shadow,
        "ready_for_adjusted_preview_research": ready_adjusted,
        "future_preview_research_scope_defined": bool(preview_scope),
        "phase3_decision_action": "QUALIFY_PRIOR_DECISION",
        "phase3_historical_support_decision_action": historical_action,
        "phase3_incremental_value_decision_action": incremental_action,
        "supersedes_decision": "reports/style_regime_fit_phase_decision.json",
        "qualifies_prior_decision": "reports/style_regime_fit_phase_decision.json",
        "major_robustness_warning_active": True,
        "blocking_methodology_issue_found": False,
        "ready_for_phase_3_5c": ready_35c,
        "ready_for_preview": False,
        "ready_for_execution": False,
        "execution_allowed": False,
        "research_only": True,
        "shadow_only": True,
    }


def update_project_context(decision: dict[str, Any], summary: dict[str, Any], high_beta: dict[str, Any], commodity: dict[str, Any], incremental: dict[str, Any], preview_scope: dict[str, Any]) -> None:
    status_path = PROJECT_ROOT / "docs" / "current_phase_status.json"
    state_path = PROJECT_ROOT / "docs" / "current_project_state.md"
    status = _read_json(status_path)
    now = _now() + " CST"
    status.update({
        "context_updated_at": now,
        "context_updated_by": "Codex",
        "context_update_reason": "Regime Layer Phase 3.5B robustness decision and evidence qualification completed; Phase 3.5C research integration is next",
        "main_phase": "Regime Layer Phase 3.5 - Style Fit Robustness Audit",
        "main_phase_id": "regime_layer_phase_3_5",
        "phase_status": "IN_PROGRESS",
        "current_batch": "Phase 3.5C",
        "current_batch_id": "phase_3_5c",
        "current_batch_status": "PENDING",
        "completed_batches": ["Phase 3.5A", "Phase 3.5B"],
        "pending_batches": ["Phase 3.5C", "Phase 3.5D"],
        "last_completed_batch": "Phase 3.5B",
        "resume_from": "Phase 3.5C",
        "required_batches": ["Phase 3.5A", "Phase 3.5B", "Phase 3.5C", "Phase 3.5D"],
        "final_closeout_batch": "Phase 3.5D",
        "next_research_phase": "Regime Layer Phase 3.5C - Research Output Integration & Shadow Tracking Design",
        "current_phase_report": "reports/style_fit_evidence_qualification_summary.md",
        "current_phase_decision": "reports/regime_layer_phase3_5b_decision.json",
        "formal_model_changed": False,
        "buy_ranking_changed": False,
        "market_regime_changed": False,
        "ready_for_fit_shadow_observation": decision["ready_for_fit_shadow_observation"],
        "ready_for_adjusted_preview_research": decision["ready_for_adjusted_preview_research"],
        "ready_for_preview": False,
        "ready_for_execution": False,
        "research_only": True,
        "execution_allowed": False,
    })
    sources = dict(status.get("status_sources", {}))
    sources.setdefault("style_fit_decision", [])
    if "reports/regime_layer_phase3_5b_decision.json" not in sources["style_fit_decision"]:
        sources["style_fit_decision"].append("reports/regime_layer_phase3_5b_decision.json")
    sources["style_fit_evidence_qualification"] = [
        "reports/style_regime_evidence_qualification_matrix.json",
        "reports/style_fit_evidence_qualification_summary.json",
        "reports/style_fit_future_preview_research_scope.json",
    ]
    status["status_sources"] = sources
    history = list(status.get("phase_transition_history", []))
    history.append({
        "from_batch": "Phase 3.5B",
        "to_batch": "Phase 3.5C",
        "reason": "Phase 3.5B robustness decision and evidence qualification completed",
        "recorded_at": now,
        "transition_type": "BATCH_COMPLETION",
    })
    status["phase_transition_history"] = history
    _write_json(status_path, status)
    state_path.write_text(render_current_project_state(decision, summary, high_beta, commodity, incremental, preview_scope, now), encoding="utf-8")


def render_current_project_state(decision: dict[str, Any], summary: dict[str, Any], high_beta: dict[str, Any], commodity: dict[str, Any], incremental: dict[str, Any], preview_scope: dict[str, Any], now: str) -> str:
    return f"""# Current Project State

## 1. Snapshot Metadata

- Project: A-Share Swing System
- Repository root: `/Users/dayin/Code/a-share-swing-system`
- State snapshot date: 2026-07-08
- State snapshot source: Regime Layer Phase 3.5B evidence qualification and decision files.

This file is a human and Codex shared current project fact snapshot. It is not a history log, README replacement, or phase report.

## 2. Current Project Stage

- Engineering Maturity: approximately stable / operational
- Strategy Maturity: research validation stage
- Current Main Research Track: Regime & Risk Allocation

Current stage:

```text
工程系统基本成型
正式模型稳定运行观察
Shadow / Research 正在验证自适应 Regime Layer
Regime Layer Phase 3.5 - Style Fit Robustness Audit IN_PROGRESS
```

## 3. Formal Model State

- Formal model unchanged.
- `mid_trend = 70%`
- `short_swing = 30%`
- Uses BUY / WATCH / SELL framework.
- Paper simulation active.
- ETF-first.
- Total stock exposure `<= 10%`.

Regime Layer has not changed formal execution.

Style Fit has not changed BUY ranking or raw ranking scores.

## 4. Completed Regime/Risk Phases

| Phase | Name | Status |
| --- | --- | --- |
| Phase 1 | ETF Realized Risk Profile | COMPLETE |
| Phase 1.5 | Style + Structural Risk Profile | COMPLETE |
| Phase 2 | Market Regime Audit & Historical Replay | COMPLETE |
| Phase 2.5 | Regime Stabilization Research | COMPLETE |
| Phase 3 | Style-Regime Fit Research | COMPLETE |
| Phase 3.5A | Style Fit Robustness Core Audit | COMPLETE |
| Phase 3.5B | Robustness Decision & Evidence Qualification | COMPLETE |

## 5. Current Research Architecture

```text
Market Regime
↓
ASYMMETRIC_CONFIRM shadow stabilization
↓
Style-Regime Fit
↓
Evidence Qualification
↓
Future research-only preview scope
↓
mid_trend + short_swing
↓
BUY Ranking
```

Style Fit evidence is now cell-level qualified. Raw Phase 3 `SUPPORTED` / `CONFLICT` labels must not be treated as equal-confidence evidence.

## 6. Selected Shadow Regime

- selected candidate: `ASYMMETRIC_CONFIRM`
- shadow-only: true
- research-only: true
- not formal execution

Latest known snapshot:

```text
latest_data_date = 2026-07-07
latest_known_regime_date = 2026-07-06
raw regime as of 2026-07-06 = NEUTRAL
selected shadow regime as of 2026-07-06 = NEUTRAL
regime_snapshot_stale = true
```

This snapshot is stale relative to 2026-07-07 data. Do not describe it as the live current market regime.

## 7. Phase 3.5B Current Conclusions

From `reports/regime_layer_phase3_5b_decision.json`:

```text
style_fit_has_historical_support = {str(decision['style_fit_has_historical_support']).lower()}
style_fit_has_incremental_signal_value = {str(decision['style_fit_has_incremental_signal_value']).lower()}
style_fit_incremental_signal_value_robustness = {decision['style_fit_incremental_signal_value_robustness']}
incremental_signal_value_final_answer = {decision['incremental_signal_value_final_answer']}
ready_for_fit_shadow_observation = {str(decision['ready_for_fit_shadow_observation']).lower()}
ready_for_adjusted_preview_research = {str(decision['ready_for_adjusted_preview_research']).lower()}
ready_for_preview = false
ready_for_execution = false
execution_allowed = false
```

Incremental signal value remains true, but robustness is qualified: `{decision['style_fit_incremental_signal_value_robustness']}` due to ETF-level pooling reversal warnings.

Qualification counts:

```text
QUALIFIED_SUPPORT = {summary['qualified_support_count']}
CONDITIONAL_SUPPORT = {summary['conditional_support_count']}
DESCRIPTIVE_ONLY = {summary['descriptive_only_count']}
UNSTABLE = {summary['unstable_count']}
QUALIFIED_CONFLICT = {summary['qualified_conflict_count']}
CONDITIONAL_CONFLICT = {summary['conditional_conflict_count']}
INSUFFICIENT = {summary['insufficient_count']}
```

HIGH_BETA_THEME final interpretation:

```text
{high_beta['high_beta_theme_final_interpretation']}
flags = {high_beta['flags']}
```

COMMODITY_CYCLICAL final interpretation:

```text
{commodity['commodity_cyclical_final_interpretation']}
flags = {commodity['flags']}
```

Future preview research scope is defined, but no adjusted preview is created. Score bonus and score penalty are not authorized in Phase 3.5B.

## 8. Open Research Risks

Current unresolved issues:

- ETF-level pooling reversal remains an active major robustness warning.
- `HIGH_BETA_THEME` still carries sample dependence risk.
- Cell-level evidence heterogeneity means future research may only use qualified evidence cells.
- DESCRIPTIVE_ONLY / UNSTABLE / INSUFFICIENT cells are excluded from future preview filter research.

## 9. Current Main Bottlenecks

- Phase 3.5C must integrate research outputs and design shadow tracking scope without creating adjusted preview.
- Real forward shadow samples are limited.
- Formal exit logic remains a major strategy bottleneck.
- Formal model is still research-unproven statistically.

## 10. Project Context Persistence

```text
Project Context Persistence Phase = COMPLETE
```

New threads must still execute repository bootstrap before substantive edits.

## 11. Immediate Next Work

```text
Regime Layer Phase 3.5C
Research Output Integration & Shadow Tracking Design
status = PENDING
```

Do not create adjusted preview. Current `ready_for_preview=false`.

Context updated at: {now}
"""


def build_phase3_matrix_lookup(df: pd.DataFrame) -> dict[tuple[str, str, int], dict[str, Any]]:
    lookup = {}
    if df.empty:
        return lookup
    for _, row in df.iterrows():
        lookup[(str(row["regime"]), str(row["style_profile"]), int(row["forward_horizon"]))] = row.to_dict()
    return lookup


def build_robustness_lookup(rows: list[dict[str, Any]], kind: str) -> dict[tuple[str, str, str, int], dict[str, Any]]:
    out = {}
    for row in rows:
        horizon = int(str(row.get("horizon", "0d")).replace("d", ""))
        out[(str(row["stable_regime"]), str(row["style_profile"]), str(row["signal_fit_group"]), horizon)] = row
    return out


def rows_by_regime(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("stable_regime")): row for row in rows}


def signal_group_for_evidence(evidence: str) -> str:
    if evidence in SUPPORT_EVIDENCE:
        return "STRONG_SUPPORTED"
    if evidence in CONFLICT_EVIDENCE:
        return "STRONG_CONFLICT"
    return "STRONG_SUPPORTED"


def phase3_horizon_direction(evidence: Any) -> str:
    value = str(evidence or "INSUFFICIENT")
    if value in SUPPORT_EVIDENCE:
        return "SUPPORTIVE"
    if value in CONFLICT_EVIDENCE:
        return "CONFLICTING"
    if value == "INSUFFICIENT":
        return "INSUFFICIENT"
    return "NEUTRAL"


def time_direction(rows: list[dict[str, Any]]) -> str:
    core = [
        row for row in rows
        if row.get("signal_fit_group") == "STRONG_SUPPORTED" and row.get("horizon") == "10d"
    ]
    directions = [row.get("direction") for row in core]
    if directions and all(direction == "SUPPORTED_BEATS_CONFLICT" for direction in directions):
        return "SUPPORTED_BEATS_CONFLICT"
    if any(direction == "CONFLICT_BEATS_SUPPORTED" for direction in directions):
        return "CONFLICT_BEATS_SUPPORTED"
    if directions:
        return "MIXED_OR_NEUTRAL"
    return "INSUFFICIENT"


def aggregate_metric_direction(rows: list[dict[str, Any]], metric: str) -> str:
    values = [_maybe_float(row.get(metric)) for row in rows if row]
    values = [value for value in values if value is not None]
    if not values:
        return "INSUFFICIENT"
    positive = sum(1 for value in values if value > 0)
    negative = sum(1 for value in values if value < 0)
    if positive == len(values):
        return "POSITIVE"
    if negative == len(values):
        return "NEGATIVE"
    if positive > negative:
        return "MIXED_POSITIVE"
    if negative > positive:
        return "MIXED_NEGATIVE"
    return "MIXED"


def special_segment_direction(row: dict[str, Any]) -> str:
    if not row:
        return "INSUFFICIENT"
    values = [_maybe_float(row.get(f"{h}d_segment_level_median")) for h in CORE_HORIZONS]
    values = [value for value in values if value is not None]
    if not values:
        return "INSUFFICIENT"
    positive = sum(1 for value in values if value > 0)
    negative = sum(1 for value in values if value < 0)
    if positive == len(values):
        return "POSITIVE"
    if negative == len(values):
        return "NEGATIVE"
    if positive > negative:
        return "MIXED_POSITIVE"
    if negative > positive:
        return "MIXED_NEGATIVE"
    return "MIXED"


def max_flag(flags: list[Any]) -> str:
    clean = [str(flag) for flag in flags if flag not in (None, "", float("nan")) and str(flag) != "nan"]
    if not clean:
        return "INSUFFICIENT"
    return max(clean, key=lambda flag: FLAG_RANK.get(flag, 0))


def qualification_score(confidence: str, excess: float | None, sample: float | None, qualification: str) -> float:
    direction = 1.0
    if qualification in NEGATIVE_QUALIFICATIONS:
        direction = -1.0
    return round(CONFIDENCE_RANK.get(confidence, 0) * 1000 + direction * (_float(excess) * 1000) + min(_float(sample), 1000) / 1000, 6)


def top_cells(rows: list[dict[str, Any]], qualification: str, limit: int = 8) -> list[dict[str, Any]]:
    sub = [r for r in rows if r["final_research_qualification"] == qualification]
    sub = sorted(sub, key=lambda r: (CONFIDENCE_RANK.get(r["evidence_confidence"], 0), _float(r.get("phase3_benchmark_excess_median")), _float(r.get("phase3_sample_count"))), reverse=True)
    keys = ["style_profile", "stable_regime", "phase3_evidence_level", "phase3_benchmark_excess_median", "pooling_bias_flag", "segment_concentration_flag", "evidence_confidence", "qualification_reason"]
    return [{key: row.get(key) for key in keys} for row in sub[:limit]]


def qualification_rules_payload() -> dict[str, Any]:
    return {
        "final_research_qualification_values": sorted(QUALIFICATIONS),
        "evidence_confidence_values": sorted(CONFIDENCE_VALUES),
        "qualified_support": "Phase 3 positive evidence plus supportive ETF-level/core horizon/time evidence, no direction reversal, no major sample or concentration warning.",
        "conditional_support": "Positive direction remains, but robustness is partial or confidence is capped by concentration, limited sample, weak excess, or sample dependence.",
        "descriptive_only": "Label remains useful only as description, not future score-adjustment research input.",
        "unstable": "Direction reversal or core instability prevents use in future adjusted preview research.",
        "qualified_conflict": "Phase 3 conflict evidence plus negative ETF-level/core horizon evidence without major caveats.",
        "conditional_conflict": "Weak negative research evidence only.",
        "insufficient": "Effective samples or Phase 3 cell evidence are insufficient.",
    }


def write_matrix_outputs(matrix_payload: dict[str, Any]) -> None:
    df = pd.DataFrame(matrix_payload["rows"]).drop(columns=["qualification_score"], errors="ignore")
    df.to_csv(QUAL_MATRIX_CSV, index=False)
    _write_json(QUAL_MATRIX_JSON, matrix_payload)
    QUAL_MATRIX_MD.write_text(render_matrix(matrix_payload), encoding="utf-8")


def render_integrity_audit(audit: dict[str, Any]) -> str:
    return "\n".join([
        "# Style Fit Robustness Evidence Integrity Audit",
        "",
        f"- source_audit_valid: {audit['source_audit_valid']}",
        f"- future_leakage_found: {audit['future_leakage_found']}",
        f"- benchmark_labels_evaluation_only: {audit['benchmark_labels_evaluation_only']}",
        f"- phase3_5a_decision_consistent: {audit['phase3_5a_decision_consistent']}",
        f"- ready_for_phase_3_5b: {audit['ready_for_phase_3_5b']}",
        f"- blocking_evidence_conflict_found: {audit['blocking_evidence_conflict_found']}",
    ])


def render_matrix(matrix_payload: dict[str, Any]) -> str:
    return "\n".join([
        "# Style-Regime Evidence Qualification Matrix",
        "",
        "Each row is one style_profile x stable_regime cell. This is research-only evidence qualification.",
        "",
        markdown_table(matrix_payload["rows"], [
            "style_profile",
            "stable_regime",
            "phase3_evidence_level",
            "pooling_bias_flag",
            "segment_concentration_flag",
            "horizon_5d_direction",
            "horizon_10d_direction",
            "horizon_20d_direction",
            "special_style_flags",
            "final_research_qualification",
            "evidence_confidence",
            "eligible_for_future_positive_filter_research",
            "eligible_for_future_negative_filter_research",
        ], limit=80),
    ])


def render_special_qualification(payload: dict[str, Any]) -> str:
    interp_key = "high_beta_theme_final_interpretation" if payload["style_profile"] == "HIGH_BETA_THEME" else "commodity_cyclical_final_interpretation"
    return "\n".join([
        f"# {payload['style_profile']} Evidence Qualification",
        "",
        f"- final_interpretation: {payload[interp_key]}",
        f"- flags: {payload['flags']}",
        f"- qualified_support_exists: {payload['qualified_support_exists']}",
        f"- future_positive_filter_research_eligibility: {payload['future_positive_filter_research_eligibility']}",
        f"- future_negative_filter_research_eligibility: {payload['future_negative_filter_research_eligibility']}",
        "",
        markdown_table(payload["cells"], [
            "stable_regime",
            "phase3_evidence_level",
            "etf_level_direction",
            "segment_direction",
            "horizon_5d_direction",
            "horizon_10d_direction",
            "horizon_20d_direction",
            "final_research_qualification",
            "evidence_confidence",
        ]),
    ])


def render_incremental_final_decision(payload: dict[str, Any]) -> str:
    return "\n".join([
        "# Style Fit Incremental Signal Final Decision",
        "",
        f"- pooled_support: {payload['pooled_support']}",
        f"- time_split_support: {payload['time_split_support']}",
        f"- etf_level_support: {payload['etf_level_support']}",
        f"- segment_level_support: {payload['segment_level_support']}",
        f"- horizon_support: {payload['horizon_support']}",
        f"- etf_level_overall_classification: {payload['etf_level_overall_classification']}",
        f"- style_fit_incremental_signal_value_robustness: {payload['style_fit_incremental_signal_value_robustness']}",
        f"- incremental_signal_value_final_answer: {payload['incremental_signal_value_final_answer']}",
        "",
        "## Caveats",
        "\n".join(f"- {item}" for item in payload["key_robustness_caveats"]) or "- None",
    ])


def render_preview_scope(payload: dict[str, Any]) -> str:
    return "\n".join([
        "# Style Fit Future Preview Research Scope",
        "",
        f"- preview_research_allowed: {payload['preview_research_allowed']}",
        f"- allowed_positive_qualifications: {payload['allowed_positive_qualifications']}",
        f"- allowed_negative_qualifications: {payload['allowed_negative_qualifications']}",
        f"- disallowed_qualifications: {payload['disallowed_qualifications']}",
        f"- score_bonus_allowed: {payload['score_bonus_allowed']}",
        f"- score_penalty_allowed: {payload['score_penalty_allowed']}",
        f"- raw_ranking_must_remain_unchanged: {payload['raw_ranking_must_remain_unchanged']}",
        f"- execution_allowed: {payload['execution_allowed']}",
    ])


def render_qualification_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Style Fit Evidence Qualification Summary",
        "",
        f"- total_cells: {summary['total_cells']}",
        f"- qualified_support_count: {summary['qualified_support_count']}",
        f"- conditional_support_count: {summary['conditional_support_count']}",
        f"- descriptive_only_count: {summary['descriptive_only_count']}",
        f"- unstable_count: {summary['unstable_count']}",
        f"- qualified_conflict_count: {summary['qualified_conflict_count']}",
        f"- conditional_conflict_count: {summary['conditional_conflict_count']}",
        f"- insufficient_count: {summary['insufficient_count']}",
        f"- positive_filter_research_eligible_count: {summary['positive_filter_research_eligible_count']}",
        f"- negative_filter_research_eligible_count: {summary['negative_filter_research_eligible_count']}",
        "",
        "## Top Qualified Support Cells",
        markdown_table(summary["top_qualified_support_cells"], ["style_profile", "stable_regime", "phase3_evidence_level", "phase3_benchmark_excess_median", "evidence_confidence"]),
        "",
        "## Top Conditional Support Cells",
        markdown_table(summary["top_conditional_support_cells"], ["style_profile", "stable_regime", "phase3_evidence_level", "phase3_benchmark_excess_median", "evidence_confidence"]),
        "",
        "## Top Qualified Conflict Cells",
        markdown_table(summary["top_qualified_conflict_cells"], ["style_profile", "stable_regime", "phase3_evidence_level", "phase3_benchmark_excess_median", "evidence_confidence"]),
        "",
        "## Top Unstable Cells",
        markdown_table(summary["top_unstable_cells"], ["style_profile", "stable_regime", "phase3_evidence_level", "pooling_bias_flag", "evidence_confidence"]),
    ]
    return "\n".join(lines)


def render_phase3_5b_decision(decision: dict[str, Any]) -> str:
    return "\n".join([
        "# Regime Layer Phase 3.5B Decision",
        "",
        f"- evidence_integrity_passed: {decision['evidence_integrity_passed']}",
        f"- style_fit_has_historical_support: {decision['style_fit_has_historical_support']}",
        f"- style_fit_has_incremental_signal_value: {decision['style_fit_has_incremental_signal_value']}",
        f"- style_fit_incremental_signal_value_robustness: {decision['style_fit_incremental_signal_value_robustness']}",
        f"- incremental_signal_value_final_answer: {decision['incremental_signal_value_final_answer']}",
        f"- high_beta_theme_final_interpretation: {decision['high_beta_theme_final_interpretation']}",
        f"- commodity_cyclical_final_interpretation: {decision['commodity_cyclical_final_interpretation']}",
        f"- ready_for_fit_shadow_observation: {decision['ready_for_fit_shadow_observation']}",
        f"- ready_for_adjusted_preview_research: {decision['ready_for_adjusted_preview_research']}",
        f"- ready_for_phase_3_5c: {decision['ready_for_phase_3_5c']}",
        f"- ready_for_preview: {decision['ready_for_preview']}",
        f"- ready_for_execution: {decision['ready_for_execution']}",
        f"- execution_allowed: {decision['execution_allowed']}",
        "",
        "Phase 3.5B qualifies prior Phase 3 evidence. It does not authorize preview, ranking changes, or execution.",
    ])


def markdown_table(rows: list[dict[str, Any]], columns: list[str], limit: int | None = None) -> str:
    data = rows[:limit] if limit else rows
    if not data:
        return "_No rows._"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in data:
        lines.append("| " + " | ".join(format_cell(row.get(col)) for col in columns) + " |")
    return "\n".join(lines)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(_sanitize(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    if isinstance(value, tuple):
        return [_sanitize(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return round(value, 6)
    return value


def _now() -> str:
    return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")


def _maybe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def _float(value: Any, fallback: float = 0.0) -> float:
    out = _maybe_float(value)
    return fallback if out is None else out


def _round(value: Any) -> float | None:
    out = _maybe_float(value)
    return round(out, 6) if out is not None else None


def _int_or_none(value: Any) -> int | None:
    out = _maybe_float(value)
    return int(out) if out is not None else None


def format_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value).replace("|", "/")


if __name__ == "__main__":
    main()
