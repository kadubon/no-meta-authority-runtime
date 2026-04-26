"""Minimal local host for local reversible file writes."""

from __future__ import annotations

from pathlib import Path

from no_meta_authority_runtime.canonical.hash import attach_record_hash, content_hash
from no_meta_authority_runtime.canonical.json import JsonValue, canonical_bytes
from no_meta_authority_runtime.checkers.micro_predicates import (
    no_external_effect,
    path_allowed,
    rollback_ready,
    selection_deterministic,
    within_budget,
)
from no_meta_authority_runtime.host.digest import digest_record
from no_meta_authority_runtime.host.probes import run_host_probe_bundle
from no_meta_authority_runtime.host.rollback import create_file_snapshot
from no_meta_authority_runtime.host.transaction import new_tx_id
from no_meta_authority_runtime.ledger.append_only import AppendOnlyLedger
from no_meta_authority_runtime.ledger.recovery import scan_ledger
from no_meta_authority_runtime.matchers.path_policy import normalize_literal_path
from no_meta_authority_runtime.schemas.constants import ACTIVE_SCHEMA


class MinimalHost:
    """Single-resource-class host for safe local reversible actions."""

    def __init__(self, host_root: str | Path, task_envelope: dict[str, JsonValue]) -> None:
        self.root = Path(host_root)
        self.task_envelope = task_envelope
        self.ledger = AppendOnlyLedger(self.root / "ledger")
        self.rollback_root = self.root / "rollback"
        self.checkers_root = self.root / "checkers"

    def boot(self) -> dict[str, JsonValue]:
        guard = self._host_root_guard()
        if guard is not None:
            return guard
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "ledger").mkdir(exist_ok=True)
        self.rollback_root.mkdir(exist_ok=True)
        self.checkers_root.mkdir(exist_ok=True)
        manifest = {
            "schemaId": ACTIVE_SCHEMA,
            "hostId": "minimal-local-host",
            "taskEnvelopeRef": str(self.task_envelope.get("recordHash", "none")),
            "protectedPatterns": self._write_roots(),
            "deniedPatterns": self._denied_roots(),
            "effectTagTable": {"writeText": ["localState"]},
            "allowedTools": [],
            "checkerDigests": {},
            "tcbProfile": "LocalMicro",
            "budgets": {"timeout": 1000},
            "pathRules": {"literalOnly": True},
            "sandboxProfile": {"network": "deny", "credentials": "deny"},
            "rollbackPolicy": {"boundedFilePreimage": True},
            "recordHash": "pending",
        }
        manifest = attach_record_hash(manifest)
        (self.root / "manifest.json").write_bytes(canonical_bytes(manifest))
        return {"outcome": "consumed", "manifestHash": manifest["recordHash"]}

    def prepare(self, operation: dict[str, JsonValue], *, now: int = 0) -> dict[str, JsonValue]:
        guard = self._host_root_guard()
        if guard is not None:
            return guard
        path = self._operation_path(operation)
        tx_id = new_tx_id()
        allowed = path_allowed(path, self._operation_write_roots(), self._denied_roots())
        if allowed.outcome != "allow":
            record = self._append_tx(
                tx_id,
                _phase_for_outcome(allowed.outcome),
                operation,
                {"path": allowed.to_json()},
                now,
            )
            return {
                "outcome": allowed.outcome,
                "txId": tx_id,
                "recordHash": record["recordHash"],
                "reason": allowed.reason_code,
            }
        rollback_ref = create_file_snapshot(path, self.rollback_root.as_posix(), tx_id)
        record = self._append_tx(tx_id, "prepared", operation, {"rollbackRef": rollback_ref}, now)
        return {"outcome": "consumed", "txId": tx_id, "rollbackRef": rollback_ref, "recordHash": record["recordHash"]}

    def check(self, tx_id: str, operation: dict[str, JsonValue], *, now: int = 0) -> dict[str, JsonValue]:
        guard = self._host_root_guard()
        if guard is not None:
            return guard
        prepared = self._find_tx(tx_id, "prepared")
        if prepared is None:
            return {"outcome": "deny", "reason": "missingPrepared", "txId": tx_id}
        path = self._operation_path(operation)
        prepared_result = prepared.get("result", {})
        rollback_ref = (
            str(prepared_result.get("rollbackRef", "")) if isinstance(prepared_result, dict) else ""
        )
        checks = [
            path_allowed(path, self._operation_write_roots(), self._denied_roots()),
            no_external_effect(["localState"]),
            rollback_ready(rollback_ref, self.rollback_root.as_posix()),
            selection_deterministic([{"path": path}], {"path": path}),
            within_budget(0, 1000),
        ]
        outcome = _compose_checker_outcome([check.outcome for check in checks])
        record = self._append_tx(
            tx_id,
            "checked" if outcome == "allow" else _phase_for_outcome(outcome),
            operation,
            {"checks": [check.to_json() for check in checks]},
            now,
        )
        return {
            "outcome": "consumed" if outcome == "allow" else outcome,
            "txId": tx_id,
            "recordHash": record["recordHash"],
            "reason": "" if outcome == "allow" else "checkerFailure",
        }

    def commit(self, tx_id: str, operation: dict[str, JsonValue], *, now: int = 0) -> dict[str, JsonValue]:
        guard = self._host_root_guard()
        if guard is not None:
            return guard
        if self._find_tx(tx_id, "checked") is None:
            return {"outcome": "deny", "reason": "missingChecked", "txId": tx_id}
        path = Path(self._operation_path(operation))
        content = operation.get("content")
        if not isinstance(content, str):
            record = self._append_tx(tx_id, "halted", operation, {"reason": "missingContent"}, now)
            return {"outcome": "halt", "txId": tx_id, "recordHash": record["recordHash"], "reason": "missingContent"}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        committed = self._append_tx(
            tx_id,
            "committed",
            operation,
            {"postHash": content_hash({"content": content})},
            now,
        )
        closed = self._append_tx(tx_id, "closed", operation, {"committedRecordHash": committed["recordHash"]}, now)
        return {"outcome": "consumed", "txId": tx_id, "recordHash": closed["recordHash"]}

    def recover(self, *, now: int = 0) -> dict[str, JsonValue]:
        guard = self._host_root_guard()
        if guard is not None:
            return guard
        scan = scan_ledger(self.ledger.root)
        if not scan.ok:
            record = self.ledger.append(
                {
                    "schemaId": ACTIVE_SCHEMA,
                    "id": "recovery",
                    "txId": "none",
                    "phase": "halted",
                    "requestHash": "none",
                    "actionHash": "none",
                    "resourceSet": [],
                    "checkerIds": [],
                    "inputCommits": [],
                    "result": {"reason": scan.reason},
                    "timeout": 0,
                    "rollbackRef": "none",
                    "envelopeHash": "none",
                    "selectionHash": "none",
                    "time": now,
                    "writer": "minimalHost",
                    "recordHash": "pending",
                }
            )
            return {"outcome": "halt", "reason": scan.reason, "recordHash": record["recordHash"]}
        open_commits = self._committed_without_closed(list(scan.records))
        if open_commits:
            record = self._append_tx(open_commits[0], "inDoubt", {}, {"reason": "committedWithoutClosed"}, now)
            return {"outcome": "halt", "reason": "inDoubt", "recordHash": record["recordHash"]}
        return {"outcome": "recovered", "reason": "ok"}

    def digest(self) -> dict[str, JsonValue]:
        return digest_record(self.ledger.head())

    def probes(self) -> dict[str, JsonValue]:
        return run_host_probe_bundle(self.root.as_posix())

    def deny(self, reason: str = "explicitDeny", *, now: int = 0) -> dict[str, JsonValue]:
        guard = self._host_root_guard()
        if guard is not None:
            return guard
        record = self._append_tx("none", "denied", {}, {"reason": reason}, now)
        return {"outcome": "deny", "recordHash": record["recordHash"], "reason": reason}

    def _append_tx(
        self,
        tx_id: str,
        phase: str,
        operation: dict[str, JsonValue],
        result: dict[str, JsonValue],
        now: int,
    ) -> dict[str, JsonValue]:
        action_hash = content_hash(operation)
        return self.ledger.append(
            {
                "schemaId": ACTIVE_SCHEMA,
                "id": f"{tx_id}-{phase}",
                "txId": tx_id,
                "phase": phase,
                "requestHash": action_hash,
                "actionHash": action_hash,
                "resourceSet": [self._operation_path(operation)] if operation else [],
                "checkerIds": [],
                "inputCommits": [],
                "result": result,
                "timeout": 0,
                "rollbackRef": str(result.get("rollbackRef", "none")),
                "envelopeHash": "none",
                "selectionHash": "none",
                "time": now,
                "writer": "minimalHost",
                "recordHash": "pending",
            }
        )

    def _find_tx(self, tx_id: str, phase: str) -> dict[str, JsonValue] | None:
        for record in self.ledger.records():
            if record.get("txId") == tx_id and record.get("phase") == phase:
                return record
        return None

    def _operation_path(self, operation: dict[str, JsonValue]) -> str:
        raw_path = operation.get("path")
        if not isinstance(raw_path, str):
            raise ValueError("operation path is required")
        return normalize_literal_path(raw_path)

    def _write_roots(self) -> list[str]:
        roots: list[str] = []
        for key in ("grantedScratchRoot", "grantedHostRoot"):
            value = self.task_envelope.get(key, "")
            if isinstance(value, str) and value:
                roots.append(value)
        write_roots = self.task_envelope.get("grantedWriteRoots", [])
        if isinstance(write_roots, list):
            roots.extend([item for item in write_roots if isinstance(item, str)])
        return roots

    def _operation_write_roots(self) -> list[str]:
        write_roots = self.task_envelope.get("grantedWriteRoots", [])
        return [item for item in write_roots if isinstance(item, str)] if isinstance(write_roots, list) else []

    def _host_root_guard(self) -> dict[str, JsonValue] | None:
        declared = self.task_envelope.get("grantedHostRoot", "")
        if not isinstance(declared, str) or not declared:
            return {"outcome": "halt", "reason": "missingDeclaredHostRoot"}
        allowed = path_allowed(self.root.resolve(strict=False).as_posix(), [declared], self._denied_roots())
        if allowed.outcome != "allow":
            return {"outcome": "halt", "reason": "hostRootOutsideEnvelope"}
        return None

    def _denied_roots(self) -> list[str]:
        denied = self.task_envelope.get("deniedRoots", [])
        return [item for item in denied if isinstance(item, str)] if isinstance(denied, list) else []

    @staticmethod
    def _committed_without_closed(records: list[dict[str, JsonValue]]) -> list[str]:
        committed = {str(record.get("txId")) for record in records if record.get("phase") == "committed"}
        closed = {str(record.get("txId")) for record in records if record.get("phase") == "closed"}
        return sorted(committed - closed)


def _compose_checker_outcome(outcomes: list[str]) -> str:
    if "halt" in outcomes:
        return "halt"
    if "timeout" in outcomes:
        return "timeout"
    if "deny" in outcomes:
        return "deny"
    if "defer" in outcomes:
        return "defer"
    return "allow"


def _phase_for_outcome(outcome: str) -> str:
    return {"halt": "halted", "timeout": "timedOut", "deny": "denied", "defer": "deferred"}.get(
        outcome, "halted"
    )
