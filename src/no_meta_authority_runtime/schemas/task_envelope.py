"""Task envelope and root contract schemas."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import attach_record_hash, content_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.base import (
    require_enum,
    require_exact_fields,
    require_hash,
    require_int,
    require_object,
    require_ref,
    require_str,
    require_str_list,
)
from no_meta_authority_runtime.schemas.constants import ACTIVE_SCHEMA, POLICIES
from no_meta_authority_runtime.schemas.raw import raw_input_commitment

TASK_ENVELOPE_FIELDS = [
    "schemaId",
    "taskId",
    "userRequestHash",
    "scope",
    "rootContractRef",
    "boundaryFloorRef",
    "grantedReadMetadata",
    "grantedScratchRoot",
    "grantedHostRoot",
    "grantedWriteRoots",
    "deniedRoots",
    "allowedTools",
    "networkPolicy",
    "credentialPolicy",
    "publicOutputPolicy",
    "createdAt",
    "expiresAt",
    "recordHash",
]

ROOT_CONTRACT_FIELDS = [
    "schemaId",
    "contractId",
    "requestChannel",
    "protectedClasses",
    "deniedActions",
    "seedTool",
    "seedArtifactHash",
    "privacyTable",
    "hostRoots",
    "revocationPath",
    "boundaryFloor",
    "createdAt",
    "expiresAt",
    "recordHash",
]


def empty_task_envelope(
    request_bytes: bytes,
    *,
    task_id: str = "empty",
    created_at: int = 0,
    expires_at: int = 1,
) -> dict[str, JsonValue]:
    raw = raw_input_commitment(request_bytes, "text/plain; charset=utf-8")
    record: dict[str, JsonValue] = {
        "schemaId": ACTIVE_SCHEMA,
        "taskId": task_id,
        "userRequestHash": content_hash(raw),
        "scope": {"resource": "unknown"},
        "rootContractRef": "none",
        "boundaryFloorRef": "none",
        "grantedReadMetadata": [],
        "grantedScratchRoot": "",
        "grantedHostRoot": "",
        "grantedWriteRoots": [],
        "deniedRoots": [],
        "allowedTools": [],
        "networkPolicy": "deny",
        "credentialPolicy": "deny",
        "publicOutputPolicy": "deny",
        "createdAt": created_at,
        "expiresAt": expires_at,
        "recordHash": "pending",
    }
    out = attach_record_hash(record)
    validate_task_envelope(out, now=created_at)
    return out


def task_envelope_hash(record: dict[str, JsonValue]) -> str:
    validate_task_envelope(record, now=None)
    return content_hash(record)


def validate_task_envelope(record: dict[str, JsonValue], *, now: int | None) -> None:
    require_exact_fields(record, TASK_ENVELOPE_FIELDS)
    require_str(record["schemaId"], "schemaId", nonempty=True, ascii_only=True)
    if record["schemaId"] != ACTIVE_SCHEMA:
        raise ValueError("unsupported schemaId")
    require_str(record["taskId"], "taskId", nonempty=True, ascii_only=True)
    require_hash(record["userRequestHash"], "userRequestHash")
    require_object(record["scope"], "scope")
    require_ref(record["rootContractRef"], "rootContractRef")
    require_ref(record["boundaryFloorRef"], "boundaryFloorRef")
    require_str_list(record["grantedReadMetadata"], "grantedReadMetadata")
    require_str(record["grantedScratchRoot"], "grantedScratchRoot", ascii_only=True)
    require_str(record["grantedHostRoot"], "grantedHostRoot", ascii_only=True)
    require_str_list(record["grantedWriteRoots"], "grantedWriteRoots")
    require_str_list(record["deniedRoots"], "deniedRoots")
    require_str_list(record["allowedTools"], "allowedTools")
    require_enum(record["networkPolicy"], "networkPolicy", POLICIES)
    require_enum(record["credentialPolicy"], "credentialPolicy", POLICIES)
    require_enum(record["publicOutputPolicy"], "publicOutputPolicy", POLICIES)
    created_at = require_int(record["createdAt"], "createdAt")
    expires_at = require_int(record["expiresAt"], "expiresAt")
    require_hash(record["recordHash"], "recordHash")
    if expires_at < created_at:
        raise ValueError("expiresAt is before createdAt")
    if now is not None and now > expires_at:
        raise ValueError("task envelope expired")


def root_contract(
    *,
    contract_id: str,
    boundary_floor: dict[str, JsonValue],
    created_at: int = 0,
    expires_at: int = 100,
    request_channel: str = "local",
) -> dict[str, JsonValue]:
    record: dict[str, JsonValue] = {
        "schemaId": ACTIVE_SCHEMA,
        "contractId": contract_id,
        "requestChannel": request_channel,
        "protectedClasses": [],
        "deniedActions": [],
        "seedTool": "referenceSeedCLI",
        "seedArtifactHash": "none",
        "privacyTable": [],
        "hostRoots": [],
        "revocationPath": "none",
        "boundaryFloor": boundary_floor,
        "createdAt": created_at,
        "expiresAt": expires_at,
        "recordHash": "pending",
    }
    return attach_record_hash(record)
