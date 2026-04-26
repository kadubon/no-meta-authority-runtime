from __future__ import annotations

from no_meta_authority_runtime.autonomy.assessment import assess_declared_autonomy
from no_meta_authority_runtime.autonomy.verdict import is_scoped_authorizing
from no_meta_authority_runtime.canonical.hash import attach_record_hash
from no_meta_authority_runtime.cert.claim_card import build_claim_card
from no_meta_authority_runtime.cert.transition_certificate import build_transition_certificate


def test_known_interface_assessment_is_scoped_authorizing() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        acceptance_passed=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    cert = build_transition_certificate(
        cert_id="c1",
        card_ref=str(card["recordHash"]),
    )

    assessment = assess_declared_autonomy(card, certificate=cert)

    assert assessment["autonomyLevel"] == "knownInterfaceMigration"
    assert assessment["authorizationStatus"] == "scopedAuthorizing"
    assert assessment["claimIsAuthorizing"] is True
    assert is_scoped_authorizing(assessment) is True
    assert "globalHumanFeedbackResidueNotProvenAbsent" in assessment["residualRisks"]
    assert assessment["humanFeedbackResidue"]["globalWeightResidueProvenAbsent"] is False


def test_retained_live_authority_blocks_authorizing_autonomy() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        acceptance_passed=True,
        retained_authority=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    cert = build_transition_certificate(
        cert_id="c1",
        card_ref=str(card["recordHash"]),
        expected_transition_outcome="partialClaim",
    )

    assessment = assess_declared_autonomy(card, certificate=cert)

    assert assessment["autonomyLevel"] == "partialMigration"
    assert assessment["authorizationStatus"] == "nonAuthorizing"
    assert is_scoped_authorizing(assessment) is False
    assert assessment["claimIsAuthorizing"] is False
    assert "retainedPositiveAuthority" in assessment["retainedAuthorityChannels"]


def test_missing_certificate_blocks_positive_assessment() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        acceptance_passed=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )

    assessment = assess_declared_autonomy(card)

    assert assessment["autonomyLevel"] == "blocked"
    assert assessment["authorizationStatus"] == "nonAuthorizing"
    assert "missingTransitionCertificate" in assessment["blockingReasons"]
    assert is_scoped_authorizing(assessment) is False


def test_modified_claim_card_hash_halts_assessment() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        acceptance_passed=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    card["effectEnvelope"] = {"unknown": False, "irreversibleInformationRelease": True}

    assessment = assess_declared_autonomy(card)

    assert assessment["autonomyLevel"] == "blocked"
    assert assessment["transitionOutcome"] == "halt"
    assert "invalidClaimCard" in assessment["blockingReasons"]


def test_missing_seed_consumption_keeps_autonomy_non_authorizing() -> None:
    card = build_claim_card(scope={"resource": "scratch"}, acceptance_passed=True, boot_ref="1" * 64)
    cert = build_transition_certificate(
        cert_id="c1",
        card_ref=str(card["recordHash"]),
        expected_transition_outcome="defer",
    )

    assessment = assess_declared_autonomy(card, certificate=cert)

    assert assessment["authorizationStatus"] == "nonAuthorizing"
    assert assessment["transitionOutcome"] == "defer"
    assert "missingSeedConsumption" in assessment["blockingReasons"]
    assert "seedConsumedBootDecision" in assessment["requiredNextEvidence"]
    assert is_scoped_authorizing(assessment) is False


def test_authorizing_verdict_rejects_rehashed_blocking_reason() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        acceptance_passed=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    cert = build_transition_certificate(cert_id="c1", card_ref=str(card["recordHash"]))
    assessment = assess_declared_autonomy(card, certificate=cert)
    assessment["blockingReasons"] = ["manualOverride"]
    assessment = attach_record_hash(assessment)

    assert is_scoped_authorizing(assessment) is False
