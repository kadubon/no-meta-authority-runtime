"""Checker result primitives."""

from __future__ import annotations

from dataclasses import dataclass

from no_meta_authority_runtime.canonical.hash import content_hash
from no_meta_authority_runtime.canonical.json import JsonValue

CHECKER_OUTCOMES = {"allow", "deny", "defer", "halt", "timeout"}


@dataclass(frozen=True)
class CheckerResult:
    outcome: str
    reason_code: str
    evidence: dict[str, JsonValue]

    def to_json(self) -> dict[str, JsonValue]:
        record: dict[str, JsonValue] = {
            "outcome": self.outcome,
            "reasonCode": self.reason_code,
            "evidence": self.evidence,
        }
        record["evidenceHash"] = content_hash(self.evidence)
        return record


def allow(reason: str = "allow", evidence: dict[str, JsonValue] | None = None) -> CheckerResult:
    return CheckerResult("allow", reason, evidence or {})


def deny(reason: str, evidence: dict[str, JsonValue] | None = None) -> CheckerResult:
    return CheckerResult("deny", reason, evidence or {})


def halt(reason: str, evidence: dict[str, JsonValue] | None = None) -> CheckerResult:
    return CheckerResult("halt", reason, evidence or {})


def timeout(reason: str = "timeout", evidence: dict[str, JsonValue] | None = None) -> CheckerResult:
    return CheckerResult("timeout", reason, evidence or {})
