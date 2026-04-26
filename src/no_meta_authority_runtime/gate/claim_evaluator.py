"""Claim-strength evaluator for conservative transition outcomes."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import MISSING_REF, is_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.gate.acceptance_window import acceptance_window_passed


def decide_transition_outcome(card: dict[str, JsonValue]) -> tuple[str, str]:
    provisioning = _obj(card.get("provisioning"))
    boundary = _obj(card.get("boundary"))
    if boundary.get("rootContractRef") in {"none", None, ""}:
        return ("hostRequest", "missingRootContract")
    if not _seed_consumption_witnessed(card):
        return ("defer", "missingSeedConsumption")
    if provisioning.get("state") in {"requestOnly", "scratchOnly"}:
        return ("hostRequest", "missingHostedTransitionHost")
    if provisioning.get("state") == "blocked":
        return ("halt", "provisioningBlocked")
    timeouts = _obj(card.get("timeouts"))
    if timeouts.get("exhausted") is True:
        return ("timeout", "timeoutBudgetExhausted")
    envelope = _obj(card.get("effectEnvelope"))
    if envelope.get("irreversibleInformationRelease") is True:
        return ("deny", "irreversibleInformationRelease")
    if envelope.get("unknown") is True:
        return ("strongerTierRequest", "unknownEffect")
    probes = _obj(card.get("hostProbes"))
    for name in ("mediation", "ledger", "checker", "lock", "rollback", "digest"):
        probe = _obj(probes.get(name))
        if probe and probe.get("pass") is not True:
            if name in {"ledger", "lock", "rollback"}:
                return ("partialClaim", f"{name}WitnessTooWeak")
            return ("hostRequest", f"missing{name.capitalize()}")
    residuals = _obj(card.get("residuals"))
    if residuals.get("retainedAuthority") is True:
        return ("partialClaim", "retainedAuthorityBlocksPositiveClaim")
    if not acceptance_window_passed(card):
        return ("provisionalClaim", "acceptanceWindowNotPassed")
    inventory = _obj(card.get("inventoryWitness"))
    intended = card.get("intendedDecision")
    if intended == "completeClaim":
        if inventory.get("complete") is True and card.get("witnessTier") in {
            "externalAnchor",
            "independentAudit",
            "separateStorage",
        }:
            return ("completeClaim", "completeInventoryWitnessed")
        return ("knownInterfaceClaim", "incompleteInventory")
    return ("knownInterfaceClaim", "knownInterfacesWitnessed")


def _obj(value: JsonValue | object) -> dict[str, JsonValue]:
    return value if isinstance(value, dict) else {}


def _seed_consumption_witnessed(card: dict[str, JsonValue]) -> bool:
    if not is_hash(card.get("bootRef")):
        return False
    boot = _obj(card.get("bootDecision"))
    if boot.get("seedConsumed") is not True:
        return False
    consumption_ref = boot.get("consumptionRecordRef")
    return is_hash(consumption_ref) and consumption_ref != MISSING_REF
