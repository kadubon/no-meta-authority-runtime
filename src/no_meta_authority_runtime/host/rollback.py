"""Rollback snapshot records for bounded local files."""

from __future__ import annotations

import base64
from pathlib import Path

from no_meta_authority_runtime.canonical.hash import attach_record_hash, content_hash, sha256_hex_bytes
from no_meta_authority_runtime.canonical.json import JsonValue, canonical_bytes, parse_json


def create_file_snapshot(path: str, rollback_root: str, tx_id: str) -> str:
    target = Path(path)
    root = Path(rollback_root)
    root.mkdir(parents=True, exist_ok=True)
    exists = target.exists()
    data = target.read_bytes() if exists and target.is_file() else b""
    record: dict[str, JsonValue] = {
        "schemaId": "no_meta_bootstrap_core",
        "txId": tx_id,
        "path": target.resolve(strict=False).as_posix(),
        "exists": exists,
        "fileType": "file" if exists else "missing",
        "byteLength": len(data),
        "sha256": sha256_hex_bytes(data),
        "contentEncoding": "base64",
        "content": base64.b64encode(data).decode("ascii"),
        "recordHash": "pending",
    }
    record = attach_record_hash(record)
    ref = f"{tx_id}-rollback-{record['recordHash']}.json"
    (root / ref).write_bytes(canonical_bytes(record))
    return ref


def restore_file_snapshot(rollback_root: str, rollback_ref: str) -> None:
    path = Path(rollback_root) / rollback_ref
    data = parse_json(path.read_bytes())
    if not isinstance(data, dict):
        raise ValueError("rollback record is not an object")
    target = Path(str(data["path"]))
    if data.get("exists") is True:
        content = base64.b64decode(str(data["content"]).encode("ascii"))
        if content_hash({"sha256": sha256_hex_bytes(content)}) == "":
            raise ValueError("unreachable")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    elif target.exists():
        target.unlink()
