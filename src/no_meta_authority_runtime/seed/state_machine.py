"""Seed ledger state machine helpers."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.json import JsonValue


def decision_states(records: list[dict[str, JsonValue]]) -> dict[str, str]:
    states: dict[str, str] = {}
    for record in records:
        phase = record.get("phase")
        if phase == "bootDecision":
            states[str(record["recordHash"])] = "open"
        elif phase == "dispatched":
            states[str(record.get("bootDecisionHash", "none"))] = "dispatched"
        elif phase in {"consumed", "denied", "timedOut", "halted", "recovered"}:
            states[str(record.get("bootDecisionHash", record.get("recordHash", "none")))] = "closed"
    return states


def open_decisions(records: list[dict[str, JsonValue]]) -> list[str]:
    return [key for key, value in decision_states(records).items() if value in {"open", "dispatched"}]


def find_record(
    records: list[dict[str, JsonValue]],
    *,
    record_hash: str,
    phase: str | None = None,
) -> dict[str, JsonValue] | None:
    for record in records:
        if record.get("recordHash") == record_hash and (phase is None or record.get("phase") == phase):
            return record
    return None


def dispatch_for_decision(
    records: list[dict[str, JsonValue]],
    *,
    boot_decision_hash: str,
    dispatch_record_hash: str,
) -> dict[str, JsonValue] | None:
    for record in records:
        if (
            record.get("phase") == "dispatched"
            and record.get("bootDecisionHash") == boot_decision_hash
            and record.get("recordHash") == dispatch_record_hash
        ):
            return record
    return None
