"""Raw input commitments."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import sha256_hex_bytes
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.constants import RAW_SCHEMA


def raw_input_commitment(data: bytes, media_type: str = "application/octet-stream") -> dict[str, JsonValue]:
    return {
        "schemaId": RAW_SCHEMA,
        "mediaType": media_type,
        "length": len(data),
        "sha256": sha256_hex_bytes(data),
    }
