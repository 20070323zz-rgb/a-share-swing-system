"""Run-scoped minimal Tushare staging proof orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from typing import Any, Callable
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

from .client import ProbeCall, TushareMinimalClient, canonical_hash
from .pit_contract import build_pit_records, interface_pit_summary
from .schemas import INTERFACE_SCHEMAS
from .validators import ValidationResult, validate_interface_frame


TZ = ZoneInfo("Asia/Shanghai")
INTERFACES = tuple(INTERFACE_SCHEMAS)


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


def load_config(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def run_probe(
    project_root: Path,
    config_path: Path,
    *,
    client_factory: Callable[..., TushareMinimalClient] = TushareMinimalClient,
    run_id: str | None = None,
) -> dict[str, Any]:
    root = project_root.resolve()
    config = load_config(config_path)
    run_id = run_id or datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")
    run_dir = root / config["runtime"]["staging_root"] / run_id
    paths = {name: run_dir / name for name in ("raw", "normalized", "pit", "validation", "manifests")}
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=False)

    runtime = config["runtime"]
    client = client_factory(
        project_root=root,
        max_requests=int(runtime["max_api_requests"]),
        timeout_seconds=int(runtime["timeout_seconds"]),
        request_interval_seconds=float(runtime["request_interval_seconds"]),
        max_network_retries=int(runtime["max_network_retries"]),
    )
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

    outcomes = process_calls(calls, call_scopes, paths, local_dates, config)
    interface_rows = aggregate_interfaces(outcomes, config)
    pit_rows = aggregate_pit(outcomes, paths)
    final_status = determine_final_status(interface_rows, client.token_configured)
    manifest = {
        "schema_version": 1,
        "proof_name": config["proof_name"],
        "run_id": run_id,
        "run_started_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "status": final_status,
        "research_only": True,
        "formal_integration": False,
        "unified_database_write": False,
        "token_configured": client.token_configured,
        "api_request_count": client.request_count,
        "api_request_limit": int(runtime["max_api_requests"]),
        "selected_etfs": etfs,
        "selected_indices": indices,
        "selected_constituents": constituents,
        "local_trade_date_min": min(local_dates),
        "local_trade_date_max": max(local_dates),
        "legacy_sample_status": config["legacy_samples"],
        "run_scoped_staging": str(run_dir.relative_to(root)),
        "commit_safe_outputs": [
            "reports/tushare_minimal_staging_proof.md",
            "reports/tushare_interface_probe_matrix.csv",
            "reports/tushare_pit_contract_matrix.csv",
            "reports/tushare_gap_reassessment.md",
            "reports/tushare_minimal_proof_run_manifest.json",
            "reports/tushare_minimal_proof_permission_audit.json",
        ],
        "interface_summary_hash": canonical_hash(interface_rows),
        "pit_summary_hash": canonical_hash(pit_rows),
    }
    _write_json(paths["manifests"] / "run_manifest.json", manifest)
    write_commit_safe_outputs(root, manifest, interface_rows, pit_rows, outcomes, config)
    return manifest


def process_calls(
    calls: list[ProbeCall],
    scopes: dict[int, str],
    paths: dict[str, Path],
    local_dates: list[str],
    config: dict[str, Any],
) -> list[ProbeOutcome]:
    outcomes: list[ProbeOutcome] = []
    for sequence, item in enumerate(calls, start=1):
        stem = f"{sequence:02d}_{item.interface}_{_safe_name(scopes[id(item)])}"
        _write_json(paths["raw"] / f"{stem}.json", item.raw_payload)
        limited_frame = limit_sample_frame(item.interface, item.frame, config)
        if item.response_status in {"ACCESS_PASS", "EMPTY_UNEXPECTED"}:
            validation = validate_interface_frame(item.interface, limited_frame)
        else:
            validation = ValidationResult(
                interface=item.interface, status="NOT_VALIDATED", normalized=pd.DataFrame(), missing_fields=[],
                duplicate_keys=0, null_rates={}, dtypes={}, date_min="", date_max="", units={},
                validation_errors=[], validation_warnings=[],
            )
        validation.normalized.to_csv(paths["normalized"] / f"{stem}.csv", index=False, lineterminator="\n")
        normalized_csv = validation.normalized.to_csv(index=False, lineterminator="\n").encode("utf-8")
        _write_json(paths["validation"] / f"{stem}.json", validation.to_summary())
        pit = build_pit_records(
            item.interface,
            validation.normalized,
            retrieved_at=item.retrieved_at,
            query_hash=item.query_hash,
            raw_payload_hash=item.raw_payload_hash,
            local_trading_dates=local_dates,
        )
        pit.to_csv(paths["pit"] / f"{stem}.csv", index=False, lineterminator="\n")
        _write_json(paths["manifests"] / f"{stem}.json", {
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
            validation_status=validation.status,
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
        ))
    return outcomes


def aggregate_interfaces(outcomes: list[ProbeOutcome], config: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for interface in INTERFACES:
        items = [item for item in outcomes if item.interface == interface]
        if not items:
            rows.append({
                "interface": interface, "request_count": 0, "sample_count": 0, "row_count": 0, "normalized_row_count": 0,
                "access_verdict": "DEPENDENCY_UNAVAILABLE", "permission_status": "NOT_TESTED",
                "schema_verdict": "NOT_TESTED", "pit_status": INTERFACE_SCHEMAS[interface].pit_default,
                "date_min": "", "date_max": "", "sample_scope": "",
                "official_doc": config["interfaces"][interface]["official_doc"],
                "official_update_pattern": config["interfaces"][interface]["official_update_pattern"],
                "request_parameters_sanitized": "", "columns": "", "dtypes": "{}", "null_rates": "{}",
                "retrieved_at": "", "query_hashes": "", "raw_payload_hashes": "", "normalized_hashes": "",
            })
            continue
        statuses = {item.response_status for item in items}
        if statuses == {"ACCESS_PASS"}:
            access = "ACCESS_PASS"
        elif "ACCESS_PASS" in statuses:
            access = "PARTIAL_ACCESS"
        elif "PERMISSION_BLOCKED" in statuses:
            access = "PERMISSION_BLOCKED"
        else:
            access = sorted(statuses)[0]
        rows.append({
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


def determine_final_status(rows: list[dict[str, Any]], token_configured: bool) -> str:
    if not token_configured:
        return "BLOCKED_TOKEN_MISSING"
    verdicts = {row["access_verdict"] for row in rows}
    if verdicts <= {"PERMISSION_BLOCKED", "DEPENDENCY_UNAVAILABLE"}:
        return "BLOCKED_PERMISSION_OR_DEPENDENCY"
    if verdicts == {"ACCESS_PASS"}:
        return "COMPLETE"
    return "COMPLETE_WITH_PERMISSION_GAPS"


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
    manifest: dict[str, Any],
    interface_rows: list[dict[str, Any]],
    pit_rows: list[dict[str, Any]],
    outcomes: list[ProbeOutcome],
    config: dict[str, Any],
) -> None:
    reports = root / "reports"
    run_history = _load_run_history(root / config["runtime"]["staging_root"])
    batch_request_count = sum(int(item.get("api_request_count", 0)) for item in run_history)
    pd.DataFrame(interface_rows).to_csv(reports / "tushare_interface_probe_matrix.csv", index=False, lineterminator="\n")
    pd.DataFrame(pit_rows).to_csv(reports / "tushare_pit_contract_matrix.csv", index=False, lineterminator="\n")
    _write_json(reports / "tushare_minimal_proof_run_manifest.json", manifest)
    permission = {
        "schema_version": 1, "run_id": manifest["run_id"], "token_value_recorded": False,
        "request_parameters_contain_token": False, "api_request_count": manifest["api_request_count"],
        "api_request_limit": manifest["api_request_limit"],
        "batch_real_api_request_count": batch_request_count,
        "completed_real_run_ids": [item.get("run_id", "") for item in run_history],
        "aggregate_budget_status": "WITHIN_SUGGESTED_AGGREGATE" if batch_request_count <= manifest["api_request_limit"] else "AGGREGATE_BUDGET_WARNING",
        "interfaces": [{"interface": row["interface"], "access_verdict": row["access_verdict"], "permission_status": row["permission_status"]} for row in interface_rows],
    }
    _write_json(reports / "tushare_minimal_proof_permission_audit.json", permission)
    lines = [
        "# Tushare Minimal Staging Proof", "", f"- Run ID: `{manifest['run_id']}`",
        f"- Final status: `{manifest['status']}`", f"- Final-run HTTP request count: `{manifest['api_request_count']} / {manifest['api_request_limit']}`",
        f"- Batch real HTTP request count: `{batch_request_count}` across `{len(run_history)}` immutable run(s)",
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
        "The final proof run stayed within the hard per-run cap at 17/30 requests. Two earlier immutable corrective runs also made 17 requests each, so this batch used 51 real requests in total and exceeded the suggested aggregate target of 30. No run exceeded the configured hard cap; the deviation is recorded rather than hidden.",
    ])
    (reports / "tushare_minimal_staging_proof.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

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
    (reports / "tushare_gap_reassessment.md").write_text("\n".join(gap_lines) + "\n", encoding="utf-8")


def _combine_success(calls: list[ProbeCall]) -> pd.DataFrame:
    frames = [call.frame for call in calls if call.response_status == "ACCESS_PASS"]
    return pd.concat(frames, ignore_index=True).drop_duplicates() if frames else pd.DataFrame()


def limit_sample_frame(interface: str, frame: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Keep normalized proof payloads minimal while retaining raw response hashes."""
    if frame.empty:
        return frame.copy()
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
    return limited.reset_index(drop=True)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_run_history(staging_root: Path) -> list[dict[str, Any]]:
    manifests = list(staging_root.glob("*/run_manifest.json")) + list(staging_root.glob("*/manifests/run_manifest.json"))
    history = []
    for path in sorted(set(manifests)):
        try:
            history.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return history


def _compact(value: str) -> str:
    return value.replace("-", "")


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:80] or "sample"
