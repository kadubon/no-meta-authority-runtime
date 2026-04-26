"""Shared schema validation helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable

from no_meta_authority_runtime.canonical.errors import SchemaError
from no_meta_authority_runtime.canonical.hash import is_hash, is_ref
from no_meta_authority_runtime.canonical.json import MAX_REASON_BYTES, JsonValue

ASCII_RE = re.compile(r"^[\x20-\x7e]*$")


def require_fields(record: dict[str, JsonValue], fields: Iterable[str]) -> None:
    missing = [field for field in fields if field not in record]
    if missing:
        raise SchemaError(f"missing required fields: {', '.join(missing)}")


def reject_unknown_fields(record: dict[str, JsonValue], fields: Iterable[str]) -> None:
    allowed = set(fields)
    unknown = sorted(set(record) - allowed)
    if unknown:
        raise SchemaError(f"unknown authorizing fields: {', '.join(unknown)}")


def require_exact_fields(record: dict[str, JsonValue], fields: Iterable[str]) -> None:
    require_fields(record, fields)
    reject_unknown_fields(record, fields)


def require_str(value: JsonValue, field: str, *, nonempty: bool = False, ascii_only: bool = True) -> str:
    if not isinstance(value, str):
        raise SchemaError(f"{field} must be a string")
    if nonempty and value == "":
        raise SchemaError(f"{field} must be nonempty")
    if ascii_only and not ASCII_RE.fullmatch(value):
        raise SchemaError(f"{field} must be ASCII")
    return value


def require_reason(value: JsonValue, field: str = "reason") -> str:
    text = require_str(value, field, ascii_only=True)
    if len(text.encode("utf-8")) > MAX_REASON_BYTES:
        raise SchemaError(f"{field} exceeds reason byte bound")
    return text


def require_bool(value: JsonValue, field: str) -> bool:
    if not isinstance(value, bool):
        raise SchemaError(f"{field} must be a boolean")
    return value


def require_int(value: JsonValue, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SchemaError(f"{field} must be an integer")
    return value


def require_hash(value: JsonValue, field: str) -> str:
    if not is_hash(value):
        raise SchemaError(f"{field} must be a lowercase SHA-256 hex string")
    return str(value)


def require_ref(value: JsonValue, field: str) -> str:
    if not is_ref(value):
        raise SchemaError(f"{field} must be a SHA-256 reference or none")
    return str(value)


def require_enum(value: JsonValue, field: str, choices: frozenset[str]) -> str:
    text = require_str(value, field, nonempty=True, ascii_only=True)
    if text not in choices:
        raise SchemaError(f"{field} has invalid value: {text}")
    return text


def require_str_list(value: JsonValue, field: str, *, ascii_only: bool = True) -> list[str]:
    if not isinstance(value, list):
        raise SchemaError(f"{field} must be an array")
    out: list[str] = []
    for index, item in enumerate(value):
        out.append(require_str(item, f"{field}[{index}]", ascii_only=ascii_only))
    if len(set(out)) != len(out):
        raise SchemaError(f"{field} contains duplicates")
    return out


def require_ref_list(value: JsonValue, field: str) -> list[str]:
    if not isinstance(value, list):
        raise SchemaError(f"{field} must be an array")
    out: list[str] = []
    for index, item in enumerate(value):
        out.append(require_ref(item, f"{field}[{index}]"))
    if len(set(out)) != len(out):
        raise SchemaError(f"{field} contains duplicates")
    return out


def require_object(value: JsonValue, field: str) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise SchemaError(f"{field} must be an object")
    return value


def require_array(value: JsonValue, field: str) -> list[JsonValue]:
    if not isinstance(value, list):
        raise SchemaError(f"{field} must be an array")
    return value


def require_ascii_identifier(value: JsonValue, field: str, *, max_bytes: int = 128) -> str:
    text = require_str(value, field, nonempty=True, ascii_only=True)
    if len(text.encode("utf-8")) > max_bytes:
        raise SchemaError(f"{field} exceeds identifier byte bound")
    return text
