"""Schema, key, unit and deterministic normalization validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .schemas import INTERFACE_SCHEMAS, InterfaceSchema


@dataclass
class ValidationResult:
    interface: str
    status: str
    normalized: pd.DataFrame
    missing_fields: list[str]
    duplicate_keys: int
    null_rates: dict[str, float]
    dtypes: dict[str, str]
    date_min: str
    date_max: str
    units: dict[str, str]
    validation_errors: list[str]
    validation_warnings: list[str]
    version_count: int = 0

    def to_summary(self) -> dict[str, Any]:
        return {
            "interface": self.interface,
            "status": self.status,
            "row_count": int(len(self.normalized)),
            "columns": list(self.normalized.columns),
            "dtypes": self.dtypes,
            "null_rates": self.null_rates,
            "duplicate_keys": self.duplicate_keys,
            "date_min": self.date_min,
            "date_max": self.date_max,
            "units": self.units,
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
            "version_count": self.version_count,
        }


def validate_interface_frame(interface: str, frame: pd.DataFrame) -> ValidationResult:
    if interface not in INTERFACE_SCHEMAS:
        raise KeyError(f"unknown interface schema: {interface}")
    schema = INTERFACE_SCHEMAS[interface]
    missing_fields = sorted(set(schema.required_fields) - set(frame.columns))
    if missing_fields:
        return _result(interface, "SCHEMA_MISMATCH", frame.copy(), schema, missing_fields, [f"missing required fields: {', '.join(missing_fields)}"])
    if frame.empty:
        status = "EMPTY_EXPECTED" if schema.expected_empty_allowed else "EMPTY_UNEXPECTED"
        return _result(interface, status, frame.copy(), schema, [], [])

    normalized = normalize_frame(frame, schema)
    duplicate_keys = int(normalized.duplicated(list(schema.primary_key), keep=False).sum()) if schema.primary_key else 0
    errors: list[str] = []
    warnings: list[str] = []
    if duplicate_keys:
        errors.append(f"duplicate primary-key rows: {duplicate_keys}")
    errors.extend(_unit_errors(interface, normalized))
    warnings.extend(_semantic_warnings(interface, normalized))
    status = "VALIDATION_FAILED" if errors else "ACCESS_PASS"
    result = _result(interface, status, normalized, schema, [], errors, warnings, duplicate_keys=duplicate_keys)
    if interface == "fund_portfolio":
        result.version_count = int(normalized[["ts_code", "end_date", "ann_date"]].drop_duplicates().shape[0])
    return result


def normalize_frame(frame: pd.DataFrame, schema: InterfaceSchema) -> pd.DataFrame:
    normalized = frame.copy()
    for field in schema.date_fields:
        if field in normalized.columns:
            parsed = pd.to_datetime(normalized[field].astype(str).str.strip(), errors="coerce")
            normalized[field] = parsed.dt.strftime("%Y-%m-%d").fillna("")
    for field in schema.numeric_fields:
        if field in normalized.columns:
            normalized[field] = pd.to_numeric(normalized[field], errors="coerce")
    sort_fields = [field for field in schema.primary_key if field in normalized.columns]
    remaining = sorted(field for field in normalized.columns if field not in sort_fields)
    normalized = normalized[sort_fields + remaining]
    if sort_fields:
        normalized = normalized.sort_values(sort_fields, kind="mergesort", na_position="last")
    return normalized.reset_index(drop=True)


def _result(
    interface: str,
    status: str,
    normalized: pd.DataFrame,
    schema: InterfaceSchema,
    missing_fields: list[str],
    errors: list[str],
    warnings: list[str] | None = None,
    *,
    duplicate_keys: int = 0,
) -> ValidationResult:
    warnings = warnings or []
    null_rates = {column: round(float(normalized[column].isna().mean()), 6) for column in normalized.columns}
    dtypes = {column: str(dtype) for column, dtype in normalized.dtypes.items()}
    date_values: list[str] = []
    for field in schema.date_fields:
        if field in normalized.columns:
            date_values.extend(value for value in normalized[field].dropna().astype(str) if value)
    return ValidationResult(
        interface=interface,
        status=status,
        normalized=normalized,
        missing_fields=missing_fields,
        duplicate_keys=duplicate_keys,
        null_rates=null_rates,
        dtypes=dtypes,
        date_min=min(date_values) if date_values else "",
        date_max=max(date_values) if date_values else "",
        units=schema.units,
        validation_errors=errors,
        validation_warnings=warnings,
    )


def _unit_errors(interface: str, frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if interface == "index_weight" and "weight" in frame:
        invalid = frame["weight"].notna() & ~frame["weight"].between(0, 100)
        if invalid.any():
            errors.append(f"weight outside [0,100]: {int(invalid.sum())}")
    if interface == "daily_basic":
        for field in ("total_share", "float_share", "free_share", "total_mv", "circ_mv"):
            if field in frame:
                invalid = frame[field].notna() & (frame[field] < 0)
                if invalid.any():
                    errors.append(f"{field} contains negative values: {int(invalid.sum())}")
    if interface == "fund_portfolio":
        for field in ("stk_mkv_ratio", "stk_float_ratio"):
            if field in frame:
                invalid = frame[field].notna() & ~frame[field].between(0, 100)
                if invalid.any():
                    errors.append(f"{field} outside [0,100]: {int(invalid.sum())}")
        invalid_dates = (frame["ann_date"] != "") & (frame["end_date"] != "") & (frame["ann_date"] < frame["end_date"])
        if invalid_dates.any():
            errors.append(f"announcement date earlier than period end: {int(invalid_dates.sum())}")
    if interface == "shibor":
        rate_fields = [field for field in ("on", "1w", "2w", "1m", "3m", "6m", "9m", "1y") if field in frame]
        for field in rate_fields:
            invalid = frame[field].notna() & ~frame[field].between(-5, 100)
            if invalid.any():
                errors.append(f"{field} outside plausible percent range: {int(invalid.sum())}")
    if interface == "index_daily":
        for field in ("close", "open", "high", "low"):
            if field in frame:
                invalid = frame[field].notna() & (frame[field] <= 0)
                if invalid.any():
                    errors.append(f"{field} contains non-positive values: {int(invalid.sum())}")
    return errors


def _semantic_warnings(interface: str, frame: pd.DataFrame) -> list[str]:
    warnings: list[str] = []
    if interface == "index_weight" and not frame.empty:
        sums = frame.groupby(["index_code", "trade_date"], dropna=False)["weight"].sum(min_count=1)
        off = sums[(sums < 95) | (sums > 105)]
        if not off.empty:
            warnings.append(f"weight sum outside [95,105] for {len(off)} snapshots")
    if interface == "daily_basic" and "pe" in frame:
        negative_pe = int((frame["pe"].notna() & (frame["pe"] < 0)).sum())
        if negative_pe:
            warnings.append(f"negative PE retained as economically meaningful: {negative_pe}")
    if interface == "fund_portfolio" and not frame.empty:
        versions = frame[["ts_code", "end_date", "ann_date"]].drop_duplicates().groupby(["ts_code", "end_date"]).size()
        revised = int((versions > 1).sum())
        if revised:
            warnings.append(f"periods with multiple announcement versions retained: {revised}")
    return warnings
