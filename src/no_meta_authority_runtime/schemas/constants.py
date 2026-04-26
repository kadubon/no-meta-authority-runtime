"""Machine schema constants from the paper's executable fragment."""

from __future__ import annotations

ACTIVE_SCHEMA = "no_meta_bootstrap_core"
RAW_SCHEMA = "no_meta_bootstrap_core.rawInput"
MISSING_REF = "none"

BOOT_MODES = frozenset(
    {
        "diagnoseOnly",
        "requestHost",
        "installMicroHost",
        "probeHost",
        "prepare",
        "check",
        "commit",
        "recover",
        "digest",
        "emitClaim",
        "deny",
        "timeout",
        "halt",
    }
)

ACTION_KINDS = frozenset(
    {
        "safeInventory",
        "writeScratch",
        "requestHost",
        "installMinimalHost",
        "runHostProbes",
        "prepare",
        "check",
        "commit",
        "recover",
        "digest",
        "emitClaim",
        "deny",
        "timeout",
        "halt",
    }
)

EFFECT_TAGS = frozenset(
    {
        "localState",
        "externalWrite",
        "infoRelease",
        "delegation",
        "memoryWrite",
        "checkerUpdate",
        "kernelUpdate",
        "publicAction",
        "unknown",
    }
)

TRANSITION_OUTCOMES = frozenset(
    {
        "bootDecision",
        "provisionalClaim",
        "knownInterfaceClaim",
        "completeClaim",
        "partialClaim",
        "hostRequest",
        "strongerTierRequest",
        "defer",
        "deny",
        "timeout",
        "halt",
    }
)

AUTONOMY_LEVELS = frozenset(
    {
        "blocked",
        "seedMediated",
        "hostMediated",
        "provisionalMigration",
        "partialMigration",
        "knownInterfaceMigration",
        "completeMigration",
    }
)

AUTHORIZATION_STATUSES = frozenset({"nonAuthorizing", "scopedAuthorizing"})

SEED_COMMAND_OUTCOMES = frozenset(
    {"consumed", "recovered", "deny", "defer", "timeout", "halt"}
)

SEED_PHASES = frozenset(
    {"bootDecision", "dispatched", "consumed", "denied", "timedOut", "halted", "recovered"}
)

HOST_PHASES = frozenset(
    {
        "prepared",
        "reserved",
        "checked",
        "committed",
        "verified",
        "closed",
        "recovered",
        "denied",
        "timedOut",
        "halted",
        "deferred",
        "inDoubt",
    }
)

RISK_CLASSES = frozenset({"micro", "standard", "high"})
POLICIES = frozenset({"deny", "allowByGate"})
WITNESS_TIERS = frozenset(
    {
        "selfReport",
        "replayableLocal",
        "separateProcess",
        "separateStorage",
        "externalAnchor",
        "independentAudit",
    }
)

PACKAGE_INSTALLER_TOOLS = [
    "apt",
    "apt-get",
    "brew",
    "bundle",
    "cargo",
    "choco",
    "dnf",
    "gem",
    "go",
    "npm",
    "pip",
    "pipx",
    "poetry",
    "scoop",
    "uv",
    "winget",
]

EXIT_BY_OUTCOME = {
    "consumed": 0,
    "recovered": 0,
    "deny": 10,
    "defer": 20,
    "timeout": 30,
    "halt": 40,
}
