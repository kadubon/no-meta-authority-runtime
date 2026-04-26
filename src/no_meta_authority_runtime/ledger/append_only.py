"""Durable append-only canonical JSON ledger."""

from __future__ import annotations

import tempfile
from pathlib import Path

from no_meta_authority_runtime.canonical.hash import attach_record_hash
from no_meta_authority_runtime.canonical.json import JsonValue, canonical_bytes
from no_meta_authority_runtime.ledger.head import Head, read_head, sync_directory, write_head_atomic
from no_meta_authority_runtime.ledger.locks import ledger_lock


class AppendOnlyLedger:
    """One-record-per-file append-only ledger with a chained HEAD."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def head(self) -> Head:
        return read_head(self.root)

    def append(self, record: dict[str, JsonValue]) -> dict[str, JsonValue]:
        with ledger_lock(self.root):
            return self._append_unlocked(record)

    def append_recovery(self, record: dict[str, JsonValue]) -> dict[str, JsonValue]:
        with ledger_lock(self.root):
            return self._append_unlocked(record)

    def records(self) -> list[dict[str, JsonValue]]:
        from no_meta_authority_runtime.ledger.recovery import read_record_files

        return [item.record for item in read_record_files(self.root)]

    def _append_unlocked(self, record: dict[str, JsonValue]) -> dict[str, JsonValue]:
        self.root.mkdir(parents=True, exist_ok=True)
        head = read_head(self.root)
        candidate = dict(record)
        candidate["seq"] = head.seq + 1
        candidate["prevHash"] = head.hash
        candidate = attach_record_hash(candidate)
        final_name = self._record_name(candidate)
        final = self.root / final_name
        fd, tmp_name = tempfile.mkstemp(prefix="tmp-", suffix=".json", dir=self.root)
        tmp = Path(tmp_name)
        try:
            with open(fd, "wb", closefd=True) as handle:
                handle.write(canonical_bytes(candidate))
                handle.flush()
                try:
                    import os

                    os.fsync(handle.fileno())
                except OSError:
                    pass
            tmp.replace(final)
            write_head_atomic(
                self.root,
                Head(seq=int(candidate["seq"]), hash=str(candidate["recordHash"]), path=final_name),
            )
            sync_directory(self.root)
            return candidate
        finally:
            if tmp.exists():
                tmp.unlink()

    @staticmethod
    def _record_name(record: dict[str, JsonValue]) -> str:
        seq = int(record["seq"])
        phase = str(record.get("phase", "record"))
        digest = str(record["recordHash"])
        tx = record.get("txId")
        if isinstance(tx, str) and tx:
            return f"{seq:06d}-{tx}-{phase}-{digest}.json"
        return f"{seq:06d}-{phase}-{digest}.json"
