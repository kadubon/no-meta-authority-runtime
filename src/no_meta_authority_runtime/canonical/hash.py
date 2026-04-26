"""SHA-256 commitments for canonical runtime records."""

from __future__ import annotations

import copy
import hashlib
import re

from no_meta_authority_runtime.canonical.errors import HashMismatchError
from no_meta_authority_runtime.canonical.json import JsonValue, canonical_bytes

GENESIS_HASH = "0" * 64
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
MISSING_REF = "none"


def sha256_hex_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(value: JsonValue) -> str:
    return sha256_hex_bytes(canonical_bytes(value))


def record_hash(record: dict[str, JsonValue]) -> str:
    """Hash a record with top-level recordHash replaced by the pending marker."""

    pending = copy.deepcopy(record)
    if "recordHash" in pending:
        pending["recordHash"] = "pending"
    return content_hash(pending)


def attach_record_hash(record: dict[str, JsonValue]) -> dict[str, JsonValue]:
    out = copy.deepcopy(record)
    out["recordHash"] = "pending"
    out["recordHash"] = record_hash(out)
    return out


def verify_record_hash(record: dict[str, JsonValue]) -> None:
    actual = record.get("recordHash")
    if not isinstance(actual, str) or not HASH_RE.fullmatch(actual):
        raise HashMismatchError("recordHash is missing or malformed")
    expected = record_hash(record)
    if actual != expected:
        raise HashMismatchError("recordHash does not match canonical record")


def is_hash(value: object) -> bool:
    return isinstance(value, str) and bool(HASH_RE.fullmatch(value))


def is_ref(value: object) -> bool:
    return value == MISSING_REF or is_hash(value)
