"""Ledger head records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from no_meta_authority_runtime.canonical.errors import LedgerError
from no_meta_authority_runtime.canonical.hash import GENESIS_HASH, is_hash
from no_meta_authority_runtime.canonical.json import JsonValue, canonical_bytes, parse_json


@dataclass(frozen=True)
class Head:
    seq: int
    hash: str
    path: str

    def to_json(self) -> dict[str, JsonValue]:
        return {"seq": self.seq, "hash": self.hash, "path": self.path}


GENESIS_HEAD = Head(seq=0, hash=GENESIS_HASH, path="genesis")


def read_head(root: Path) -> Head:
    path = root / "HEAD.json"
    if not path.exists():
        return GENESIS_HEAD
    data = parse_json(path.read_bytes())
    if not isinstance(data, dict):
        raise LedgerError("HEAD.json must contain an object")
    seq = data.get("seq")
    head_hash = data.get("hash")
    head_path = data.get("path")
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 0:
        raise LedgerError("HEAD seq is invalid")
    if not isinstance(head_hash, str) or not is_hash(head_hash):
        raise LedgerError("HEAD hash is invalid")
    if not isinstance(head_path, str) or not head_path:
        raise LedgerError("HEAD path is invalid")
    return Head(seq=seq, hash=head_hash, path=head_path)


def write_head_atomic(root: Path, head: Head) -> None:
    tmp = root / "HEAD.tmp"
    with tmp.open("wb") as handle:
        handle.write(canonical_bytes(head.to_json()))
        handle.flush()
        _fsync_file(handle.fileno())
    tmp.replace(root / "HEAD.json")
    sync_directory(root)


def _fsync_file(fd: int) -> None:
    try:
        import os

        os.fsync(fd)
    except OSError:
        return


def sync_directory(path: Path) -> None:
    try:
        import os

        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        return
