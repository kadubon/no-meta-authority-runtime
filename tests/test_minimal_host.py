from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.host.minimal_host import MinimalHost


def test_minimal_host_reversible_local_write(
    tmp_path: Path,
    make_env: Callable[[Path], dict[str, JsonValue]],
) -> None:
    env = make_env(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "note.txt"
    host = MinimalHost(tmp_path / "host", env)
    assert host.boot()["outcome"] == "consumed"
    operation = {"kind": "writeText", "path": target.as_posix(), "content": "hello"}
    prepared = host.prepare(operation)
    checked = host.check(str(prepared["txId"]), operation)
    committed = host.commit(str(prepared["txId"]), operation)
    assert checked["outcome"] == "consumed"
    assert committed["outcome"] == "consumed"
    assert target.read_text(encoding="utf-8") == "hello"


def test_minimal_host_boot_requires_declared_host_root(tmp_path: Path) -> None:
    host_root = tmp_path / "host"
    host = MinimalHost(host_root, {})
    result = host.boot()
    assert result["outcome"] == "halt"
    assert not host_root.exists()


def test_minimal_host_operation_write_must_use_declared_write_root(
    tmp_path: Path,
    make_env: Callable[[Path], dict[str, JsonValue]],
) -> None:
    env = make_env(tmp_path)
    host = MinimalHost(tmp_path / "host", env)
    assert host.boot()["outcome"] == "consumed"
    operation = {
        "kind": "writeText",
        "path": (tmp_path / "scratch" / "not-workspace.txt").as_posix(),
        "content": "blocked",
    }
    result = host.prepare(operation)
    assert result["outcome"] == "halt"
    assert result["reason"] == "pathOutsideEnvelope"
