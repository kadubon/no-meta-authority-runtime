"""Host digest helpers."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.ledger.head import Head


def digest_record(head: Head) -> dict[str, JsonValue]:
    return {"headSeq": head.seq, "headHash": head.hash, "path": head.path}
