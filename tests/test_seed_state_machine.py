from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from no_meta_authority_runtime.canonical.hash import GENESIS_HASH
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.seed.interpreter import SeedInterpreter


def test_seed_issue_dispatch_consumes_safe_inventory(
    tmp_path: Path,
    make_env: Callable[[Path], dict[str, JsonValue]],
    make_action: Callable[..., dict[str, JsonValue]],
    make_decision: Callable[..., dict[str, JsonValue]],
) -> None:
    env = make_env(tmp_path)
    action = make_action(env)
    decision = make_decision(env, action)
    seed = SeedInterpreter(tmp_path / "ledger")
    issued = seed.issue(decision)
    dispatched = seed.dispatch(str(issued["bootDecisionHash"]), action, env)
    assert issued["outcome"] == "consumed"
    assert dispatched["outcome"] == "consumed"
    assert dispatched["dispatchRecordHash"] != "none"
    assert dispatched["consumptionRecordHash"] != "none"


def test_second_open_decision_halts(
    tmp_path: Path,
    make_env: Callable[[Path], dict[str, JsonValue]],
    make_action: Callable[..., dict[str, JsonValue]],
    make_decision: Callable[..., dict[str, JsonValue]],
) -> None:
    env = make_env(tmp_path)
    action = make_action(env)
    seed = SeedInterpreter(tmp_path / "ledger")
    first = make_decision(env, action)
    assert seed.issue(first)["outcome"] == "consumed"
    second = make_decision(env, action, seq=2)
    result = seed.issue(second)
    assert result["outcome"] == "halt"
    assert result["reasonCode"] == "openDecision"


def test_dispatch_without_issue_denied(tmp_path: Path) -> None:
    seed = SeedInterpreter(tmp_path / "ledger")
    result = seed.dispatch(GENESIS_HASH, {}, {}, now=0)
    assert result["outcome"] == "deny"
