"""Literal deterministic selection checker."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import content_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.checkers.base import CheckerResult, allow, deny, halt


def check_deterministic_selection(candidates: list[JsonValue], selected: JsonValue) -> CheckerResult:
    if not candidates:
        return halt("emptySelectionSet")
    ordered = sorted(candidates, key=content_hash)
    expected = ordered[0]
    if selected != expected:
        return deny("selectionNotDeterministic", {"expectedHash": content_hash(expected)})
    return allow("literalSelectionOk", {"selectedHash": content_hash(selected)})
