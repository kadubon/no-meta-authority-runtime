"""Micro predicate facade used by host and gate code."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.checkers.base import CheckerResult, allow, deny, halt, timeout
from no_meta_authority_runtime.checkers.deterministic_selection import check_deterministic_selection
from no_meta_authority_runtime.checkers.no_external_effect import check_no_external_effect
from no_meta_authority_runtime.checkers.path_allowed import check_path_allowed
from no_meta_authority_runtime.checkers.privacy_table import check_privacy_table
from no_meta_authority_runtime.checkers.rollback_ready import check_rollback_ready


def path_allowed(path: str, allowed_roots: list[str], denied_roots: list[str]) -> CheckerResult:
    return check_path_allowed(path, allowed_roots, denied_roots)


def no_external_effect(effect_tags: list[str]) -> CheckerResult:
    return check_no_external_effect(effect_tags)


def rollback_ready(rollback_ref: str, rollback_root: str) -> CheckerResult:
    return check_rollback_ready(rollback_ref, rollback_root)


def privacy_table_ok(field: str, privacy_table: list[JsonValue], requested_form: str) -> CheckerResult:
    return check_privacy_table(field, privacy_table, requested_form)


def selection_deterministic(candidates: list[JsonValue], selected: JsonValue) -> CheckerResult:
    return check_deterministic_selection(candidates, selected)


def within_budget(elapsed: int, timeout_budget: int) -> CheckerResult:
    if elapsed > timeout_budget:
        return timeout("timeoutBudgetExceeded", {"elapsed": elapsed, "timeoutBudget": timeout_budget})
    return allow("withinBudget", {"elapsed": elapsed, "timeoutBudget": timeout_budget})


def checker_totality(outcomes: list[str]) -> CheckerResult:
    if not outcomes:
        return halt("checkerNoResult")
    if any(outcome not in {"allow", "deny", "defer", "halt", "timeout"} for outcome in outcomes):
        return halt("checkerInvalidOutcome")
    if "halt" in outcomes:
        return halt("checkerHalt")
    if "timeout" in outcomes:
        return timeout("checkerTimeout")
    if "deny" in outcomes:
        return deny("checkerDeny")
    return allow("checkerTotal")
