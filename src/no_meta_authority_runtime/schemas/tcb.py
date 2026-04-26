"""Trusted computing base budget records."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.base import require_enum, require_int, require_object, require_str_list
from no_meta_authority_runtime.schemas.constants import WITNESS_TIERS

TCB_PROFILES = frozenset({"Diagnostic", "SeedMicro", "LocalMicro", "Standard", "High"})


def tcb_budget(
    *,
    profile: str = "LocalMicro",
    components: list[str] | None = None,
    witness_tier: str = "replayableLocal",
    timeout_budget: int = 1000,
) -> dict[str, JsonValue]:
    data: dict[str, JsonValue] = {
        "profile": profile,
        "components": components or [],
        "componentCount": len(components or []),
        "codeSize": 0,
        "dependencyCount": 0,
        "stateSurfaces": [],
        "opaqueCalls": 0,
        "semanticCalls": 0,
        "overridePaths": 0,
        "updateGate": "twoSlot",
        "witnessTier": witness_tier,
        "timeoutBudget": timeout_budget,
    }
    validate_tcb_budget(data)
    return data


def validate_tcb_budget(record: dict[str, JsonValue]) -> None:
    require_enum(record.get("profile"), "profile", TCB_PROFILES)
    require_str_list(record.get("components"), "components")
    require_int(record.get("componentCount"), "componentCount")
    require_int(record.get("codeSize"), "codeSize")
    require_int(record.get("dependencyCount"), "dependencyCount")
    if not isinstance(record.get("stateSurfaces"), list):
        raise ValueError("stateSurfaces must be an array")
    require_int(record.get("opaqueCalls"), "opaqueCalls")
    require_int(record.get("semanticCalls"), "semanticCalls")
    require_int(record.get("overridePaths"), "overridePaths")
    require_enum(record.get("witnessTier"), "witnessTier", WITNESS_TIERS)
    require_int(record.get("timeoutBudget"), "timeoutBudget")
    require_object(record, "tcbBudget")
