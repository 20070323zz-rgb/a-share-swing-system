"""Fail-closed deep merge for shared Reports/Availability authority state."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


class AuthorityMergeError(ValueError):
    """Base class for deterministic authority merge failures."""


class AuthorityConflictError(AuthorityMergeError):
    pass


class AuthorityTypeConflictError(AuthorityMergeError):
    pass


@dataclass(frozen=True)
class AuthorityRule:
    path: tuple[str, ...]
    owner: str


def _owner_for(path: tuple[str, ...], rules: tuple[AuthorityRule, ...]) -> str | None:
    matches = [rule for rule in rules if path[: len(rule.path)] == rule.path]
    if not matches:
        return None
    return max(matches, key=lambda rule: len(rule.path)).owner


def deep_merge_authority(
    base: Mapping[str, Any],
    incoming: Mapping[str, Any],
    *,
    base_owner: str,
    incoming_owner: str,
    rules: tuple[AuthorityRule, ...],
    path: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Deep merge without deleting unknown keys or silently resolving conflicts.

    Unknown keys present on either side are preserved. Scalar conflicts require
    an explicit longest-prefix authority rule. Type conflicts always fail.
    """

    result: dict[str, Any] = deepcopy(dict(base))
    for key, incoming_value in incoming.items():
        child_path = (*path, key)
        if key not in result:
            result[key] = deepcopy(incoming_value)
            continue
        base_value = result[key]
        if isinstance(base_value, Mapping) and isinstance(incoming_value, Mapping):
            result[key] = deep_merge_authority(
                base_value,
                incoming_value,
                base_owner=base_owner,
                incoming_owner=incoming_owner,
                rules=rules,
                path=child_path,
            )
            continue
        if isinstance(base_value, Mapping) != isinstance(incoming_value, Mapping) or (
            isinstance(base_value, list) != isinstance(incoming_value, list)
        ):
            raise AuthorityTypeConflictError(
                f"type conflict at {'.'.join(child_path)}: "
                f"{type(base_value).__name__} vs {type(incoming_value).__name__}"
            )
        if base_value == incoming_value:
            continue
        owner = _owner_for(child_path, rules)
        if owner == incoming_owner:
            result[key] = deepcopy(incoming_value)
        elif owner == base_owner:
            continue
        else:
            raise AuthorityConflictError(
                f"unowned conflict at {'.'.join(child_path)}: "
                f"{base_owner} vs {incoming_owner}"
            )
    return result


REPORTS_AUTHORITY_PREFIXES = (
    "reports_governance_",
    "report_catalog_",
    "report_dependency_",
    "report_classification_",
    "report_producer_",
    "report_dynamic_",
    "report_archive_",
    "report_naming_",
    "report_metadata_",
    "report_path_registry_",
    "report_file_migration_",
    "report_migration_",
)

AVAILABILITY_AUTHORITY_PREFIXES = (
    "etf_daily_availability_",
    "availability_temporary_",
    "draft_pr_3_",
    "tushare_data_source_role",
    "baostock_data_source_role",
    "canonical_etf_data_source",
    "data_promotion_status",
)


def authority_rules_for_states(*states: Mapping[str, Any]) -> tuple[AuthorityRule, ...]:
    rules: list[AuthorityRule] = []
    for state in states:
        for key in state:
            if key.startswith(REPORTS_AUTHORITY_PREFIXES):
                rules.append(AuthorityRule((key,), "reports_governance"))
            if key.startswith(AVAILABILITY_AUTHORITY_PREFIXES):
                rules.append(AuthorityRule((key,), "availability_audit"))
    rules.extend(
        (
            AuthorityRule(
                ("phase_deliverables", "tushare_etf_daily_availability_timing_audit"),
                "availability_audit",
            ),
            AuthorityRule(("main_phase",), "availability_audit"),
            AuthorityRule(("main_phase_id",), "availability_audit"),
            AuthorityRule(("phase_status",), "availability_audit"),
            AuthorityRule(("phase_started_at",), "availability_audit"),
            AuthorityRule(("phase_completed_at",), "availability_audit"),
            AuthorityRule(("current_batch",), "availability_audit"),
            AuthorityRule(("current_batch_id",), "availability_audit"),
            AuthorityRule(("current_batch_status",), "availability_audit"),
            AuthorityRule(("resume_from",), "availability_audit"),
            AuthorityRule(("required_batches",), "availability_audit"),
            AuthorityRule(("final_closeout_batch",), "availability_audit"),
            AuthorityRule(("next_research_phase",), "availability_audit"),
            AuthorityRule(("current_phase_report",), "availability_audit"),
            AuthorityRule(("current_phase_decision",), "availability_audit"),
            AuthorityRule(("context_updated_at",), "availability_audit"),
            AuthorityRule(("context_updated_by",), "availability_audit"),
            AuthorityRule(("context_update_reason",), "availability_audit"),
        )
    )
    return tuple(dict.fromkeys(rules))
