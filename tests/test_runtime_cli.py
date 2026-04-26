from __future__ import annotations

import subprocess
import sys

from no_meta_authority_runtime.canonical.json import canonical_dumps, parse_json
from no_meta_authority_runtime.cert.claim_card import build_claim_card
from no_meta_authority_runtime.cert.transition_certificate import build_transition_certificate


def test_runtime_cli_autonomy_assessment() -> None:
    card = build_claim_card(
        scope={"resource": "scratch"},
        acceptance_passed=True,
        boot_ref="1" * 64,
        seed_consumed=True,
        consumption_ref="2" * 64,
    )
    cert = build_transition_certificate(cert_id="c1", card_ref=str(card["recordHash"]))
    payload = canonical_dumps({"claimCard": card, "transitionCertificate": cert}).encode("utf-8")

    proc = subprocess.run(
        [sys.executable, "-m", "no_meta_authority_runtime.cli.main", "autonomy"],
        input=payload,
        capture_output=True,
        check=True,
    )
    out = parse_json(proc.stdout)

    assert isinstance(out, dict)
    assert out["recordType"] == "AutonomyAssessment"
    assert out["authorizationStatus"] == "scopedAuthorizing"
