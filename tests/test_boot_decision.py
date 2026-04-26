from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.boot_decision import validate_boot_decision


def test_boot_decision_commits_single_action(
    tmp_path: Path,
    make_env: Callable[[Path], dict[str, JsonValue]],
    make_action: Callable[..., dict[str, JsonValue]],
    make_decision: Callable[..., dict[str, JsonValue]],
) -> None:
    env = make_env(tmp_path)
    action = make_action(env)
    decision = make_decision(env, action)
    assert decision["permittedActionHash"]
    validate_boot_decision(decision, now=0)
