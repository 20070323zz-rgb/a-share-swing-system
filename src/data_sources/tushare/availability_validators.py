"""Universe mapping and daily-bar quality validation for shadow audits."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

import pandas as pd

from .availability_models import CRITICAL_FIELDS, SNAPSHOT_FIELDS, UniverseRecord


FILE_RE = re.compile(r"^(sh|sz)_(\d{6})\.csv$")


def build_universe_mapping(project_root: Path, config: dict[str, Any]) -> tuple[list[UniverseRecord], dict[str, Any]]:
    root = project_root.resolve()
    daily_dir = root / config["universe"]["etf_daily_dir"]
    classification_path = root / config["universe"]["classification_file"]
    classification = pd.read_csv(classification_path, dtype=str).fillna("")
    roles = {}
    if {"symbol", "pool"} <= set(classification.columns):
        roles = dict(zip(classification["symbol"].str.zfill(6), classification["pool"]))

    records: list[UniverseRecord] = []
    invalid_files: list[str] = []
    inventory_files = sorted(daily_dir.glob("*.csv"))
    for path in inventory_files:
        match = FILE_RE.fullmatch(path.name)
        if not match:
            invalid_files.append(str(path.relative_to(root)))
            continue
        prefix, code = match.groups()
        exchange = "SH" if prefix == "sh" else "SZ"
        records.append(UniverseRecord(
            etf_code=code,
            ts_code=f"{code}.{exchange}",
            exchange=exchange,
            universe_role=roles.get(code, "UNCLASSIFIED"),
            file_path=str(path.relative_to(root)),
        ))

    codes = [item.etf_code for item in records]
    ts_codes = [item.ts_code for item in records]
    duplicate_codes = sorted({code for code in codes if codes.count(code) > 1})
    duplicate_ts_codes = sorted({code for code in ts_codes if ts_codes.count(code) > 1})
    unmapped_roles = sorted(item.etf_code for item in records if item.universe_role == "UNCLASSIFIED")
    expected = len(inventory_files)
    payload = {
        "count_source": str(config["universe"]["count_source"]),
        "expected_count": expected,
        "mapped_count": len(records),
        "mapping_complete": len(records) == expected and not invalid_files and not duplicate_codes and not duplicate_ts_codes and not unmapped_roles,
        "sh_count": sum(item.exchange == "SH" for item in records),
        "sz_count": sum(item.exchange == "SZ" for item in records),
        "invalid_files": invalid_files,
        "duplicate_codes": duplicate_codes,
        "duplicate_ts_codes": duplicate_ts_codes,
        "unmapped_role_codes": unmapped_roles,
        "mapping_hash": canonical_hash([item.__dict__ for item in records]),
    }
    return records, payload


def mapping_frame(records: list[UniverseRecord]) -> pd.DataFrame:
    return pd.DataFrame([item.__dict__ for item in records], columns=["etf_code", "ts_code", "exchange", "universe_role", "file_path"])


def normalize_vendor_frame(frame: pd.DataFrame, trade_date: str, source: str) -> pd.DataFrame:
    normalized = frame.copy()
    rename = {"date": "trade_date", "code": "source_code", "volume": "vol", "preclose": "pre_close"}
    normalized = normalized.rename(columns=rename)
    if source == "baostock" and "source_code" in normalized:
        normalized["ts_code"] = normalized["source_code"].astype(str).map(baostock_to_ts_code)
    for field in SNAPSHOT_FIELDS:
        if field not in normalized:
            normalized[field] = pd.NA
    normalized["ts_code"] = normalized["ts_code"].astype(str).str.strip().str.upper()
    normalized["trade_date"] = pd.to_datetime(normalized["trade_date"].astype(str), errors="coerce").dt.strftime("%Y-%m-%d")
    for field in SNAPSHOT_FIELDS[2:]:
        normalized[field] = pd.to_numeric(normalized[field], errors="coerce")
    normalized = normalized[list(SNAPSHOT_FIELDS)]
    return normalized[normalized["trade_date"] == trade_date].reset_index(drop=True)


def validate_snapshot(frame: pd.DataFrame, universe: list[UniverseRecord], trade_date: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    required = {item.ts_code for item in universe}
    exchange_by_code = {item.ts_code: item.exchange for item in universe}
    filtered = frame[frame["ts_code"].isin(required)].copy()
    duplicate_codes = sorted(filtered.loc[filtered.duplicated("ts_code", keep=False), "ts_code"].unique().tolist())
    unique = filtered.drop_duplicates("ts_code", keep="last").sort_values("ts_code", kind="mergesort").reset_index(drop=True)
    present = set(unique["ts_code"])
    missing = sorted(required - present)
    invalid_codes = sorted(code for code in present if not re.fullmatch(r"\d{6}\.(SH|SZ)", code))
    null_counts = {field: int(unique[field].isna().sum()) for field in SNAPSHOT_FIELDS}

    ohlc_null = unique[list(CRITICAL_FIELDS)].isna().any(axis=1)
    ohlc_bad = (~ohlc_null) & (
        (unique["close"] <= 0)
        | (unique["high"] < unique[["open", "close", "low"]].max(axis=1))
        | (unique["low"] > unique[["open", "close", "high"]].min(axis=1))
    )
    invalid_volume = unique["vol"].isna() | (unique["vol"] < 0)
    invalid_amount = unique["amount"].isna() | (unique["amount"] < 0)
    legal_zero = (unique["vol"].fillna(-1) == 0) & (unique["amount"].fillna(-1) == 0) & ~ohlc_null & ~ohlc_bad

    sh_required = sum(item.exchange == "SH" for item in universe)
    sz_required = sum(item.exchange == "SZ" for item in universe)
    sh_matched = sum(exchange_by_code.get(code) == "SH" for code in present)
    sz_matched = sum(exchange_by_code.get(code) == "SZ" for code in present)
    critical_error_count = int(ohlc_null.sum() + ohlc_bad.sum() + invalid_volume.sum() + invalid_amount.sum())
    field_complete = bool(not unique.empty and not unique[list(SNAPSHOT_FIELDS)].isna().any().any())
    snapshot_hash = snapshot_content_hash(unique)
    payload = {
        "trade_date_valid": bool(unique.empty or (unique["trade_date"] == trade_date).all()),
        "matched_etf_count": len(present),
        "coverage_ratio": len(present) / len(required) if required else 0.0,
        "sh_count": sh_matched,
        "sz_count": sz_matched,
        "sh_coverage_ratio": sh_matched / sh_required if sh_required else 0.0,
        "sz_coverage_ratio": sz_matched / sz_required if sz_required else 0.0,
        "missing_codes": missing,
        "duplicate_codes": duplicate_codes,
        "invalid_codes": invalid_codes,
        "null_field_counts": null_counts,
        "invalid_ohlc_count": int(ohlc_bad.sum() + ohlc_null.sum()),
        "invalid_volume_count": int(invalid_volume.sum()),
        "invalid_amount_count": int(invalid_amount.sum()),
        "legal_zero_volume_count": int(legal_zero.sum()),
        "critical_field_error_count": critical_error_count,
        "field_complete": field_complete,
        "quality_complete": len(present) == len(required) and not duplicate_codes and not invalid_codes and critical_error_count == 0 and field_complete,
        "source_snapshot_hash": snapshot_hash,
    }
    return unique, payload


def compare_snapshots(previous: pd.DataFrame | None, current: pd.DataFrame) -> dict[str, Any]:
    if previous is None or previous.empty:
        return {"revision_count": 0, "revised_code_count": 0, "revised_fields": [], "added_codes": [], "removed_codes": [], "material_revision": False, "previous_snapshot_hash": ""}
    old = previous.set_index("ts_code")
    new = current.set_index("ts_code")
    added = sorted(set(new.index) - set(old.index))
    removed = sorted(set(old.index) - set(new.index))
    revised_codes: set[str] = set()
    revised_fields: set[str] = set()
    for code in sorted(set(old.index) & set(new.index)):
        for field in SNAPSHOT_FIELDS[1:]:
            left, right = old.at[code, field], new.at[code, field]
            if not values_equal(left, right):
                revised_codes.add(code)
                revised_fields.add(field)
    material = bool(added or removed or revised_codes)
    return {
        "revision_count": len(added) + len(removed) + len(revised_codes),
        "revised_code_count": len(revised_codes),
        "revised_fields": sorted(revised_fields),
        "added_codes": added,
        "removed_codes": removed,
        "material_revision": material,
        "previous_snapshot_hash": snapshot_content_hash(previous),
    }


def snapshot_content_hash(frame: pd.DataFrame) -> str:
    if frame.empty:
        return hashlib.sha256(b"").hexdigest()
    normalized = frame[list(SNAPSHOT_FIELDS)].sort_values("ts_code", kind="mergesort").copy()
    for field in SNAPSHOT_FIELDS[2:]:
        normalized[field] = normalized[field].map(lambda value: "" if pd.isna(value) else format(float(value), ".12g"))
    text = normalized.to_csv(index=False, lineterminator="\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def baostock_to_ts_code(value: str) -> str:
    text = str(value).strip().lower()
    match = re.fullmatch(r"(sh|sz)\.(\d{6})", text)
    return f"{match.group(2)}.{match.group(1).upper()}" if match else text.upper()


def values_equal(left: Any, right: Any) -> bool:
    if pd.isna(left) and pd.isna(right):
        return True
    try:
        return abs(float(left) - float(right)) <= 1e-12
    except (TypeError, ValueError):
        return str(left) == str(right)
