"""Unified outcome records."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import attach_record_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.base import (
    require_bool,
    require_enum,
    require_exact_fields,
    require_hash,
    require_reason,
    require_ref,
    require_str,
    require_str_list,
)
from no_meta_authority_runtime.schemas.constants import ACTIVE_SCHEMA, RISK_CLASSES, TRANSITION_OUTCOMES

OUTCOME_FIELDS = [
    "schemaId",
    "outcome",
    "taskEnvelopeRef",
    "bootDecisionHash",
    "cardRef",
    "certRef",
    "missingPrimitives",
    "requestedRoots",
    "requestedTools",
    "riskClass",
    "safeFallback",
    "privacyLimit",
    "nonAuthorization",
    "reason",
    "recordHash",
]

NON_AUTHORIZING_OUTCOMES = frozenset(
    {
        "hostRequest",
        "strongerTierRequest",
        "defer",
        "deny",
        "timeout",
        "halt",
        "provisionalClaim",
        "partialClaim",
    }
)


def computed_non_authorization(outcome: str, fields: dict[str, JsonValue]) -> bool:
    if outcome in NON_AUTHORIZING_OUTCOMES:
        return True
    if fields.get("seedConsumed") is not True:
        return True
    return not (
        outcome in {"knownInterfaceClaim", "completeClaim"}
        and fields.get("certAccepted") is True
        and fields.get("acceptanceWindowPassed") is True
        and fields.get("noRetainedBlockingAuthority") is True
    )


def outcome_record(
    outcome: str,
    *,
    task_envelope_ref: str = "none",
    fields: dict[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    data = fields or {}
    record: dict[str, JsonValue] = {
        "schemaId": ACTIVE_SCHEMA,
        "outcome": outcome,
        "taskEnvelopeRef": task_envelope_ref,
        "bootDecisionHash": str(data.get("bootDecisionHash", "none")),
        "cardRef": str(data.get("cardRef", "none")),
        "certRef": str(data.get("certRef", "none")),
        "missingPrimitives": _str_list(data.get("missingPrimitives", [])),
        "requestedRoots": _str_list(data.get("requestedRoots", [])),
        "requestedTools": _str_list(data.get("requestedTools", [])),
        "riskClass": str(data.get("riskClass", "micro")),
        "safeFallback": str(data.get("safeFallback", "noProtectedAction")),
        "privacyLimit": str(data.get("privacyLimit", "noSecretPayload")),
        "nonAuthorization": computed_non_authorization(outcome, data),
        "reason": str(data.get("reason", "")),
        "recordHash": "pending",
    }
    out = attach_record_hash(record)
    validate_outcome_record(out)
    return out


def validate_outcome_record(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, OUTCOME_FIELDS)
    if require_str(record["schemaId"], "schemaId", nonempty=True) != ACTIVE_SCHEMA:
        raise ValueError("unsupported schemaId")
    outcome = require_enum(record["outcome"], "outcome", TRANSITION_OUTCOMES)
    require_ref(record["taskEnvelopeRef"], "taskEnvelopeRef")
    require_ref(record["bootDecisionHash"], "bootDecisionHash")
    require_ref(record["cardRef"], "cardRef")
    require_ref(record["certRef"], "certRef")
    require_str_list(record["missingPrimitives"], "missingPrimitives")
    require_str_list(record["requestedRoots"], "requestedRoots")
    require_str_list(record["requestedTools"], "requestedTools")
    require_enum(record["riskClass"], "riskClass", RISK_CLASSES)
    require_str(record["safeFallback"], "safeFallback", nonempty=True)
    require_str(record["privacyLimit"], "privacyLimit", nonempty=True)
    non_auth = require_bool(record["nonAuthorization"], "nonAuthorization")
    if outcome in NON_AUTHORIZING_OUTCOMES and not non_auth:
        raise ValueError("nonAuthorization conflicts with outcome")
    if not non_auth and outcome not in {"knownInterfaceClaim", "completeClaim"}:
        raise ValueError("only knownInterfaceClaim or completeClaim can be authorizing")
    require_reason(record["reason"], "reason")
    require_hash(record["recordHash"], "recordHash")


def _str_list(value: JsonValue) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
