"""Deterministic canonical JSON for runtime records."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any, TypeAlias

from no_meta_authority_runtime.canonical.errors import CanonicalError

JsonValue: TypeAlias = Any

MAX_RECORD_BYTES = 65_536
MAX_STRING_BYTES = 4_096
MAX_REASON_BYTES = 512
MAX_ARRAY_LENGTH = 256
MAX_TICK = 9_007_199_254_740_991


def _reject_duplicate_keys(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CanonicalError(f"duplicate object key: {key}")
        out[key] = value
    return out


def parse_json(data: str | bytes, *, max_bytes: int = MAX_RECORD_BYTES) -> JsonValue:
    """Parse JSON while rejecting duplicate keys and non-runtime values."""

    raw = data.encode("utf-8") if isinstance(data, str) else data
    if len(raw) > max_bytes:
        raise CanonicalError("record exceeds maximum byte length")
    try:
        parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except UnicodeDecodeError as exc:
        raise CanonicalError("input is not valid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise CanonicalError("malformed JSON") from exc
    _validate_json_value(parsed, "$")
    return parsed


def canonical_dumps(value: JsonValue) -> str:
    """Return canonical JSON text with sorted keys and compact separators."""

    _validate_json_value(value, "$")
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CanonicalError("value cannot be canonicalized") from exc


def canonical_bytes(value: JsonValue) -> bytes:
    """Return canonical UTF-8 bytes."""

    return canonical_dumps(value).encode("utf-8")


def assert_canonical_bytes(data: bytes) -> JsonValue:
    """Parse and require that the byte representation is already canonical."""

    parsed = parse_json(data)
    if canonical_bytes(parsed) != data:
        raise CanonicalError("JSON input is not canonical")
    return parsed


def sort_unique_array(values: list[JsonValue]) -> list[JsonValue]:
    """Sort set-like arrays by canonical element bytes and reject duplicates."""

    seen: set[bytes] = set()
    out: list[JsonValue] = []
    for item in sorted(values, key=canonical_bytes):
        key = canonical_bytes(item)
        if key in seen:
            raise CanonicalError("duplicate canonical array element")
        seen.add(key)
        out.append(item)
    return out


def _validate_json_value(value: Any, path: str) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if value < 0 or value > MAX_TICK:
            raise CanonicalError(f"integer out of bounds at {path}")
        return
    if isinstance(value, float):
        raise CanonicalError(f"floats are not permitted at {path}")
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_STRING_BYTES:
            raise CanonicalError(f"string exceeds byte bound at {path}")
        return
    if isinstance(value, list):
        if len(value) > MAX_ARRAY_LENGTH:
            raise CanonicalError(f"array exceeds length bound at {path}")
        for index, item in enumerate(value):
            _validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalError(f"non-string key at {path}")
            if len(key.encode("utf-8")) > MAX_STRING_BYTES:
                raise CanonicalError(f"key exceeds byte bound at {path}")
            _validate_json_value(item, f"{path}.{key}")
        return
    raise CanonicalError(f"unsupported JSON value at {path}")
