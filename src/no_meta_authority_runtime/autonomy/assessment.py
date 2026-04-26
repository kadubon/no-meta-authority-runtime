"""Boundary-relative autonomy assessment.

This layer maps transition-gate evidence to a machine-readable autonomy stage.
It deliberately does not claim that historical human-feedback residue vanished
from model weights. It only reports whether the declared scope has enough
witnessed mediation to remove live positive authority for that scope.
"""

from __future__ import annotations

from no_meta_authority_runtime.canonical.errors import HashMismatchError, SchemaError
from no_meta_authority_runtime.canonical.hash import MISSING_REF, content_hash, verify_record_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.gate.claim_evaluator import decide_transition_outcome
from no_meta_authority_runtime.gate.transition_gate import transition_gate
from no_meta_authority_runtime.schemas.autonomy import autonomy_assessment
from no_meta_authority_runtime.schemas.certificate import validate_claim_card, validate_transition_certificate
from no_meta_authority_runtime.schemas.constants import TRANSITION_OUTCOMES

_POSITIVE_AUTHORIZING_OUTCOMES = {"knownInterfaceClaim", "completeClaim"}
_OUTCOME_STRENGTH = {
    "halt": 0,
    "timeout": 0,
    "deny": 0,
    "defer": 0,
    "hostRequest": 0,
    "strongerTierRequest": 0,
    "bootDecision": 0,
    "partialClaim": 1,
    "provisionalClaim": 2,
    "knownInterfaceClaim": 3,
    "completeClaim": 4,
}
_RETAINED_CHANNEL_FIELDS = {
    "retainedAuthority": "retainedPositiveAuthority",
    "humanApprovalRequired": "liveHumanApproval",
    "rewardModelRequired": "rewardModelAuthority",
    "constitutionRequired": "externalConstitutionAuthority",
    "openSemanticAuthority": "semanticAuthority",
    "hiddenMaterialSelector": "materialSelectionAuthority",
    "agendaUnbounded": "agendaAuthority",
}


def assess_declared_autonomy(
    card: dict[str, JsonValue],
    *,
    certificate: dict[str, JsonValue] | None = None,
    supplied_transition_outcome: str | None = None,
) -> dict[str, JsonValue]:
    blocking_reasons: list[str] = []
    required_next_evidence: list[str] = []
    retained_channels: list[str] = []

    try:
        validate_claim_card(card)
        verify_record_hash(card)
    except (HashMismatchError, SchemaError, ValueError):
        return blocked_autonomy_assessment("invalidClaimCard")

    card_ref = str(card["recordHash"])
    cert_ref = MISSING_REF
    gate_transition = "defer"
    gate_reason = "missingTransitionCertificate"

    if certificate is None:
        evaluated_transition, evaluated_reason = decide_transition_outcome(card)
        gate_transition = _weaker_transition("defer", evaluated_transition)
        gate_reason = evaluated_reason if gate_transition == evaluated_transition else "missingTransitionCertificate"
        blocking_reasons.append("missingTransitionCertificate")
        required_next_evidence.append("transitionCertificate")
    else:
        try:
            validate_transition_certificate(certificate)
            verify_record_hash(certificate)
        except (HashMismatchError, SchemaError, ValueError):
            return blocked_autonomy_assessment("invalidTransitionCertificate", card_ref=card_ref, scope=_scope(card))
        cert_ref = str(certificate["recordHash"])
        if certificate.get("cardRef") != card_ref:
            return blocked_autonomy_assessment("certificateCardRefMismatch", card_ref=card_ref, scope=_scope(card))
        decision = transition_gate(certificate, card)
        gate_transition = decision.transition_outcome
        gate_reason = decision.reason
        if decision.outcome != "allow":
            blocking_reasons.append(gate_reason)

    if supplied_transition_outcome is not None:
        if supplied_transition_outcome not in TRANSITION_OUTCOMES:
            return blocked_autonomy_assessment(
                "invalidSuppliedTransitionOutcome",
                card_ref=card_ref,
                scope=_scope(card),
            )
        if supplied_transition_outcome != gate_transition:
            blocking_reasons.append("transitionOutcomeMismatch")
            gate_transition = _weaker_transition(gate_transition, supplied_transition_outcome)

    retained_channels.extend(_retained_channels(card))
    if retained_channels:
        blocking_reasons.append("retainedAuthorityChannelPresent")

    required_next_evidence.extend(_required_next_evidence(card, gate_transition, retained_channels))
    claim_is_authorizing = (
        gate_transition in _POSITIVE_AUTHORIZING_OUTCOMES and not blocking_reasons and not retained_channels
    )
    autonomy_level = _autonomy_level(gate_transition, claim_is_authorizing)
    authorization_status = "scopedAuthorizing" if claim_is_authorizing else "nonAuthorizing"

    return autonomy_assessment(
        assessment_id=content_hash(
            {
                "cardRef": card_ref,
                "certRef": cert_ref,
                "transitionOutcome": gate_transition,
                "retainedAuthorityChannels": sorted(set(retained_channels)),
                "blockingReasons": sorted(set(blocking_reasons)),
            }
        ),
        card_ref=card_ref,
        cert_ref=cert_ref,
        scope=_scope(card),
        transition_outcome=gate_transition,
        autonomy_level=autonomy_level,
        authorization_status=authorization_status,
        claim_is_authorizing=claim_is_authorizing,
        human_feedback_residue=_human_feedback_residue(),
        retained_authority_channels=_unique(retained_channels),
        residual_risks=_residual_risks(),
        blocking_reasons=_unique(blocking_reasons),
        required_next_evidence=_unique(required_next_evidence),
        evidence_refs=[] if cert_ref == MISSING_REF else [card_ref, cert_ref],
    )


def blocked_autonomy_assessment(
    reason: str,
    *,
    card_ref: str = MISSING_REF,
    scope: dict[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    return autonomy_assessment(
        assessment_id=content_hash({"blockedReason": reason, "cardRef": card_ref}),
        card_ref=card_ref,
        cert_ref=MISSING_REF,
        scope=scope or {},
        transition_outcome="halt",
        autonomy_level="blocked",
        authorization_status="nonAuthorizing",
        claim_is_authorizing=False,
        human_feedback_residue=_human_feedback_residue(),
        retained_authority_channels=[],
        residual_risks=_residual_risks(),
        blocking_reasons=[reason],
        required_next_evidence=["validClaimCard"],
        evidence_refs=[],
    )


def _autonomy_level(transition_outcome: str, claim_is_authorizing: bool) -> str:
    if not claim_is_authorizing:
        if transition_outcome == "provisionalClaim":
            return "provisionalMigration"
        if transition_outcome == "partialClaim":
            return "partialMigration"
        return "blocked"
    if transition_outcome == "completeClaim":
        return "completeMigration"
    return "knownInterfaceMigration"


def _human_feedback_residue() -> dict[str, JsonValue]:
    return {
        "globalWeightResidueProvenAbsent": False,
        "providerInternalsInspected": False,
        "treatedAsResidualRisk": True,
        "authorityEffect": "notAuthorizingWithoutDeclaredChannel",
    }


def _residual_risks() -> list[str]:
    return [
        "boundaryRelativeOnly",
        "globalHumanFeedbackResidueNotProvenAbsent",
        "providerInternalsNotInspected",
        "tcbRelativeOnly",
        "witnessRelativeOnly",
    ]


def _required_next_evidence(
    card: dict[str, JsonValue],
    transition_outcome: str,
    retained_channels: list[str],
) -> list[str]:
    required: list[str] = []
    boot = _obj(card.get("bootDecision"))
    if card.get("bootRef") == MISSING_REF or boot.get("seedConsumed") is not True:
        required.append("seedConsumedBootDecision")
    boundary = _obj(card.get("boundary"))
    if boundary.get("rootContractRef") in {MISSING_REF, "", None}:
        required.append("rootContract")
    if transition_outcome == "provisionalClaim":
        required.append("acceptanceWindow")
    if transition_outcome == "partialClaim" or retained_channels:
        required.append("retainedAuthorityRemovalEvidence")
    if transition_outcome == "knownInterfaceClaim":
        required.append("independentCompleteInventoryWitness")
    if transition_outcome == "hostRequest":
        required.append("hostMediationPrimitive")
    if transition_outcome == "strongerTierRequest":
        required.append("strongerWitnessTier")
    if transition_outcome in {"defer", "timeout", "halt", "deny"}:
        required.append("blockingConditionResolution")
    return required


def _retained_channels(card: dict[str, JsonValue]) -> list[str]:
    residuals = _obj(card.get("residuals"))
    channels: list[str] = []
    for field, channel in _RETAINED_CHANNEL_FIELDS.items():
        if residuals.get(field) is True:
            channels.append(channel)
    explicit = residuals.get("retainedAuthorityChannels")
    if isinstance(explicit, list):
        channels.extend(item for item in explicit if isinstance(item, str))
    return _unique(channels)


def _weaker_transition(left: str, right: str) -> str:
    left_strength = _OUTCOME_STRENGTH.get(left, 0)
    right_strength = _OUTCOME_STRENGTH.get(right, 0)
    return left if left_strength <= right_strength else right


def _scope(card: dict[str, JsonValue]) -> dict[str, JsonValue]:
    return _obj(card.get("scope"))


def _obj(value: JsonValue | object) -> dict[str, JsonValue]:
    return value if isinstance(value, dict) else {}


def _unique(values: list[str]) -> list[str]:
    return sorted(set(values))
