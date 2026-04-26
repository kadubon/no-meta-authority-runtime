"""Deterministic seed interpreter."""

from __future__ import annotations

from pathlib import Path

from no_meta_authority_runtime.canonical.errors import CanonicalError, MatcherError, SchemaError
from no_meta_authority_runtime.canonical.hash import content_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.ledger.append_only import AppendOnlyLedger
from no_meta_authority_runtime.ledger.recovery import scan_ledger
from no_meta_authority_runtime.matchers.forbidden import evaluate_forbidden_matchers
from no_meta_authority_runtime.schemas.action import validate_action_descriptor
from no_meta_authority_runtime.schemas.boot_decision import validate_boot_decision
from no_meta_authority_runtime.schemas.constants import ACTION_KINDS, ACTIVE_SCHEMA
from no_meta_authority_runtime.schemas.task_envelope import validate_task_envelope
from no_meta_authority_runtime.seed.commands import seed_command_result
from no_meta_authority_runtime.seed.state_machine import (
    decision_states,
    dispatch_for_decision,
    find_record,
    open_decisions,
)


class SeedInterpreter:
    """Fail-closed interpreter for BootDecision records."""

    def __init__(self, ledger_root: str | Path) -> None:
        self.ledger = AppendOnlyLedger(ledger_root)

    def head(self) -> dict[str, JsonValue]:
        return seed_command_result(command="head", outcome="consumed", head=self.ledger.head())

    def parse(self, task_envelope: dict[str, JsonValue], *, now: int = 0) -> dict[str, JsonValue]:
        try:
            validate_task_envelope(task_envelope, now=now)
        except (ValueError, SchemaError, CanonicalError):
            return self._result("parse", "halt", "malformedTaskEnvelope")
        return self._result("parse", "consumed", "parsed")

    def issue(self, decision: dict[str, JsonValue], *, now: int = 0) -> dict[str, JsonValue]:
        scan = scan_ledger(self.ledger.root)
        if not scan.ok:
            return self._result("issue", "halt", scan.reason)
        if open_decisions(list(scan.records)):
            return self._result("issue", "halt", "openDecision")
        head = self.ledger.head()
        if decision.get("seq") != head.seq + 1 or decision.get("prevHash") != head.hash:
            return self._result("issue", "deny", "badSequence")
        try:
            validate_boot_decision(decision, now=now)
        except (ValueError, SchemaError, CanonicalError):
            return self._result("issue", "halt", "malformedBootDecision")
        appended = self.ledger.append({**decision, "phase": "bootDecision"})
        return self._result(
            "issue",
            "consumed",
            "",
            boot_decision_hash=str(appended["recordHash"]),
        )

    def dispatch(
        self,
        boot_decision_hash: str,
        action: dict[str, JsonValue],
        task_envelope: dict[str, JsonValue],
        *,
        now: int = 0,
    ) -> dict[str, JsonValue]:
        records = self.ledger.records()
        states = decision_states(records)
        if states.get(boot_decision_hash) != "open":
            return self._result("dispatch", "deny", "decisionNotOpen", boot_decision_hash)
        decision = find_record(records, record_hash=boot_decision_hash, phase="bootDecision")
        if decision is None:
            return self._result("dispatch", "deny", "decisionNotFound", boot_decision_hash)
        if action.get("kind") not in ACTION_KINDS:
            return self._terminal_before_dispatch(
                "dispatch", boot_decision_hash, action, "deny", "unknownActionKind"
            )
        try:
            decision_body = {key: value for key, value in decision.items() if key != "phase"}
            validate_boot_decision(decision_body, now=now)
            validate_action_descriptor(action)
        except (ValueError, SchemaError, CanonicalError):
            return self._terminal_before_dispatch(
                "dispatch", boot_decision_hash, action, "halt", "malformedDispatchInput"
            )
        try:
            bad = evaluate_forbidden_matchers(list(decision["forbiddenMatchers"]), action)
        except MatcherError:
            return self._terminal_before_dispatch(
                "dispatch", boot_decision_hash, action, "halt", "matcherError"
            )
        if bad is not None:
            return self._terminal_before_dispatch(
                "dispatch", boot_decision_hash, action, bad.outcome, bad.reason_code
            )
        if content_hash(action) != decision.get("permittedActionHash"):
            return self._terminal_before_dispatch(
                "dispatch",
                boot_decision_hash,
                action,
                "deny",
                "permittedActionHashMismatch",
            )
        dispatch = self.ledger.append(
            {
                "schemaId": ACTIVE_SCHEMA,
                "bootDecisionHash": boot_decision_hash,
                "actionHash": content_hash(action),
                "phase": "dispatched",
                "outcome": "none",
                "reasonCode": "",
                "issuedAt": now,
                "recordHash": "pending",
            }
        )
        result = self._run_safe_action(action, task_envelope)
        phase = "consumed" if result["outcome"] == "consumed" else "denied"
        consumption = self.ledger.append(
            {
                "schemaId": ACTIVE_SCHEMA,
                "bootDecisionHash": boot_decision_hash,
                "dispatchRecordHash": str(dispatch["recordHash"]),
                "actionHash": content_hash(action),
                "phase": phase,
                "outcome": str(result["outcome"]),
                "resultHash": content_hash(result),
                "reasonCode": str(result.get("reason", "")),
                "issuedAt": now,
                "recordHash": "pending",
            }
        )
        return self._result(
            "dispatch",
            str(result["outcome"]),
            str(result.get("reason", "")),
            boot_decision_hash,
            str(dispatch["recordHash"]),
            str(consumption["recordHash"]),
            _missing(result),
        )

    def consume(
        self,
        boot_decision_hash: str,
        dispatch_record_hash: str,
        action_result: dict[str, JsonValue],
        *,
        now: int = 0,
    ) -> dict[str, JsonValue]:
        records = self.ledger.records()
        if decision_states(records).get(boot_decision_hash) != "dispatched":
            return self._result("consume", "deny", "decisionNotDispatched", boot_decision_hash)
        dispatch = dispatch_for_decision(
            records,
            boot_decision_hash=boot_decision_hash,
            dispatch_record_hash=dispatch_record_hash,
        )
        if dispatch is None:
            return self._result("consume", "deny", "dispatchNotFound", boot_decision_hash)
        outcome = str(action_result.get("outcome", "consumed"))
        if outcome not in {"consumed", "deny", "defer", "timeout", "halt", "recovered"}:
            outcome = "halt"
        phase = {
            "consumed": "consumed",
            "recovered": "recovered",
            "deny": "denied",
            "defer": "halted",
            "timeout": "timedOut",
            "halt": "halted",
        }[outcome]
        consumption = self.ledger.append(
            {
                "schemaId": ACTIVE_SCHEMA,
                "bootDecisionHash": boot_decision_hash,
                "dispatchRecordHash": dispatch_record_hash,
                "actionHash": str(dispatch.get("actionHash", "none")),
                "phase": phase,
                "outcome": outcome,
                "resultHash": content_hash(action_result),
                "reasonCode": str(action_result.get("reason", "")),
                "issuedAt": now,
                "recordHash": "pending",
            }
        )
        return self._result(
            "consume",
            outcome,
            str(action_result.get("reason", "")),
            boot_decision_hash,
            dispatch_record_hash,
            str(consumption["recordHash"]),
        )

    def deny(self, boot_decision_hash: str, reason_code: str = "explicitDeny", *, now: int = 0) -> dict[str, JsonValue]:
        records = self.ledger.records()
        if decision_states(records).get(boot_decision_hash) not in {"open", "dispatched"}:
            return self._result("deny", "deny", "decisionNotOpen", boot_decision_hash)
        consumption = self.ledger.append(
            {
                "schemaId": ACTIVE_SCHEMA,
                "bootDecisionHash": boot_decision_hash,
                "dispatchRecordHash": "none",
                "actionHash": "none",
                "phase": "denied",
                "outcome": "deny",
                "resultHash": "none",
                "reasonCode": reason_code,
                "issuedAt": now,
                "recordHash": "pending",
            }
        )
        return self._result(
            "deny",
            "deny",
            reason_code,
            boot_decision_hash,
            consumption_record_hash=str(consumption["recordHash"]),
        )

    def recover(self, *, now: int = 0) -> dict[str, JsonValue]:
        scan = scan_ledger(self.ledger.root)
        if not scan.ok:
            return self._result("recover", "halt", scan.reason)
        if scan.open_decisions:
            decision_hash = scan.open_decisions[0]
            record = self.ledger.append_recovery(
                {
                    "schemaId": ACTIVE_SCHEMA,
                    "bootDecisionHash": decision_hash,
                    "dispatchRecordHash": "none",
                    "actionHash": "none",
                    "phase": "halted",
                    "outcome": "halt",
                    "resultHash": "none",
                    "reasonCode": "openDecisionRecovered",
                    "issuedAt": now,
                    "recordHash": "pending",
                }
            )
            return self._result(
                "recover",
                "recovered",
                "openDecisionRecovered",
                decision_hash,
                consumption_record_hash=str(record["recordHash"]),
            )
        if scan.dispatched_unconsumed:
            dispatch_hash = scan.dispatched_unconsumed[0]
            dispatch = find_record(list(scan.records), record_hash=dispatch_hash, phase="dispatched")
            decision_hash = str(dispatch.get("bootDecisionHash", "none")) if dispatch else "none"
            record = self.ledger.append_recovery(
                {
                    "schemaId": ACTIVE_SCHEMA,
                    "bootDecisionHash": decision_hash,
                    "dispatchRecordHash": dispatch_hash,
                    "actionHash": str(dispatch.get("actionHash", "none")) if dispatch else "none",
                    "phase": "halted",
                    "outcome": "halt",
                    "resultHash": "none",
                    "reasonCode": "dispatchRecovered",
                    "issuedAt": now,
                    "recordHash": "pending",
                }
            )
            return self._result(
                "recover",
                "recovered",
                "dispatchRecovered",
                decision_hash,
                dispatch_hash,
                str(record["recordHash"]),
            )
        return self._result("recover", "recovered", "ok")

    def digest(self) -> dict[str, JsonValue]:
        return seed_command_result(command="digest", outcome="consumed", head=self.ledger.head())

    def _terminal_before_dispatch(
        self,
        command: str,
        boot_decision_hash: str,
        action: dict[str, JsonValue],
        outcome: str,
        reason_code: str,
    ) -> dict[str, JsonValue]:
        phase = "denied" if outcome == "deny" else "halted"
        action_hash = content_hash(action)
        consumption = self.ledger.append(
            {
                "schemaId": ACTIVE_SCHEMA,
                "bootDecisionHash": boot_decision_hash,
                "dispatchRecordHash": "none",
                "actionHash": action_hash,
                "phase": phase,
                "outcome": outcome,
                "resultHash": "none",
                "reasonCode": reason_code,
                "issuedAt": 0,
                "recordHash": "pending",
            }
        )
        return self._result(
            command,
            outcome,
            reason_code,
            boot_decision_hash,
            consumption_record_hash=str(consumption["recordHash"]),
        )

    def _run_safe_action(
        self,
        action: dict[str, JsonValue],
        task_envelope: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        if action.get("kind") != "safeInventory":
            return {"outcome": "deny", "reason": "unsupportedSeedAction"}
        if task_envelope.get("rootContractRef") == "none":
            return {
                "outcome": "consumed",
                "state": "requestOnly",
                "missingPrimitives": ["rootContract"],
                "reason": "missingRootContract",
            }
        if task_envelope.get("grantedHostRoot") and task_envelope.get("grantedWriteRoots"):
            return {"outcome": "consumed", "state": "localInstallable", "missingPrimitives": []}
        if task_envelope.get("grantedScratchRoot"):
            return {
                "outcome": "consumed",
                "state": "scratchOnly",
                "missingPrimitives": ["hostRoot"],
                "reason": "scratchOnly",
            }
        return {
            "outcome": "consumed",
            "state": "requestOnly",
            "missingPrimitives": ["seedInterpreterOrWrapper", "hostRoot"],
            "reason": "requestOnly",
        }

    def _result(
        self,
        command: str,
        outcome: str,
        reason_code: str,
        boot_decision_hash: str = "none",
        dispatch_record_hash: str = "none",
        consumption_record_hash: str = "none",
        missing_primitives: list[str] | None = None,
    ) -> dict[str, JsonValue]:
        return seed_command_result(
            command=command,
            outcome=outcome,
            head=self.ledger.head(),
            boot_decision_hash=boot_decision_hash,
            dispatch_record_hash=dispatch_record_hash,
            consumption_record_hash=consumption_record_hash,
            missing_primitives=missing_primitives or [],
            reason_code=reason_code,
        )


def _missing(result: dict[str, JsonValue]) -> list[str]:
    missing = result.get("missingPrimitives", [])
    if not isinstance(missing, list):
        return []
    return [item for item in missing if isinstance(item, str)]
