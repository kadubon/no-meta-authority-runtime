"""Declared autonomy assessment records."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import attach_record_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.base import (
    require_bool,
    require_enum,
    require_exact_fields,
    require_hash,
    require_object,
    require_ref,
    require_ref_list,
    require_str_list,
)
from no_meta_authority_runtime.schemas.constants import (
    ACTIVE_SCHEMA,
    AUTHORIZATION_STATUSES,
    AUTONOMY_LEVELS,
    TRANSITION_OUTCOMES,
)

AUTONOMY_ASSESSMENT_FIELDS = [
    "schemaId",
    "recordType",
    "assessmentId",
    "cardRef",
    "certRef",
    "scope",
    "transitionOutcome",
    "autonomyLevel",
    "authorizationStatus",
    "claimIsAuthorizing",
    "boundaryRelative",
    "tcbRelative",
    "witnessRelative",
    "humanFeedbackResidue",
    "retainedAuthorityChannels",
    "residualRisks",
    "blockingReasons",
    "requiredNextEvidence",
    "evidenceRefs",
    "recordHash",
]


def autonomy_assessment(
    *,
    assessment_id: str,
    card_ref: str,
    cert_ref: str,
    scope: dict[str, JsonValue],
    transition_outcome: str,
    autonomy_level: str,
    authorization_status: str,
    claim_is_authorizing: bool,
    human_feedback_residue: dict[str, JsonValue],
    retained_authority_channels: list[str],
    residual_risks: list[str],
    blocking_reasons: list[str],
    required_next_evidence: list[str],
    evidence_refs: list[str],
) -> dict[str, JsonValue]:
    record: dict[str, JsonValue] = {
        "schemaId": ACTIVE_SCHEMA,
        "recordType": "AutonomyAssessment",
        "assessmentId": assessment_id,
        "cardRef": card_ref,
        "certRef": cert_ref,
        "scope": scope,
        "transitionOutcome": transition_outcome,
        "autonomyLevel": autonomy_level,
        "authorizationStatus": authorization_status,
        "claimIsAuthorizing": claim_is_authorizing,
        "boundaryRelative": True,
        "tcbRelative": True,
        "witnessRelative": True,
        "humanFeedbackResidue": human_feedback_residue,
        "retainedAuthorityChannels": sorted(retained_authority_channels),
        "residualRisks": sorted(residual_risks),
        "blockingReasons": sorted(blocking_reasons),
        "requiredNextEvidence": sorted(required_next_evidence),
        "evidenceRefs": sorted(evidence_refs),
        "recordHash": "pending",
    }
    out = attach_record_hash(record)
    validate_autonomy_assessment(out)
    return out


def validate_autonomy_assessment(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, AUTONOMY_ASSESSMENT_FIELDS)
    if record["schemaId"] != ACTIVE_SCHEMA:
        raise ValueError("unsupported schemaId")
    if record["recordType"] != "AutonomyAssessment":
        raise ValueError("recordType must be AutonomyAssessment")
    require_hash(record["assessmentId"], "assessmentId")
    require_ref(record["cardRef"], "cardRef")
    require_ref(record["certRef"], "certRef")
    require_object(record["scope"], "scope")
    require_enum(record["transitionOutcome"], "transitionOutcome", TRANSITION_OUTCOMES)
    require_enum(record["autonomyLevel"], "autonomyLevel", AUTONOMY_LEVELS)
    require_enum(record["authorizationStatus"], "authorizationStatus", AUTHORIZATION_STATUSES)
    require_bool(record["claimIsAuthorizing"], "claimIsAuthorizing")
    require_bool(record["boundaryRelative"], "boundaryRelative")
    require_bool(record["tcbRelative"], "tcbRelative")
    require_bool(record["witnessRelative"], "witnessRelative")
    require_object(record["humanFeedbackResidue"], "humanFeedbackResidue")
    require_str_list(record["retainedAuthorityChannels"], "retainedAuthorityChannels")
    require_str_list(record["residualRisks"], "residualRisks")
    require_str_list(record["blockingReasons"], "blockingReasons")
    require_str_list(record["requiredNextEvidence"], "requiredNextEvidence")
    require_ref_list(record["evidenceRefs"], "evidenceRefs")
    require_hash(record["recordHash"], "recordHash")
