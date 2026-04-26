from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.matchers.default_matchers import default_matchers
from no_meta_authority_runtime.matchers.forbidden import evaluate_forbidden_matchers


def test_network_denied(
    tmp_path: Path,
    make_env: Callable[[Path], dict[str, JsonValue]],
    make_action: Callable[..., dict[str, JsonValue]],
) -> None:
    env = make_env(tmp_path)
    action = make_action(env, needs_network=True)
    decision = evaluate_forbidden_matchers(default_matchers(env), action)
    assert decision is not None
    assert decision.outcome == "deny"
    assert decision.reason_code == "networkDenied"


def test_write_outside_halts(
    tmp_path: Path,
    make_env: Callable[[Path], dict[str, JsonValue]],
    make_action: Callable[..., dict[str, JsonValue]],
) -> None:
    env = make_env(tmp_path)
    action = make_action(env, write_set=[(tmp_path / "other" / "x.txt").as_posix()])
    decision = evaluate_forbidden_matchers(default_matchers(env), action)
    assert decision is not None
    assert decision.outcome == "halt"
    assert decision.reason_code == "writeOutsideEnvelope"
