"""Ledger scanning and fail-closed recovery classification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from no_meta_authority_runtime.canonical.errors import LedgerError
from no_meta_authority_runtime.canonical.hash import GENESIS_HASH, verify_record_hash
from no_meta_authority_runtime.canonical.json import JsonValue, parse_json
from no_meta_authority_runtime.ledger.head import Head, read_head


@dataclass(frozen=True)
class LedgerRecordFile:
    path: Path
    record: dict[str, JsonValue]


@dataclass(frozen=True)
class LedgerScan:
    ok: bool
    reason: str
    head: Head
    records: tuple[dict[str, JsonValue], ...]
    open_decisions: tuple[str, ...]
    dispatched_unconsumed: tuple[str, ...]


def read_record_files(root: Path) -> list[LedgerRecordFile]:
    if not root.exists():
        return []
    out: list[LedgerRecordFile] = []
    for path in sorted(root.glob("*.json")):
        if path.name == "HEAD.json":
            continue
        data = parse_json(path.read_bytes())
        if not isinstance(data, dict):
            raise LedgerError(f"ledger record is not an object: {path.name}")
        out.append(LedgerRecordFile(path=path, record=data))
    return out


def scan_ledger(root: str | Path) -> LedgerScan:
    ledger_root = Path(root)
    try:
        head = read_head(ledger_root)
        record_files = read_record_files(ledger_root)
        records = [item.record for item in record_files]
        _validate_chain(records)
        if records:
            last = records[-1]
            if head.seq != last["seq"] or head.hash != last["recordHash"]:
                return _bad("headMismatch", head, records)
        elif head.seq != 0 or head.hash != GENESIS_HASH:
            return _bad("headMismatch", head, records)
        open_decisions, dispatched = _decision_state(records)
        return LedgerScan(
            ok=True,
            reason="ok",
            head=head,
            records=tuple(records),
            open_decisions=tuple(open_decisions),
            dispatched_unconsumed=tuple(dispatched),
        )
    except (OSError, ValueError, LedgerError) as exc:
        return LedgerScan(
            ok=False,
            reason=exc.__class__.__name__,
            head=Head(0, GENESIS_HASH, "genesis"),
            records=(),
            open_decisions=(),
            dispatched_unconsumed=(),
        )


def _validate_chain(records: list[dict[str, JsonValue]]) -> None:
    seen_seq: set[int] = set()
    records.sort(key=lambda rec: int(rec.get("seq", -1)))
    prev_hash = GENESIS_HASH
    for expected_seq, record in enumerate(records, start=1):
        seq = record.get("seq")
        if not isinstance(seq, int) or isinstance(seq, bool):
            raise LedgerError("record seq is invalid")
        if seq in seen_seq:
            raise LedgerError("duplicate sequence number")
        seen_seq.add(seq)
        if seq != expected_seq:
            raise LedgerError("sequence gap")
        if record.get("prevHash") != prev_hash:
            raise LedgerError("previous hash mismatch")
        verify_record_hash(record)
        prev_hash = str(record["recordHash"])


def _decision_state(records: list[dict[str, JsonValue]]) -> tuple[list[str], list[str]]:
    states: dict[str, str] = {}
    dispatches: dict[str, str] = {}
    for record in records:
        phase = record.get("phase")
        if phase == "bootDecision":
            states[str(record["recordHash"])] = "open"
        elif phase == "dispatched":
            decision = str(record.get("bootDecisionHash", "none"))
            states[decision] = "dispatched"
            dispatches[decision] = str(record["recordHash"])
        elif phase in {"consumed", "denied", "timedOut", "halted", "recovered"}:
            decision = str(record.get("bootDecisionHash", record.get("recordHash", "none")))
            states[decision] = "closed"
    open_decisions = [key for key, state in states.items() if state == "open"]
    dispatched = [dispatches[key] for key, state in states.items() if state == "dispatched"]
    return open_decisions, dispatched


def _bad(reason: str, head: Head, records: list[dict[str, JsonValue]]) -> LedgerScan:
    return LedgerScan(
        ok=False,
        reason=reason,
        head=head,
        records=tuple(records),
        open_decisions=(),
        dispatched_unconsumed=(),
    )
