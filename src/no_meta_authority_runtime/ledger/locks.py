"""Portable best-effort lock files."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from no_meta_authority_runtime.canonical.errors import LedgerError


@contextmanager
def ledger_lock(root: Path) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".lock"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise LedgerError("ledger lock is already held") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        yield
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
