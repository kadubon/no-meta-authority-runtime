"""Claim card builder wrapper."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.certificate import claim_card


def build_claim_card(
    *,
    scope: dict[str, JsonValue],
    intended_decision: str = "knownInterfaceClaim",
    boot_ref: str = "none",
    seed_consumed: bool = False,
    consumption_ref: str = "none",
    host_probes: dict[str, JsonValue] | None = None,
    retained_authority: bool = False,
    acceptance_passed: bool = False,
    complete_inventory: bool = False,
    witness_tier: str = "replayableLocal",
) -> dict[str, JsonValue]:
    return claim_card(
        scope=scope,
        intended_decision=intended_decision,
        boot_ref=boot_ref,
        seed_consumed=seed_consumed,
        consumption_ref=consumption_ref,
        host_probes=host_probes,
        retained_authority=retained_authority,
        acceptance_passed=acceptance_passed,
        complete_inventory=complete_inventory,
        witness_tier=witness_tier,
    )
