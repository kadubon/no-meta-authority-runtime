"""Host ledger record schema."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import attach_record_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.base import (
    require_exact_fields,
    require_hash,
    require_int,
    require_object,
    require_ref,
    require_str,
    require_str_list,
)
from no_meta_authority_runtime.schemas.constants import ACTIVE_SCHEMA

LEDGER_RECORD_FIELDS = [
    "schemaId",
    "id",
    "prevHash",
    "txId",
    "phase",
    "requestHash",
    "actionHash",
    "resourceSet",
    "checkerIds",
    "inputCommits",
    "result",
    "timeout",
    "rollbackRef",
    "envelopeHash",
    "selectionHash",
    "time",
    "writer",
    "recordHash",
]


def ledger_record(
    *,
    record_id: str,
    tx_id: str,
    phase: str,
    request_hash: str = "none",
    action_hash: str = "none",
    result: dict[str, JsonValue] | None = None,
    time: int = 0,
) -> dict[str, JsonValue]:
    record: dict[str, JsonValue] = {
        "schemaId": ACTIVE_SCHEMA,
        "id": record_id,
        "prevHash": "0" * 64,
        "txId": tx_id,
        "phase": phase,
        "requestHash": request_hash,
        "actionHash": action_hash,
        "resourceSet": [],
        "checkerIds": [],
        "inputCommits": [],
        "result": result or {},
        "timeout": 0,
        "rollbackRef": "none",
        "envelopeHash": "none",
        "selectionHash": "none",
        "time": time,
        "writer": "schemaBuilder",
        "recordHash": "pending",
    }
    out = attach_record_hash(record)
    validate_ledger_record(out)
    return out


def validate_ledger_record(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, LEDGER_RECORD_FIELDS)
    if require_str(record["schemaId"], "schemaId", nonempty=True) != ACTIVE_SCHEMA:
        raise ValueError("unsupported schemaId")
    require_str(record["id"], "id", nonempty=True)
    require_hash(record["prevHash"], "prevHash")
    require_str(record["txId"], "txId", nonempty=True)
    require_str(record["phase"], "phase", nonempty=True)
    require_ref(record["requestHash"], "requestHash")
    require_ref(record["actionHash"], "actionHash")
    require_str_list(record["resourceSet"], "resourceSet")
    require_str_list(record["checkerIds"], "checkerIds")
    refs = record["inputCommits"]
    if not isinstance(refs, list):
        raise ValueError("inputCommits must be an array")
    require_object(record["result"], "result")
    require_int(record["timeout"], "timeout")
    require_ref(record["rollbackRef"], "rollbackRef")
    require_ref(record["envelopeHash"], "envelopeHash")
    require_ref(record["selectionHash"], "selectionHash")
    require_int(record["time"], "time")
    require_str(record["writer"], "writer", nonempty=True)
    require_hash(record["recordHash"], "recordHash")
