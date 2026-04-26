"""Provisioning state records."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import attach_record_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.base import (
    require_enum,
    require_exact_fields,
    require_hash,
    require_object,
    require_str,
    require_str_list,
)
from no_meta_authority_runtime.schemas.constants import ACTIVE_SCHEMA

PROVISIONING_STATES = frozenset(
    {"uninspected", "requestOnly", "scratchOnly", "localInstallable", "hosted", "blocked"}
)

PROVISIONING_FIELDS = [
    "schemaId",
    "id",
    "scope",
    "state",
    "existingRights",
    "missingPrimitives",
    "localInstallPlan",
    "installerAuthority",
    "witnessNeed",
    "outcome",
    "recordHash",
]


def provisioning_record(
    *,
    record_id: str,
    scope: dict[str, JsonValue],
    state: str,
    missing_primitives: list[str] | None = None,
    outcome: str = "hostRequest",
) -> dict[str, JsonValue]:
    record: dict[str, JsonValue] = {
        "schemaId": ACTIVE_SCHEMA,
        "id": record_id,
        "scope": scope,
        "state": state,
        "existingRights": [],
        "missingPrimitives": missing_primitives or [],
        "localInstallPlan": {},
        "installerAuthority": {},
        "witnessNeed": {},
        "outcome": outcome,
        "recordHash": "pending",
    }
    out = attach_record_hash(record)
    validate_provisioning_record(out)
    return out


def validate_provisioning_record(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, PROVISIONING_FIELDS)
    if require_str(record["schemaId"], "schemaId", nonempty=True) != ACTIVE_SCHEMA:
        raise ValueError("unsupported schemaId")
    require_str(record["id"], "id", nonempty=True)
    require_object(record["scope"], "scope")
    require_enum(record["state"], "state", PROVISIONING_STATES)
    if not isinstance(record["existingRights"], list):
        raise ValueError("existingRights must be an array")
    require_str_list(record["missingPrimitives"], "missingPrimitives")
    require_object(record["localInstallPlan"], "localInstallPlan")
    require_object(record["installerAuthority"], "installerAuthority")
    require_object(record["witnessNeed"], "witnessNeed")
    require_str(record["outcome"], "outcome", nonempty=True)
    require_hash(record["recordHash"], "recordHash")
