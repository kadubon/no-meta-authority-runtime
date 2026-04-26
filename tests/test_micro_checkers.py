from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import content_hash
from no_meta_authority_runtime.checkers.micro_predicates import (
    no_external_effect,
    selection_deterministic,
    within_budget,
)


def test_external_effect_denied() -> None:
    assert no_external_effect(["externalWrite"]).outcome == "deny"
    assert no_external_effect(["unknown"]).outcome == "halt"


def test_literal_selection_deterministic() -> None:
    candidates = [{"id": "b"}, {"id": "a"}]
    selected = sorted(candidates, key=content_hash)[0]
    result = selection_deterministic(candidates, selected)
    assert result.outcome == "allow"


def test_timeout_budget() -> None:
    assert within_budget(2, 1).outcome == "timeout"
