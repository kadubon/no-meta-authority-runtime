from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import attach_record_hash
from no_meta_authority_runtime.cert.claim_card import build_claim_card
from no_meta_authority_runtime.cert.transition_certificate import build_transition_certificate
from no_meta_authority_runtime.gate.claim_evaluator import decide_transition_outcome
from no_meta_authority_runtime.gate.transition_gate import transition_gate


def test_known_interface_claim_after_acceptance() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        acceptance_passed=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    cert = build_transition_certificate(cert_id="c1", card_ref=str(card["recordHash"]))
    decision = transition_gate(cert, card)
    assert decision.outcome == "allow"
    assert decision.transition_outcome == "knownInterfaceClaim"
    assert decision.authorizing is True


def test_complete_claim_requires_complete_inventory() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        intended_decision="completeClaim",
        acceptance_passed=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    assert decide_transition_outcome(card)[0] == "knownInterfaceClaim"


def test_irreversible_release_denied() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        acceptance_passed=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    card["effectEnvelope"] = {"unknown": False, "irreversibleInformationRelease": True}
    assert decide_transition_outcome(card)[0] == "deny"


def test_transition_gate_halts_on_modified_claim_card_hash() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        acceptance_passed=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    cert = build_transition_certificate(cert_id="c1", card_ref=str(card["recordHash"]))
    card["effectEnvelope"] = {"unknown": False, "irreversibleInformationRelease": True}

    decision = transition_gate(cert, card)

    assert decision.outcome == "halt"
    assert decision.transition_outcome == "halt"


def test_transition_gate_halts_on_card_ref_mismatch() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        acceptance_passed=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    cert = build_transition_certificate(cert_id="c1", card_ref="1" * 64)

    decision = transition_gate(cert, card)

    assert decision.outcome == "halt"
    assert decision.reason == "cardRefMismatch"


def test_transition_gate_defers_without_seed_consumption_evidence() -> None:
    card = build_claim_card(scope={"resource": "scratch"}, acceptance_passed=True, boot_ref="1" * 64)
    cert = build_transition_certificate(
        cert_id="c1",
        card_ref=str(card["recordHash"]),
        expected_transition_outcome="defer",
    )

    decision = transition_gate(cert, card)

    assert decision.outcome == "defer"
    assert decision.transition_outcome == "defer"
    assert decision.reason == "missingSeedConsumption"
    assert decision.authorizing is False


def test_transition_gate_halts_when_certificate_omits_card_evidence() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        acceptance_passed=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    cert = build_transition_certificate(cert_id="c1", card_ref=str(card["recordHash"]))
    cert["evidence"] = ["3" * 64]
    cert = attach_record_hash(cert)

    decision = transition_gate(cert, card)

    assert decision.outcome == "halt"
    assert decision.reason == "certificateMissingCardEvidence"


def test_transition_gate_defers_transition_mismatch() -> None:
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
        expected_transition_outcome="completeClaim",
    )

    decision = transition_gate(cert, card)

    assert decision.outcome == "defer"
    assert decision.reason == "certificateTransitionMismatch"


def test_transition_gate_rejects_nested_authorizing_field_even_when_rehashed() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        acceptance_passed=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    card["residuals"] = {"retainedAuthority": False, "grantAuthority": True}
    card = attach_record_hash(card)
    cert = build_transition_certificate(cert_id="c1", card_ref=str(card["recordHash"]))

    decision = transition_gate(cert, card)

    assert decision.outcome == "halt"
    assert decision.reason == "schemaInvalid"


def test_transition_gate_defers_provisional_claim() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    cert = build_transition_certificate(
        cert_id="c1",
        card_ref=str(card["recordHash"]),
        expected_transition_outcome="provisionalClaim",
    )

    decision = transition_gate(cert, card)

    assert decision.outcome == "defer"
    assert decision.transition_outcome == "provisionalClaim"
    assert decision.authorizing is False


def test_transition_gate_defers_partial_claim() -> None:
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

    decision = transition_gate(cert, card)

    assert decision.outcome == "defer"
    assert decision.transition_outcome == "partialClaim"
    assert decision.authorizing is False
