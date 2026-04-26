from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import attach_record_hash, record_hash, verify_record_hash


def test_record_hash_uses_pending_marker() -> None:
    record = attach_record_hash({"schemaId": "x", "recordHash": "pending"})
    assert record["recordHash"] == record_hash({"schemaId": "x", "recordHash": "different"})
    verify_record_hash(record)
