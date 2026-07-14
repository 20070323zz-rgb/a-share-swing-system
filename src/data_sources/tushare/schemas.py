"""Interface schemas and unit contracts for the minimal Tushare proof."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InterfaceSchema:
    interface: str
    required_fields: tuple[str, ...]
    primary_key: tuple[str, ...]
    date_fields: tuple[str, ...]
    numeric_fields: tuple[str, ...]
    units: dict[str, str]
    pit_default: str
    expected_empty_allowed: bool = False


INTERFACE_SCHEMAS: dict[str, InterfaceSchema] = {
    "index_basic": InterfaceSchema(
        interface="index_basic",
        required_fields=("ts_code", "name", "market"),
        primary_key=("ts_code",),
        date_fields=("base_date", "list_date", "exp_date"),
        numeric_fields=("base_point",),
        units={"base_point": "index_points"},
        pit_default="PIT_UNRESOLVED",
    ),
    "index_daily": InterfaceSchema(
        interface="index_daily",
        required_fields=("ts_code", "trade_date", "close", "open", "high", "low"),
        primary_key=("ts_code", "trade_date"),
        date_fields=("trade_date",),
        numeric_fields=("close", "open", "high", "low", "pre_close", "change", "pct_chg", "vol", "amount"),
        units={"price": "index_points", "pct_chg": "percent", "vol": "lots_or_provider_units", "amount": "thousand_cny"},
        pit_default="PIT_CONSERVATIVE",
    ),
    "index_weight": InterfaceSchema(
        interface="index_weight",
        required_fields=("index_code", "con_code", "trade_date", "weight"),
        primary_key=("index_code", "con_code", "trade_date"),
        date_fields=("trade_date",),
        numeric_fields=("weight",),
        units={"weight": "percent"},
        pit_default="PIT_PARTIAL",
    ),
    "index_classify": InterfaceSchema(
        interface="index_classify",
        required_fields=("index_code", "industry_name", "level", "src"),
        primary_key=("index_code", "src"),
        date_fields=(),
        numeric_fields=(),
        units={},
        pit_default="PIT_UNRESOLVED",
    ),
    "index_member_all": InterfaceSchema(
        interface="index_member_all",
        required_fields=("l1_code", "l1_name", "ts_code", "in_date"),
        primary_key=("l1_code", "ts_code", "in_date"),
        date_fields=("in_date", "out_date"),
        numeric_fields=(),
        units={},
        pit_default="PIT_PARTIAL",
    ),
    "daily_basic": InterfaceSchema(
        interface="daily_basic",
        required_fields=("ts_code", "trade_date", "total_mv", "circ_mv"),
        primary_key=("ts_code", "trade_date"),
        date_fields=("trade_date",),
        numeric_fields=(
            "turnover_rate", "turnover_rate_f", "volume_ratio", "pe", "pe_ttm", "pb", "ps", "ps_ttm",
            "dv_ratio", "dv_ttm", "total_share", "float_share", "free_share", "total_mv", "circ_mv",
        ),
        units={
            "turnover_rate": "percent", "turnover_rate_f": "percent", "dv_ratio": "percent", "dv_ttm": "percent",
            "total_share": "ten_thousand_shares", "float_share": "ten_thousand_shares", "free_share": "ten_thousand_shares",
            "total_mv": "ten_thousand_cny", "circ_mv": "ten_thousand_cny",
        },
        pit_default="PIT_CONSERVATIVE",
    ),
    "fund_portfolio": InterfaceSchema(
        interface="fund_portfolio",
        required_fields=("ts_code", "ann_date", "end_date", "symbol", "mkv", "amount", "stk_mkv_ratio"),
        primary_key=("ts_code", "end_date", "ann_date", "symbol"),
        date_fields=("ann_date", "end_date"),
        numeric_fields=("mkv", "amount", "stk_mkv_ratio", "stk_float_ratio"),
        units={"mkv": "cny", "amount": "shares", "stk_mkv_ratio": "percent", "stk_float_ratio": "percent"},
        pit_default="PIT_RESOLVED",
        expected_empty_allowed=True,
    ),
    "shibor": InterfaceSchema(
        interface="shibor",
        required_fields=("date", "on", "1w", "2w", "1m", "3m", "6m", "9m", "1y"),
        primary_key=("date",),
        date_fields=("date",),
        numeric_fields=("on", "1w", "2w", "1m", "3m", "6m", "9m", "1y"),
        units={"on_to_1y": "percent_per_annum"},
        pit_default="PIT_CONSERVATIVE",
        expected_empty_allowed=True,
    ),
}


PIT_METADATA_FIELDS = (
    "source",
    "evidence_mode",
    "source_interface",
    "entity_id",
    "observation_date",
    "period_end",
    "announcement_date",
    "source_update_window",
    "official_release_time",
    "project_conservative_available_time",
    "conservative_lag_minutes",
    "retrieved_at",
    "available_at",
    "available_date",
    "pit_basis",
    "pit_confidence",
    "pit_status",
    "query_hash",
    "raw_payload_hash",
    "schema_version",
)
