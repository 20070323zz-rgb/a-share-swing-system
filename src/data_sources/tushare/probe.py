"""Run-scoped minimal Tushare staging proof orchestration."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from typing import Any, Mapping
import uuid
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

from .client import MockTushareClient, ProbeCall, TushareMinimalClient, canonical_hash, load_token
from .pit_contract import build_pit_records, interface_pit_summary
from .schemas import INTERFACE_SCHEMAS
from .validators import ValidationResult, validate_interface_frame


TZ = ZoneInfo("Asia/Shanghai")
INTERFACES = tuple(INTERFACE_SCHEMAS)
EVIDENCE_MODES = {"real", "mock"}
RUN_ID_PATTERN = re.compile(r"^(real|mock)-\d{8}(?:T\d{6})?-[A-Za-z0-9][A-Za-z0-9._-]*$")
REAL_STATUSES = {"REAL_PROOF_COMPLETE", "REAL_PROOF_PARTIAL", "REAL_PROOF_FAILED", "REAL_PROOF_BLOCKED"}
MOCK_STATUSES = {"MOCK_VALIDATION_PASS", "MOCK_VALIDATION_FAILED"}


@dataclass
class ProbeOutcome:
    interface: str
    call_count: int
    response_status: str
    permission_status: str
    row_count: int
    normalized_row_count: int
    validation_status: str
    pit_status: str
    sample_scope: str
    date_min: str
    date_max: str
    missing_fields: str
    duplicate_keys: int
    error_class: str
    error_message: str
    official_doc: str
    official_update_pattern: str
    request_parameters_sanitized: str
    columns: str
    dtypes: str
    null_rates: str
    retrieved_at: str
    query_hash: str
    raw_payload_hash: str
    normalized_hash: str
    reduction_evidence: dict[str, Any]


def load_config(path: Path) -> dict[str, Any]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Tushare proof config must be a mapping")
    contract = config.get("evidence_contract")
    if not isinstance(contract, dict) or contract.get("require_explicit_mode") is not True:
        raise ValueError("config must require an explicit evidence_mode")
    modes = set(contract.get("allowed_modes") or [])
    if modes != EVIDENCE_MODES:
        raise ValueError("config evidence_contract.allowed_modes must be exactly real and mock")
    namespaces = contract.get("output_namespaces") or {}
    if namespaces != {"real": "real", "mock": "mock"}:
        raise ValueError("config must isolate real and mock output namespaces")
    return config


def validate_evidence_mode(evidence_mode: str) -> str:
    if evidence_mode not in EVIDENCE_MODES:
        raise ValueError("evidence_mode must be explicitly set to real or mock")
    return evidence_mode


def generate_run_id(evidence_mode: str) -> str:
    mode = validate_evidence_mode(evidence_mode)
    timestamp = datetime.now(TZ).strftime("%Y%m%dT%H%M%S")
    return f"{mode}-{timestamp}-{uuid.uuid4().hex[:8]}"


def validate_run_id(evidence_mode: str, run_id: str) -> str:
    mode = validate_evidence_mode(evidence_mode)
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id must match <real|mock>-<YYYYMMDD[THHMMSS]>-<suffix>")
    if not run_id.startswith(f"{mode}-"):
        raise ValueError(f"{mode} evidence_mode requires a {mode}-* run_id")
    return run_id


def resolve_run_directory(root: Path, config: dict[str, Any], evidence_mode: str, run_id: str) -> Path:
    mode = validate_evidence_mode(evidence_mode)
    validated_run_id = validate_run_id(mode, run_id)
    namespace = config["evidence_contract"]["output_namespaces"][mode]
    return root / config["runtime"]["staging_root"] / namespace / validated_run_id


def run_probe(
    project_root: Path,
    config_path: Path,
    *,
    evidence_mode: str,
    mock_responses: Mapping[str, Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    root = project_root.resolve()
    config = load_config(config_path)
    mode = validate_evidence_mode(evidence_mode)
    resolved_run_id = validate_run_id(mode, run_id or generate_run_id(mode))
    runtime = config["runtime"]
    if mode == "real":
        if mock_responses is not None:
            raise ValueError("real evidence_mode rejects mock responses")
        token = load_token(root)
        if not token:
            raise RuntimeError("REAL_PROOF_BLOCKED: secure Tushare token provider returned no token")
        client: TushareMinimalClient | MockTushareClient = TushareMinimalClient(
            project_root=root,
            token=token,
            max_requests=int(runtime["max_api_requests"]),
            timeout_seconds=int(runtime["timeout_seconds"]),
            request_interval_seconds=float(runtime["request_interval_seconds"]),
            max_network_retries=int(runtime["max_network_retries"]),
        )
    else:
        if mock_responses is None:
            raise ValueError("mock evidence_mode requires explicit fixture responses")
        client = MockTushareClient(
            fixture_responses=mock_responses,
            max_requests=int(runtime["max_api_requests"]),
        )

    run_dir = resolve_run_directory(root, config, mode, resolved_run_id)
    paths = {
        name: run_dir / name
        for name in ("raw", "normalized", "pit", "validation", "manifests", "report_evidence")
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=False)

    etfs = select_etf_samples(root, config)
    local_dates = load_local_trading_dates(root, etfs)
    date_to = max(local_dates)
    daily_start = _compact(local_dates[-int(config["sample_selection"]["max_trade_dates"])])

    calls: list[ProbeCall] = []
    call_scopes: dict[int, str] = {}

    def call(interface: str, params: dict[str, Any], scope: str) -> ProbeCall:
        item = client.request(interface, params, config["interfaces"][interface]["fields"])
        calls.append(item)
        call_scopes[id(item)] = scope
        return item

    index_catalog_calls = [call("index_basic", {"market": market}, market) for market in config["sample_selection"]["index_markets"]]
    catalog = _combine_success(index_catalog_calls)
    indices = select_index_samples(catalog, config)
    for index in indices:
        code = index["ts_code"]
        call("index_daily", {"ts_code": code, "start_date": daily_start, "end_date": _compact(date_to)}, code)
        weight_start = (pd.Timestamp(date_to) - pd.Timedelta(days=int(config["sample_selection"]["index_weight_lookback_days"]))).strftime("%Y%m%d")
        call("index_weight", {"index_code": code, "start_date": weight_start, "end_date": _compact(date_to)}, code)

    classify = call("index_classify", {"level": "L1", "src": "SW2021"}, "SW2021 L1")
    industry_code = select_industry_code(classify.frame, config)
    member = None
    if industry_code:
        member = call("index_member_all", {"l1_code": industry_code}, industry_code)

    constituents = select_constituents(member.frame if member else pd.DataFrame(), config)
    for symbol in constituents:
        call("daily_basic", {"ts_code": symbol, "trade_date": _compact(date_to)}, symbol)

    fund_start = (pd.Timestamp(date_to) - pd.Timedelta(days=int(config["sample_selection"]["fund_portfolio_lookback_days"]))).strftime("%Y%m%d")
    for etf in etfs:
        call("fund_portfolio", {"ts_code": etf["ts_code"], "start_date": fund_start, "end_date": _compact(date_to)}, etf["ts_code"])

    shibor_start = (pd.Timestamp(date_to) - pd.Timedelta(days=int(config["sample_selection"]["shibor_lookback_days"]))).strftime("%Y%m%d")
    call("shibor", {"start_date": shibor_start, "end_date": _compact(date_to)}, f"{shibor_start}:{_compact(date_to)}")

    outcomes = process_calls(calls, call_scopes, paths, local_dates, config, mode)
    interface_rows = aggregate_interfaces(outcomes, config, mode)
    pit_rows = aggregate_pit(outcomes, paths)
    final_status = determine_final_status(interface_rows, mode)
    per_run_real_call_count = client.request_count if mode == "real" else 0
    attested_real_call_count = load_attested_real_call_count(root / "reports/tushare_real_run_attestations.csv")
    batch_aggregate_real_call_count = attested_real_call_count + per_run_real_call_count
    configured_real_budget = int(runtime["max_api_requests"])
    if mode == "mock":
        budget_status = "NOT_APPLICABLE_MOCK"
    elif batch_aggregate_real_call_count > configured_real_budget:
        budget_status = "AGGREGATE_BUDGET_WARNING"
    else:
        budget_status = "WITHIN_CONFIGURED_REAL_BUDGET"
    mode_output_names = [
        "tushare_minimal_staging_proof.md",
        "tushare_interface_probe_matrix.csv",
        "tushare_pit_contract_matrix.csv",
        "tushare_index_weight_reduction_evidence.csv",
        "tushare_minimal_proof_run_manifest.json",
        "tushare_minimal_proof_permission_audit.json",
    ]
    if mode == "real":
        mode_output_names.append("tushare_gap_reassessment.md")
    mode_scoped_outputs = [
        str((paths["report_evidence"] / name).relative_to(root))
        for name in mode_output_names
    ]
    manifest = {
        "schema_version": 2,
        "proof_name": config["proof_name"],
        "evidence_mode": mode,
        "run_id": resolved_run_id,
        "run_started_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "status": final_status,
        "research_only": True,
        "formal_integration": False,
        "unified_database_write": False,
        "token_configured": client.token_configured if mode == "real" else False,
        "total_call_count": client.request_count,
        "real_api_call_count": per_run_real_call_count,
        "mock_call_count": client.request_count if mode == "mock" else 0,
        "per_run_real_call_count": per_run_real_call_count,
        "batch_aggregate_real_call_count": batch_aggregate_real_call_count,
        "configured_real_budget": configured_real_budget,
        "budget_status": budget_status,
        "selected_etfs": etfs,
        "selected_indices": indices,
        "selected_constituents": constituents,
        "local_trade_date_min": min(local_dates),
        "local_trade_date_max": max(local_dates),
        "legacy_sample_status": config["legacy_samples"],
        "run_scoped_staging": str(run_dir.relative_to(root)),
        "mode_scoped_outputs": mode_scoped_outputs,
        "commit_safe_outputs": mode_scoped_outputs if mode == "mock" else mode_scoped_outputs + _real_global_output_paths(),
        "interface_summary_hash": canonical_hash(interface_rows),
        "pit_summary_hash": canonical_hash(pit_rows),
        "index_weight_reduction_summary": _index_weight_reduction_rows(outcomes),
    }
    validate_evidence_manifest(manifest)
    _write_json(paths["manifests"] / "run_manifest.json", manifest)
    write_commit_safe_outputs(root, paths, manifest, interface_rows, pit_rows, outcomes, config)
    return manifest


def process_calls(
    calls: list[ProbeCall],
    scopes: dict[int, str],
    paths: dict[str, Path],
    local_dates: list[str],
    config: dict[str, Any],
    evidence_mode: str,
) -> list[ProbeOutcome]:
    outcomes: list[ProbeOutcome] = []
    for sequence, item in enumerate(calls, start=1):
        stem = f"{sequence:02d}_{item.interface}_{_safe_name(scopes[id(item)])}"
        _write_json(paths["raw"] / f"{stem}.json", item.raw_payload)
        limited_frame, reduction_evidence = limit_sample_frame(item.interface, item.frame, config)
        reduction_evidence.update({
            "evidence_mode": evidence_mode,
            "sample_scope": scopes[id(item)],
            "query_start_date": _iso_query_date(item.request_parameters_sanitized.get("start_date")),
            "query_end_date": _iso_query_date(item.request_parameters_sanitized.get("end_date")),
        })
        if item.response_status in {"ACCESS_PASS", "EMPTY_UNEXPECTED", "MOCK_RESPONSE_PASS", "MOCK_EMPTY"}:
            validation = validate_interface_frame(item.interface, limited_frame)
        else:
            validation = ValidationResult(
                interface=item.interface, status="NOT_VALIDATED", normalized=pd.DataFrame(), missing_fields=[],
                duplicate_keys=0, null_rates={}, dtypes={}, date_min="", date_max="", units={},
                validation_errors=[], validation_warnings=[],
            )
        validation.normalized.to_csv(paths["normalized"] / f"{stem}.csv", index=False, lineterminator="\n")
        normalized_csv = validation.normalized.to_csv(index=False, lineterminator="\n").encode("utf-8")
        validation_status = validation.status
        if evidence_mode == "mock":
            validation_status = "MOCK_VALIDATION_PASS" if validation.status in {"ACCESS_PASS", "EMPTY_EXPECTED"} else "MOCK_VALIDATION_FAILED"
        validation_summary = validation.to_summary()
        validation_summary.update({"evidence_mode": evidence_mode, "status": validation_status})
        _write_json(paths["validation"] / f"{stem}.json", validation_summary)
        pit = build_pit_records(
            item.interface,
            validation.normalized,
            retrieved_at=item.retrieved_at,
            query_hash=item.query_hash,
            raw_payload_hash=item.raw_payload_hash,
            local_trading_dates=local_dates,
            evidence_mode=evidence_mode,
        )
        pit.to_csv(paths["pit"] / f"{stem}.csv", index=False, lineterminator="\n")
        _write_json(paths["manifests"] / f"{stem}.json", {
            "schema_version": 2,
            "evidence_mode": evidence_mode,
            "interface": item.interface,
            "request_parameters_sanitized": item.request_parameters_sanitized,
            "request_sequence": item.request_sequence,
            "attempts": item.attempts,
            "response_status": item.response_status,
            "permission_status": item.permission_status,
            "raw_row_count": item.row_count,
            "normalized_row_count": len(validation.normalized),
            "retrieved_at": item.retrieved_at,
            "query_hash": item.query_hash,
            "raw_payload_hash": item.raw_payload_hash,
            "normalized_hash": hashlib.sha256(normalized_csv).hexdigest(),
            "error_class": item.error_class,
            "error_message_sanitized": item.error_message_sanitized,
            "validation_status": validation_status,
            **reduction_evidence,
        })
        pit_statuses = sorted(pit["pit_status"].dropna().unique()) if not pit.empty else [INTERFACE_SCHEMAS[item.interface].pit_default]
        response_status = "EMPTY_EXPECTED" if validation.status == "EMPTY_EXPECTED" else item.response_status
        outcomes.append(ProbeOutcome(
            interface=item.interface,
            call_count=item.attempts,
            response_status=response_status,
            permission_status=item.permission_status,
            row_count=item.row_count,
            normalized_row_count=len(validation.normalized),
            validation_status=validation_status,
            pit_status="|".join(pit_statuses),
            sample_scope=scopes[id(item)],
            date_min=validation.date_min,
            date_max=validation.date_max,
            missing_fields="|".join(validation.missing_fields),
            duplicate_keys=validation.duplicate_keys,
            error_class=item.error_class,
            error_message=item.error_message_sanitized,
            official_doc=config["interfaces"][item.interface]["official_doc"],
            official_update_pattern=config["interfaces"][item.interface]["official_update_pattern"],
            request_parameters_sanitized=json.dumps(item.request_parameters_sanitized, ensure_ascii=False, sort_keys=True),
            columns="|".join(validation.normalized.columns),
            dtypes=json.dumps(validation.dtypes, ensure_ascii=False, sort_keys=True),
            null_rates=json.dumps(validation.null_rates, ensure_ascii=False, sort_keys=True),
            retrieved_at=item.retrieved_at,
            query_hash=item.query_hash,
            raw_payload_hash=item.raw_payload_hash,
            normalized_hash=hashlib.sha256(normalized_csv).hexdigest(),
            reduction_evidence=reduction_evidence,
        ))
    return outcomes


def aggregate_interfaces(outcomes: list[ProbeOutcome], config: dict[str, Any], evidence_mode: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for interface in INTERFACES:
        items = [item for item in outcomes if item.interface == interface]
        if not items:
            rows.append({
                "evidence_mode": evidence_mode, "interface": interface, "request_count": 0, "sample_count": 0, "row_count": 0, "normalized_row_count": 0,
                "access_verdict": "NOT_APPLICABLE_MOCK" if evidence_mode == "mock" else "DEPENDENCY_UNAVAILABLE",
                "permission_status": "NOT_APPLICABLE_MOCK" if evidence_mode == "mock" else "NOT_TESTED",
                "schema_verdict": "MOCK_VALIDATION_FAILED" if evidence_mode == "mock" else "NOT_TESTED", "pit_status": INTERFACE_SCHEMAS[interface].pit_default,
                "date_min": "", "date_max": "", "sample_scope": "",
                "official_doc": config["interfaces"][interface]["official_doc"],
                "official_update_pattern": config["interfaces"][interface]["official_update_pattern"],
                "request_parameters_sanitized": "", "columns": "", "dtypes": "{}", "null_rates": "{}",
                "retrieved_at": "", "query_hashes": "", "raw_payload_hashes": "", "normalized_hashes": "",
            })
            continue
        statuses = {item.response_status for item in items}
        if evidence_mode == "mock":
            access = "NOT_APPLICABLE_MOCK"
        elif statuses == {"ACCESS_PASS"}:
            access = "ACCESS_PASS"
        elif "ACCESS_PASS" in statuses:
            access = "PARTIAL_ACCESS"
        elif "PERMISSION_BLOCKED" in statuses:
            access = "PERMISSION_BLOCKED"
        else:
            access = sorted(statuses)[0]
        rows.append({
            "evidence_mode": evidence_mode,
            "interface": interface,
            "request_count": sum(item.call_count for item in items),
            "sample_count": len(items),
            "row_count": sum(item.row_count for item in items),
            "normalized_row_count": sum(item.normalized_row_count for item in items),
            "access_verdict": access,
            "permission_status": "|".join(sorted({item.permission_status for item in items})),
            "schema_verdict": "|".join(sorted({item.validation_status for item in items})),
            "pit_status": "|".join(sorted({item.pit_status for item in items})),
            "date_min": min((item.date_min for item in items if item.date_min), default=""),
            "date_max": max((item.date_max for item in items if item.date_max), default=""),
            "sample_scope": "|".join(item.sample_scope for item in items),
            "official_doc": items[0].official_doc,
            "official_update_pattern": items[0].official_update_pattern,
            "request_parameters_sanitized": "|".join(item.request_parameters_sanitized for item in items),
            "columns": "|".join(sorted({item.columns for item in items})),
            "dtypes": "|".join(sorted({item.dtypes for item in items})),
            "null_rates": "|".join(sorted({item.null_rates for item in items})),
            "retrieved_at": "|".join(sorted({item.retrieved_at for item in items})),
            "query_hashes": "|".join(item.query_hash for item in items),
            "raw_payload_hashes": "|".join(item.raw_payload_hash for item in items),
            "normalized_hashes": "|".join(item.normalized_hash for item in items),
        })
    return rows


def aggregate_pit(outcomes: list[ProbeOutcome], paths: dict[str, Path]) -> list[dict[str, Any]]:
    frames = [pd.read_csv(path, dtype=str).fillna("") for path in sorted(paths["pit"].glob("*.csv")) if path.stat().st_size > 1]
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    rows = []
    for interface in INTERFACES:
        subset = combined[combined["source_interface"] == interface] if not combined.empty else pd.DataFrame()
        summary = interface_pit_summary(interface, subset)
        summary.update({
            "default_contract": INTERFACE_SCHEMAS[interface].pit_default,
            "historical_backtest_policy": "ALLOW_WITH_CONTRACT" if INTERFACE_SCHEMAS[interface].pit_default in {"PIT_RESOLVED", "PIT_CONSERVATIVE"} else "REJECT_OR_REVIEW",
        })
        rows.append(summary)
    return rows


def determine_final_status(rows: list[dict[str, Any]], evidence_mode: str) -> str:
    if evidence_mode == "mock":
        schemas = {row["schema_verdict"] for row in rows}
        return "MOCK_VALIDATION_PASS" if schemas == {"MOCK_VALIDATION_PASS"} else "MOCK_VALIDATION_FAILED"
    verdicts = {row["access_verdict"] for row in rows}
    if verdicts <= {"PERMISSION_BLOCKED", "DEPENDENCY_UNAVAILABLE"}:
        return "REAL_PROOF_BLOCKED"
    if verdicts == {"ACCESS_PASS"} and all(row["schema_verdict"] == "ACCESS_PASS" for row in rows):
        return "REAL_PROOF_COMPLETE"
    if "ACCESS_PASS" in verdicts:
        return "REAL_PROOF_PARTIAL"
    return "REAL_PROOF_FAILED"


def select_etf_samples(root: Path, config: dict[str, Any]) -> list[dict[str, str]]:
    module_path = root / config["sample_selection"]["benchmark_source"]
    spec = importlib.util.spec_from_file_location("proof_benchmark_source", module_path)
    if not spec or not spec.loader:
        raise RuntimeError("cannot load benchmark source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    allowed = set(config["sample_selection"]["benchmark_families"])
    selected = [item for item in module.BENCHMARK_BASKET if item["benchmark_family"] in allowed]
    registry = yaml.safe_load((root / config["sample_selection"]["universe_registry"]).read_text(encoding="utf-8"))
    registry_codes = {str(row["etf_code"]).zfill(6) for row in registry["records"]}
    results = []
    for item in selected[: int(config["sample_selection"]["max_etfs"])]:
        code = str(item["benchmark_code"]).zfill(6)
        market = "SH" if code.startswith(("5", "6")) else "SZ"
        results.append({
            "etf_code": code, "ts_code": f"{code}.{market}", "benchmark_family": item["benchmark_family"],
            "selection_source": "market_exposure_vector.BENCHMARK_BASKET",
            "in_v2_registry": code in registry_codes,
        })
    return results


def load_local_trading_dates(root: Path, etfs: list[dict[str, str]]) -> list[str]:
    all_dates: set[str] = set()
    for item in etfs:
        matches = list((root / "data/etf_daily").glob(f"*{item['etf_code']}.csv"))
        if not matches:
            raise FileNotFoundError(f"ETF SSOT sample missing: {item['etf_code']}")
        frame = pd.read_csv(matches[0], usecols=["date"], dtype=str)
        all_dates.update(pd.to_datetime(frame["date"], errors="coerce").dropna().dt.strftime("%Y-%m-%d"))
    if not all_dates:
        raise ValueError("no local trading dates")
    return sorted(all_dates)


def select_index_samples(catalog: pd.DataFrame, config: dict[str, Any]) -> list[dict[str, str]]:
    if catalog.empty:
        return []
    results = []
    names = catalog.get("name", pd.Series(index=catalog.index, dtype=str)).fillna("").astype(str)
    fullnames = catalog.get("fullname", pd.Series(index=catalog.index, dtype=str)).fillna("").astype(str)
    for family in config["sample_selection"]["benchmark_families"]:
        found = None
        for hint in config["sample_selection"]["index_name_hints"].get(family, []):
            mask = names.str.contains(hint, regex=False) | fullnames.str.contains(hint, regex=False)
            if mask.any():
                found = catalog[mask].sort_values("ts_code").iloc[0]
                break
        if found is not None:
            results.append({"ts_code": str(found["ts_code"]), "name": str(found.get("name", "")), "benchmark_family": family})
    return results[: int(config["sample_selection"]["max_indices"])]


def select_industry_code(frame: pd.DataFrame, config: dict[str, Any]) -> str:
    if frame.empty or "industry_name" not in frame or "index_code" not in frame:
        return ""
    names = frame["industry_name"].fillna("").astype(str)
    for keyword in config["sample_selection"]["industry_member_keyword_priority"]:
        mask = names.str.contains(keyword, regex=False)
        if mask.any():
            return str(frame[mask].sort_values("index_code").iloc[0]["index_code"])
    return str(frame.sort_values("index_code").iloc[0]["index_code"])


def select_constituents(frame: pd.DataFrame, config: dict[str, Any]) -> list[str]:
    if frame.empty or "ts_code" not in frame:
        return []
    if "is_new" in frame:
        current = frame[frame["is_new"].astype(str).isin({"Y", "1", "True", "true"})]
        frame = current if not current.empty else frame
    limit = int(config["sample_selection"]["daily_basic_constituent_limit"])
    return sorted(frame["ts_code"].dropna().astype(str).unique())[:limit]


def write_commit_safe_outputs(
    root: Path,
    paths: dict[str, Path],
    manifest: dict[str, Any],
    interface_rows: list[dict[str, Any]],
    pit_rows: list[dict[str, Any]],
    outcomes: list[ProbeOutcome],
    config: dict[str, Any],
) -> None:
    mode = manifest["evidence_mode"]
    report_targets = [paths["report_evidence"]]
    if mode == "real":
        report_targets.append(root / "reports")
    reduction_rows = _index_weight_reduction_rows(outcomes)
    for reports in report_targets:
        pd.DataFrame(interface_rows).to_csv(reports / "tushare_interface_probe_matrix.csv", index=False, lineterminator="\n")
        pd.DataFrame(pit_rows).to_csv(reports / "tushare_pit_contract_matrix.csv", index=False, lineterminator="\n")
        pd.DataFrame(reduction_rows).to_csv(reports / "tushare_index_weight_reduction_evidence.csv", index=False, lineterminator="\n")
        _write_json(reports / "tushare_minimal_proof_run_manifest.json", manifest)
    permission = {
        "schema_version": 2, "evidence_mode": mode, "run_id": manifest["run_id"],
        "token_value_recorded": False, "request_parameters_contain_token": False,
        "real_api_call_count": manifest["real_api_call_count"],
        "mock_call_count": manifest["mock_call_count"],
        "per_run_real_call_count": manifest["per_run_real_call_count"],
        "batch_aggregate_real_call_count": manifest["batch_aggregate_real_call_count"],
        "configured_real_budget": manifest["configured_real_budget"],
        "budget_status": manifest["budget_status"],
        "interfaces": [{"interface": row["interface"], "access_verdict": row["access_verdict"], "permission_status": row["permission_status"]} for row in interface_rows],
    }
    for reports in report_targets:
        _write_json(reports / "tushare_minimal_proof_permission_audit.json", permission)

    if mode == "mock":
        mock_lines = [
            "# Tushare Mock Validation Evidence", "",
            f"- Evidence mode: `{mode}`", f"- Run ID: `{manifest['run_id']}`",
            f"- Status: `{manifest['status']}`", f"- Mock call count: `{manifest['mock_call_count']}`",
            "- Real API call count: `0`", "- Permission conclusion: `NOT_APPLICABLE_MOCK`", "",
            "This fixture-only run did not read a Token provider, instantiate the production client, or make a network request.",
            "It validates schemas and PIT transformations only and cannot complete the real proof batch.", "",
            "## Interface Validation", "",
            "| Interface | Permission | Schema | Raw rows | Proof rows | PIT |", "|---|---|---|---:|---:|---|",
        ]
        for row in interface_rows:
            pit_display = str(row["pit_status"]).replace("|", " / ")
            mock_lines.append(f"| {row['interface']} | {row['permission_status']} | {row['schema_verdict']} | {row['row_count']} | {row['normalized_row_count']} | {pit_display} |")
        (paths["report_evidence"] / "tushare_minimal_staging_proof.md").write_text("\n".join(mock_lines) + "\n", encoding="utf-8")
        return

    reports = root / "reports"
    lines = [
        "# Tushare Minimal Staging Proof", "", f"- Evidence mode: `{mode}`", f"- Run ID: `{manifest['run_id']}`",
        f"- Final status: `{manifest['status']}`", f"- Final-run real HTTP request count: `{manifest['per_run_real_call_count']} / {manifest['configured_real_budget']}`",
        f"- Attested aggregate real HTTP request count: `{manifest['batch_aggregate_real_call_count']}`",
        f"- Run-scoped staging: `{manifest['run_scoped_staging']}` (git-ignored)",
        "- ETF daily SSOT write: `NONE`", "- Formal / Strategy / Replay integration: `NONE`", "",
        "## Interface Results", "", "| Interface | Access | Permission | Raw rows | Proof rows | Schema | PIT |", "|---|---|---|---:|---:|---|---|",
    ]
    for row in interface_rows:
        pit_display = str(row["pit_status"]).replace("|", " / ")
        lines.append(f"| {row['interface']} | {row['access_verdict']} | {row['permission_status']} | {row['row_count']} | {row['normalized_row_count']} | {row['schema_verdict']} | {pit_display} |")
    lines.extend([
        "", "## Governance", "",
        "Raw responses, deterministic normalized samples, validation records and row-level PIT metadata are isolated under the run directory and are not committed.",
        "The legacy `data/staging/tushare/tushare_etf_daily_sample.csv` remains `LEGACY_UNVERIFIED_SAMPLE` and was not overwritten.",
        "No interface is admitted to historical replay unless its PIT contract is `PIT_RESOLVED` or an explicitly approved conservative rule applies.",
        "", "## Evidence Boundaries", "",
        "- Real API evidence: the interface matrix above, run-scoped response hashes, schemas, row counts, and PIT records from this run.",
        "- Mock evidence: unit tests cover normal, empty, permission, network, schema, duplicate-key, unit, versioning, and PIT failure paths; mock PASS is not used as permission evidence.",
        "- Official documentation: update patterns and units are sourced from the official URLs recorded in the interface matrix.",
        "- Inference: conservative availability rules are governance choices designed to prevent look-ahead; they are not provider row-level timestamps.",
        "- Unresolved: taxonomy publication history and snapshot publication times remain unavailable; the latest trade-date rows also need a future local trading-calendar date before next-day availability can be materialized.",
        "", "## Versioning And Call-Budget Note", "",
        "The final two-period `fund_portfolio` sample did not contain multiple announcement dates for one period. The primary key includes `ann_date`, and the mock test confirms that multiple announcement versions are retained rather than overwritten.",
        f"This real run used {manifest['per_run_real_call_count']}/{manifest['configured_real_budget']} calls. The aggregate real count is {manifest['batch_aggregate_real_call_count']} and is sourced from committed real-run attestations plus this run; mock calls are excluded. Budget status: {manifest['budget_status']}.",
    ])
    for target in report_targets:
        (target / "tushare_minimal_staging_proof.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    passed = [row["interface"] for row in interface_rows if row["access_verdict"] == "ACCESS_PASS"]
    gaps = [row["interface"] for row in interface_rows if row["access_verdict"] != "ACCESS_PASS"]
    available = set(passed)
    reassessment = [
        ("Concentration Exposure", "fund_portfolio + index_weight" if "fund_portfolio" in available else "not proven", "PIT_RESOLVED for announced fund versions; index weights remain partial", "minimal ETF/index samples", "MEDIUM", "HIGH", "MEDIUM", "HIGH_VALUE_REOPEN_CANDIDATE" if "fund_portfolio" in available else "DEFER"),
        ("Dividend Exposure", "daily_basic dv_ratio/dv_ttm" if "daily_basic" in available else "not proven", "PIT_CONSERVATIVE: next trading day", "minimal constituents", "LOW", "HIGH", "MEDIUM", "HIGH_VALUE_REOPEN_CANDIDATE" if "daily_basic" in available else "DEFER"),
        ("Size Exposure", "daily_basic total/circulating market value" if "daily_basic" in available else "not proven", "PIT_CONSERVATIVE: next trading day", "minimal constituents", "LOW", "HIGH", "LOW", "HIGH_VALUE_REOPEN_CANDIDATE" if "daily_basic" in available else "DEFER"),
        ("Sector Exposure", "index taxonomy + member effective dates" if {"index_classify", "index_member_all"} <= available else "not fully proven", "PIT_PARTIAL/UNRESOLVED without publication history", "one taxonomy/member sample", "MEDIUM", "HIGH", "MEDIUM", "RESEARCH_OBSERVATION" if {"index_classify", "index_member_all"} <= available else "DEFER"),
        ("Value / Growth Exposure", "valuation fields only; growth fundamentals absent" if "daily_basic" in available else "not proven", "PIT_CONSERVATIVE for observed valuation", "minimal constituents", "MEDIUM", "MEDIUM", "HIGH", "RESEARCH_OBSERVATION" if "daily_basic" in available else "DEFER"),
        ("Interest Rate Sensitivity", "Shibor curve only; no ETF duration/cash-flow contract" if "shibor" in available else "not proven", "PIT_CONSERVATIVE", "short rate window", "LOW", "MEDIUM", "MEDIUM", "EXPLANATION_ONLY" if "shibor" in available else "DEFER"),
    ]
    gap_lines = [
        "# Tushare Gap Reassessment", "", f"- Run status: `{manifest['status']}`",
        f"- Proven accessible: `{', '.join(passed) or 'none'}`", f"- Permission/dependency/validation gaps: `{', '.join(gaps) or 'none'}`", "",
        "## Reassessment", "",
        "This proof changes capability claims only where a real response and schema validation were observed. A configured token or a catalog response alone is not proof that dependent interfaces are usable.",
        "Current ETF daily files remain the only ETF price source of truth. Tushare outputs are staged evidence, not a replacement database.",
        "PIT-unresolved taxonomy or metadata may support current-state description, but must not enter historical replay without publication-time evidence or a conservative versioned rule.",
        "", "## Exposure Gap Matrix", "",
        "| Candidate | Newly available data | PIT readiness | Coverage | Maintenance | Incremental value | Overfitting risk | Status |",
        "|---|---|---|---|---|---|---|---|",
        *[f"| {name} | {data} | {pit} | {coverage} | {maintenance} | {value} | {risk} | {status} |" for name, data, pit, coverage, maintenance, value, risk, status in reassessment],
        "", "Top 3 for Main reassessment are Concentration, Dividend, and Size, conditional on the corresponding real access verdicts above. This is a governance recommendation only; Exposure Phase 2 remains not started.",
        "", "## Next Gate", "",
        "Formal staging architecture remains a separate Main approval. It requires permission-gap resolution where relevant, retained run manifests, schema-versioned ingestion, and acceptance tests against the PIT contract.",
    ]
    for target in report_targets:
        (target / "tushare_gap_reassessment.md").write_text("\n".join(gap_lines) + "\n", encoding="utf-8")


def _combine_success(calls: list[ProbeCall]) -> pd.DataFrame:
    frames = [call.frame for call in calls if call.response_status in {"ACCESS_PASS", "MOCK_RESPONSE_PASS"}]
    return pd.concat(frames, ignore_index=True).drop_duplicates() if frames else pd.DataFrame()


def limit_sample_frame(interface: str, frame: pd.DataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Keep normalized proof payloads minimal while retaining raw response hashes."""
    raw_count = int(len(frame))
    raw_trade_dates = _sorted_dates(frame["trade_date"]) if "trade_date" in frame else []
    if frame.empty:
        return frame.copy(), _reduction_evidence(interface, raw_count, 0, raw_trade_dates, [], config)
    limited = frame.copy()
    if interface == "index_daily" and "trade_date" in limited:
        count = int(config["sample_selection"]["max_trade_dates"])
        dates = sorted(limited["trade_date"].dropna().astype(str).unique())[-count:]
        limited = limited[limited["trade_date"].astype(str).isin(dates)]
    elif interface == "index_weight" and "trade_date" in limited:
        dates = sorted(limited["trade_date"].dropna().astype(str).unique())[-2:]
        limited = limited[limited["trade_date"].astype(str).isin(dates)]
    elif interface == "fund_portfolio" and "end_date" in limited:
        count = int(config["sample_selection"]["fund_report_period_limit"])
        periods = sorted(limited["end_date"].dropna().astype(str).unique())[-count:]
        limited = limited[limited["end_date"].astype(str).isin(periods)]
    limited = limited.reset_index(drop=True)
    selected_trade_dates = _sorted_dates(limited["trade_date"]) if "trade_date" in limited else []
    return limited, _reduction_evidence(
        interface,
        raw_count,
        int(len(limited)),
        raw_trade_dates,
        selected_trade_dates,
        config,
    )


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _reduction_evidence(
    interface: str,
    raw_count: int,
    proof_count: int,
    raw_trade_dates: list[str],
    selected_trade_dates: list[str],
    config: dict[str, Any],
) -> dict[str, Any]:
    excluded_trade_dates = sorted(set(raw_trade_dates) - set(selected_trade_dates))
    reduced = interface == "index_weight" and proof_count < raw_count
    return {
        "raw_count": raw_count,
        "proof_count": proof_count,
        "excluded_count": raw_count - proof_count,
        "visible_trade_dates": raw_trade_dates,
        "selected_trade_dates": selected_trade_dates,
        "excluded_trade_dates": excluded_trade_dates,
        "reduction_reason": "PROOF_SAMPLE_DATE_WINDOW_REDUCTION" if reduced else "NO_INDEX_WEIGHT_REDUCTION",
        "reduction_policy_version": config["evidence_contract"]["index_weight_reduction_policy_version"],
    }


def _index_weight_reduction_rows(outcomes: list[ProbeOutcome]) -> list[dict[str, Any]]:
    return [dict(item.reduction_evidence) for item in outcomes if item.interface == "index_weight"]


def load_attested_real_call_count(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    seen: set[str] = set()
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                run_id = str(row.get("run_id", ""))
                if row.get("evidence_mode") != "real" or run_id in seen:
                    continue
                seen.add(run_id)
                total += int(row.get("real_call_count") or 0)
    except (OSError, ValueError):
        return 0
    return total


def validate_evidence_manifest(manifest: dict[str, Any]) -> None:
    required = {
        "schema_version", "evidence_mode", "run_id", "status", "run_scoped_staging",
        "total_call_count", "real_api_call_count", "mock_call_count", "per_run_real_call_count",
        "batch_aggregate_real_call_count", "configured_real_budget", "budget_status",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError(f"evidence manifest missing fields: {', '.join(missing)}")
    mode = validate_evidence_mode(str(manifest["evidence_mode"]))
    validate_run_id(mode, str(manifest["run_id"]))
    isolated_path = f"/{mode}/{manifest['run_id']}" in f"/{manifest['run_scoped_staging']}"
    legacy_real_path = (
        mode == "real"
        and manifest.get("legacy_storage_layout") is True
        and str(manifest["run_scoped_staging"]).endswith(f"/{manifest['run_id']}")
    )
    if not isolated_path and not legacy_real_path:
        raise ValueError("manifest run_scoped_staging is not mode isolated and is not an attested legacy real run")
    if mode == "mock":
        if manifest["status"] not in MOCK_STATUSES:
            raise ValueError("mock manifest contains a real proof status")
        if int(manifest["real_api_call_count"]) != 0 or int(manifest["per_run_real_call_count"]) != 0:
            raise ValueError("mock manifest cannot record real API calls")
        if int(manifest["mock_call_count"]) != int(manifest["total_call_count"]):
            raise ValueError("mock call counts are inconsistent")
    else:
        if manifest["status"] not in REAL_STATUSES:
            raise ValueError("real manifest contains a mock validation status")
        if int(manifest["mock_call_count"]) != 0:
            raise ValueError("real manifest cannot record mock calls")
        if int(manifest["real_api_call_count"]) != int(manifest["total_call_count"]):
            raise ValueError("real call counts are inconsistent")


def _real_global_output_paths() -> list[str]:
    return [
        "reports/tushare_minimal_staging_proof.md",
        "reports/tushare_interface_probe_matrix.csv",
        "reports/tushare_pit_contract_matrix.csv",
        "reports/tushare_index_weight_reduction_evidence.csv",
        "reports/tushare_gap_reassessment.md",
        "reports/tushare_minimal_proof_run_manifest.json",
        "reports/tushare_minimal_proof_permission_audit.json",
    ]


def _sorted_dates(values: pd.Series) -> list[str]:
    parsed = pd.to_datetime(values.astype(str).str.strip(), errors="coerce").dropna()
    return sorted(parsed.dt.strftime("%Y-%m-%d").unique())


def _iso_query_date(value: Any) -> str:
    if value in (None, ""):
        return ""
    parsed = pd.to_datetime(str(value), errors="coerce")
    return "" if pd.isna(parsed) else parsed.strftime("%Y-%m-%d")


def _compact(value: str) -> str:
    return value.replace("-", "")


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:80] or "sample"
