"""Seed command result records."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import attach_record_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.ledger.head import Head
from no_meta_authority_runtime.schemas.constants import ACTIVE_SCHEMA


def seed_command_result(
    *,
    command: str,
    outcome: str,
    head: Head,
    boot_decision_hash: str = "none",
    dispatch_record_hash: str = "none",
    consumption_record_hash: str = "none",
    missing_primitives: list[str] | None = None,
    reason_code: str = "",
) -> dict[str, JsonValue]:
    record: dict[str, JsonValue] = {
        "schemaId": ACTIVE_SCHEMA,
        "command": command,
        "outcome": outcome,
        "headSeq": head.seq,
        "headHash": head.hash,
        "bootDecisionHash": boot_decision_hash,
        "dispatchRecordHash": dispatch_record_hash,
        "consumptionRecordHash": consumption_record_hash,
        "missingPrimitives": missing_primitives or [],
        "reasonCode": reason_code,
        "recordHash": "pending",
    }
    return attach_record_hash(record)
