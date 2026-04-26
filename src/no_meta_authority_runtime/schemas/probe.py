"""Probe and provisioning records."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import attach_record_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.base import (
    require_enum,
    require_exact_fields,
    require_hash,
    require_int,
    require_object,
    require_str,
    require_str_list,
)
from no_meta_authority_runtime.schemas.constants import ACTIVE_SCHEMA, WITNESS_TIERS

PROBE_FIELDS = [
    "schemaId",
    "id",
    "kind",
    "target",
    "method",
    "inputCommit",
    "expected",
    "observed",
    "runner",
    "witnessTier",
    "timeout",
    "resourceBudget",
    "replayScript",
    "checker",
    "outcome",
    "recordHash",
]

PROBE_OUTCOMES = frozenset({"allow", "deny", "defer", "halt", "timeout"})


def probe_record(
    *,
    probe_id: str,
    kind: str,
    target: list[str],
    method: str,
    outcome: str,
    witness_tier: str = "replayableLocal",
    checker: str = "none",
) -> dict[str, JsonValue]:
    record: dict[str, JsonValue] = {
        "schemaId": ACTIVE_SCHEMA,
        "id": probe_id,
        "kind": kind,
        "target": target,
        "method": method,
        "inputCommit": "none",
        "expected": {},
        "observed": {},
        "runner": "local",
        "witnessTier": witness_tier,
        "timeout": 0,
        "resourceBudget": {},
        "replayScript": [],
        "checker": checker,
        "outcome": outcome,
        "recordHash": "pending",
    }
    return attach_record_hash(record)


def validate_probe_record(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, PROBE_FIELDS)
    if require_str(record["schemaId"], "schemaId", nonempty=True) != ACTIVE_SCHEMA:
        raise ValueError("unsupported schemaId")
    require_str(record["id"], "id", nonempty=True)
    require_str(record["kind"], "kind", nonempty=True)
    require_str_list(record["target"], "target")
    require_str(record["method"], "method", nonempty=True)
    require_hash(record["inputCommit"], "inputCommit") if record["inputCommit"] != "none" else None
    require_object(record["expected"], "expected")
    require_object(record["observed"], "observed")
    require_str(record["runner"], "runner", nonempty=True)
    require_enum(record["witnessTier"], "witnessTier", WITNESS_TIERS)
    require_int(record["timeout"], "timeout")
    require_object(record["resourceBudget"], "resourceBudget")
    if not isinstance(record["replayScript"], list):
        raise ValueError("replayScript must be an array")
    require_str(record["checker"], "checker", nonempty=True)
    require_enum(record["outcome"], "outcome", PROBE_OUTCOMES)
    require_hash(record["recordHash"], "recordHash")
