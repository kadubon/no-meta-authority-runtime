"""BootDecision schema."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import attach_record_hash, content_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.action import validate_action_descriptor
from no_meta_authority_runtime.schemas.base import (
    require_ascii_identifier,
    require_enum,
    require_exact_fields,
    require_hash,
    require_int,
    require_object,
    require_reason,
    require_ref_list,
    require_str,
)
from no_meta_authority_runtime.schemas.constants import ACTIVE_SCHEMA, BOOT_MODES

BOOT_DECISION_FIELDS = [
    "schemaId",
    "requestId",
    "seq",
    "prevHash",
    "scope",
    "mode",
    "permittedNextAction",
    "permittedActionHash",
    "forbiddenMatchers",
    "authorityState",
    "witnessNeed",
    "claimTarget",
    "taskEnvelopeRef",
    "evidenceRefs",
    "issuedAt",
    "expiresAt",
    "nonce",
    "reason",
    "recordHash",
]


def boot_decision(
    *,
    request_id: str,
    seq: int,
    prev_hash: str,
    scope: dict[str, JsonValue],
    mode: str,
    permitted_next_action: dict[str, JsonValue],
    forbidden_matchers: list[JsonValue],
    task_envelope_ref: str,
    issued_at: int,
    expires_at: int,
    nonce: str,
    authority_state: dict[str, JsonValue] | None = None,
    witness_need: dict[str, JsonValue] | None = None,
    claim_target: dict[str, JsonValue] | None = None,
    evidence_refs: list[str] | None = None,
    reason: str = "",
) -> dict[str, JsonValue]:
    validate_action_descriptor(permitted_next_action)
    record: dict[str, JsonValue] = {
        "schemaId": ACTIVE_SCHEMA,
        "requestId": request_id,
        "seq": seq,
        "prevHash": prev_hash,
        "scope": scope,
        "mode": mode,
        "permittedNextAction": permitted_next_action,
        "permittedActionHash": content_hash(permitted_next_action),
        "forbiddenMatchers": forbidden_matchers,
        "authorityState": authority_state or {},
        "witnessNeed": witness_need or {},
        "claimTarget": claim_target or {},
        "taskEnvelopeRef": task_envelope_ref,
        "evidenceRefs": evidence_refs or [],
        "issuedAt": issued_at,
        "expiresAt": expires_at,
        "nonce": nonce,
        "reason": reason,
        "recordHash": "pending",
    }
    out = attach_record_hash(record)
    validate_boot_decision(out, now=issued_at)
    return out


def validate_boot_decision(record: dict[str, JsonValue], *, now: int | None) -> None:
    require_exact_fields(record, BOOT_DECISION_FIELDS)
    if require_str(record["schemaId"], "schemaId", nonempty=True) != ACTIVE_SCHEMA:
        raise ValueError("unsupported schemaId")
    require_ascii_identifier(record["requestId"], "requestId")
    seq = require_int(record["seq"], "seq")
    if seq <= 0:
        raise ValueError("seq must be positive for decisions")
    require_hash(record["prevHash"], "prevHash")
    require_object(record["scope"], "scope")
    require_enum(record["mode"], "mode", BOOT_MODES)
    action = require_object(record["permittedNextAction"], "permittedNextAction")
    validate_action_descriptor(action)
    expected = content_hash(action)
    if require_hash(record["permittedActionHash"], "permittedActionHash") != expected:
        raise ValueError("permittedActionHash mismatch")
    if not isinstance(record["forbiddenMatchers"], list):
        raise ValueError("forbiddenMatchers must be an array")
    require_object(record["authorityState"], "authorityState")
    require_object(record["witnessNeed"], "witnessNeed")
    require_object(record["claimTarget"], "claimTarget")
    require_hash(record["taskEnvelopeRef"], "taskEnvelopeRef")
    require_ref_list(record["evidenceRefs"], "evidenceRefs")
    issued_at = require_int(record["issuedAt"], "issuedAt")
    expires_at = require_int(record["expiresAt"], "expiresAt")
    if expires_at < issued_at:
        raise ValueError("decision expires before issue")
    if now is not None and now > expires_at:
        raise ValueError("boot decision expired")
    require_ascii_identifier(record["nonce"], "nonce")
    require_reason(record["reason"], "reason")
    require_hash(record["recordHash"], "recordHash")
