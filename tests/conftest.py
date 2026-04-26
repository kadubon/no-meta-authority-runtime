from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from no_meta_authority_runtime.canonical.hash import GENESIS_HASH, content_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.matchers.default_matchers import default_matchers
from no_meta_authority_runtime.schemas.action import action_descriptor
from no_meta_authority_runtime.schemas.boot_decision import boot_decision
from no_meta_authority_runtime.schemas.task_envelope import empty_task_envelope


def _make_env(tmp_path: Path) -> dict[str, JsonValue]:
    env = empty_task_envelope(b"migrate authority", expires_at=100)
    env["rootContractRef"] = "1" * 64
    env["boundaryFloorRef"] = "2" * 64
    env["grantedScratchRoot"] = (tmp_path / "scratch").as_posix()
    env["grantedHostRoot"] = (tmp_path / "host").as_posix()
    env["grantedWriteRoots"] = [(tmp_path / "workspace").as_posix()]
    env["allowedTools"] = ["referenceSeedCLI", "gate"]
    return env


def _make_action(env: dict[str, JsonValue], **overrides: object) -> dict[str, JsonValue]:
    kwargs = {
        "kind": "safeInventory",
        "scope": {"resource": "scratch"},
        "task_envelope_ref": str(env["recordHash"]),
        "args_hash": content_hash({"request": "migrate authority"}),
        "nonce": "a",
    }
    kwargs.update(overrides)
    return action_descriptor(**kwargs)  # type: ignore[arg-type]


def _make_decision(env: dict[str, JsonValue], action: dict[str, JsonValue], seq: int = 1) -> dict[str, JsonValue]:
    prev_hash = GENESIS_HASH if seq == 1 else "f" * 64
    return boot_decision(
        request_id="r1",
        seq=seq,
        prev_hash=prev_hash,
        scope={"resource": "scratch"},
        mode="diagnoseOnly",
        permitted_next_action=action,
        forbidden_matchers=default_matchers(env),
        task_envelope_ref=str(env["recordHash"]),
        issued_at=0,
        expires_at=100,
        nonce="b",
    )


@pytest.fixture
def make_env() -> Callable[[Path], dict[str, JsonValue]]:
    return _make_env


@pytest.fixture
def make_action() -> Callable[..., dict[str, JsonValue]]:
    return _make_action


@pytest.fixture
def make_decision() -> Callable[..., dict[str, JsonValue]]:
    return _make_decision
