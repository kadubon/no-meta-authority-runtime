"""Reference transition gate."""

from __future__ import annotations

from dataclasses import dataclass

from no_meta_authority_runtime.canonical.errors import HashMismatchError, SchemaError
from no_meta_authority_runtime.canonical.hash import verify_record_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.gate.claim_evaluator import decide_transition_outcome
from no_meta_authority_runtime.schemas.certificate import (
    validate_claim_card,
    validate_transition_certificate,
)


@dataclass(frozen=True)
class GateDecision:
    outcome: str
    reason: str
    transition_outcome: str
    authorizing: bool = False


def transition_gate(
    certificate: dict[str, JsonValue],
    card: dict[str, JsonValue],
) -> GateDecision:
    try:
        validate_claim_card(card)
        validate_transition_certificate(certificate)
        verify_record_hash(card)
        verify_record_hash(certificate)
    except (HashMismatchError, ValueError, SchemaError):
        return GateDecision("halt", "schemaInvalid", "halt")
    if certificate.get("cardRef") != card.get("recordHash"):
        return GateDecision("halt", "cardRefMismatch", "halt")
    transition_outcome, reason = decide_transition_outcome(card)
    if card.get("recordHash") not in certificate.get("evidence", []):
        return GateDecision("halt", "certificateMissingCardEvidence", "halt")
    acceptance = certificate.get("acceptance", {})
    if not isinstance(acceptance, dict) or acceptance.get("accepted") is not True:
        return GateDecision("defer", "certificateNotAccepted", transition_outcome)
    if acceptance.get("expectedTransitionOutcome") != transition_outcome:
        return GateDecision("defer", "certificateTransitionMismatch", transition_outcome)
    residuals = certificate.get("residuals", {})
    if isinstance(residuals, dict) and residuals.get("retainedAuthority") is True:
        return GateDecision("defer", "certificateRetainsAuthority", transition_outcome)
    kernel = certificate.get("kernel", {})
    if isinstance(kernel, dict) and (kernel.get("checkerUpdate") is True or kernel.get("kernelUpdate") is True):
        return GateDecision("halt", "certificateKernelUpdate", "halt")
    if transition_outcome in {"knownInterfaceClaim", "completeClaim"}:
        return GateDecision("allow", reason, transition_outcome, True)
    if transition_outcome in {"provisionalClaim", "partialClaim"}:
        return GateDecision("defer", reason, transition_outcome)
    if transition_outcome == "strongerTierRequest":
        return GateDecision("defer", reason, transition_outcome)
    if transition_outcome == "hostRequest":
        return GateDecision("defer", reason, transition_outcome)
    if transition_outcome == "defer":
        return GateDecision("defer", reason, transition_outcome)
    if transition_outcome == "timeout":
        return GateDecision("timeout", reason, transition_outcome)
    if transition_outcome == "halt":
        return GateDecision("halt", reason, transition_outcome)
    return GateDecision("deny", reason, transition_outcome)
