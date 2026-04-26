"""Claim card and transition certificate records."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import attach_record_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.base import (
    reject_unknown_fields,
    require_bool,
    require_enum,
    require_exact_fields,
    require_hash,
    require_int,
    require_object,
    require_ref,
    require_ref_list,
    require_str,
    require_str_list,
)
from no_meta_authority_runtime.schemas.constants import ACTIVE_SCHEMA, TRANSITION_OUTCOMES, WITNESS_TIERS
from no_meta_authority_runtime.schemas.provisioning import PROVISIONING_STATES
from no_meta_authority_runtime.schemas.tcb import tcb_budget, validate_tcb_budget

CLAIM_CARD_FIELDS = [
    "schemaId",
    "tier",
    "bootRef",
    "scope",
    "boundary",
    "tcbBudget",
    "bootDecision",
    "provisioning",
    "hostProbes",
    "witnessTier",
    "mediationWitness",
    "inventoryWitness",
    "ledgerWitness",
    "lockWitnesses",
    "accessWitnesses",
    "threats",
    "predicates",
    "effectEnvelope",
    "selectionEnvelope",
    "negativeAgenda",
    "floors",
    "acceptanceWindow",
    "timeouts",
    "residuals",
    "intendedDecision",
    "recordHash",
]

CERTIFICATE_FIELDS = [
    "schemaId",
    "id",
    "tier",
    "cardRef",
    "action",
    "authorityDiff",
    "selectionDiff",
    "agendaDiff",
    "evidence",
    "obligations",
    "effectEnvelope",
    "rollback",
    "floors",
    "privacy",
    "bypass",
    "kernel",
    "threats",
    "timeouts",
    "acceptance",
    "residuals",
    "notes",
    "recordHash",
]


def claim_card(
    *,
    scope: dict[str, JsonValue],
    intended_decision: str = "knownInterfaceClaim",
    boot_ref: str = "none",
    seed_consumed: bool = False,
    consumption_ref: str = "none",
    witness_tier: str = "replayableLocal",
    host_probes: dict[str, JsonValue] | None = None,
    retained_authority: bool = False,
    acceptance_passed: bool = False,
    complete_inventory: bool = False,
) -> dict[str, JsonValue]:
    record: dict[str, JsonValue] = {
        "schemaId": ACTIVE_SCHEMA,
        "tier": "micro",
        "bootRef": boot_ref,
        "scope": scope,
        "boundary": {"completeInventory": complete_inventory, "rootContractRef": "1" * 64},
        "tcbBudget": tcb_budget(),
        "bootDecision": {
            "seedConsumed": seed_consumed,
            "consumptionRecordRef": consumption_ref,
        },
        "provisioning": {"state": "hosted"},
        "hostProbes": host_probes or {},
        "witnessTier": witness_tier,
        "mediationWitness": {"pass": True},
        "inventoryWitness": {"complete": complete_inventory},
        "ledgerWitness": {"pass": True},
        "lockWitnesses": {"pass": True},
        "accessWitnesses": {},
        "threats": [],
        "predicates": [],
        "effectEnvelope": {"unknown": False, "irreversibleInformationRelease": False},
        "selectionEnvelope": {"deterministic": True},
        "negativeAgenda": {"bounded": True},
        "floors": {"passed": acceptance_passed},
        "acceptanceWindow": {"passed": acceptance_passed, "taskCount": 1},
        "timeouts": {"exhausted": False},
        "residuals": {"retainedAuthority": retained_authority},
        "intendedDecision": intended_decision,
        "recordHash": "pending",
    }
    out = attach_record_hash(record)
    validate_claim_card(out)
    return out


def transition_certificate(
    *,
    cert_id: str,
    card_ref: str,
    action: str,
    expected_transition_outcome: str = "knownInterfaceClaim",
    notes: str = "",
    residuals: dict[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    record: dict[str, JsonValue] = {
        "schemaId": ACTIVE_SCHEMA,
        "id": cert_id,
        "tier": "micro",
        "cardRef": card_ref,
        "action": action,
        "authorityDiff": {"removesLivePositiveAuthority": True},
        "selectionDiff": {"deterministicSelection": True},
        "agendaDiff": {"boundedAgenda": True},
        "evidence": [card_ref],
        "obligations": ["hashValidCard", "hashValidCertificate", "seedConsumedBootDecision"],
        "effectEnvelope": {"unknown": False, "irreversibleInformationRelease": False},
        "rollback": {"rollbackCertified": True},
        "floors": {"passed": True},
        "privacy": {"noSecretPayload": True},
        "bypass": {"knownBypassAbsent": True},
        "kernel": {"checkerUpdate": False, "kernelUpdate": False},
        "threats": [],
        "timeouts": {"exhausted": False},
        "acceptance": {"accepted": True, "expectedTransitionOutcome": expected_transition_outcome},
        "residuals": residuals or {"retainedAuthority": False},
        "notes": notes,
        "recordHash": "pending",
    }
    out = attach_record_hash(record)
    validate_transition_certificate(out)
    return out


def validate_claim_card(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, CLAIM_CARD_FIELDS)
    if require_str(record["schemaId"], "schemaId", nonempty=True) != ACTIVE_SCHEMA:
        raise ValueError("unsupported schemaId")
    require_str(record["tier"], "tier", nonempty=True)
    boot_ref = require_ref(record["bootRef"], "bootRef")
    require_object(record["scope"], "scope")
    _validate_boundary(require_object(record["boundary"], "boundary"))
    validate_tcb_budget(require_object(record["tcbBudget"], "tcbBudget"))
    seed_consumed, consumption_ref = _validate_boot_decision_summary(
        require_object(record["bootDecision"], "bootDecision")
    )
    if seed_consumed and (boot_ref == "none" or consumption_ref == "none"):
        raise ValueError("seedConsumed requires bootRef and consumptionRecordRef")
    if not seed_consumed and consumption_ref != "none":
        raise ValueError("consumptionRecordRef requires seedConsumed")
    _validate_provisioning_summary(require_object(record["provisioning"], "provisioning"))
    require_object(record["hostProbes"], "hostProbes")
    require_enum(record["witnessTier"], "witnessTier", WITNESS_TIERS)
    _validate_inventory_witness(require_object(record["inventoryWitness"], "inventoryWitness"))
    _validate_effect_envelope(require_object(record["effectEnvelope"], "effectEnvelope"))
    _validate_selection_envelope(require_object(record["selectionEnvelope"], "selectionEnvelope"))
    _validate_negative_agenda(require_object(record["negativeAgenda"], "negativeAgenda"))
    _validate_floors(require_object(record["floors"], "floors"))
    _validate_acceptance_window(require_object(record["acceptanceWindow"], "acceptanceWindow"))
    _validate_timeouts(require_object(record["timeouts"], "timeouts"))
    _validate_residuals(require_object(record["residuals"], "residuals"))
    require_enum(record["intendedDecision"], "intendedDecision", TRANSITION_OUTCOMES)
    require_hash(record["recordHash"], "recordHash")


def validate_transition_certificate(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, CERTIFICATE_FIELDS)
    if require_str(record["schemaId"], "schemaId", nonempty=True) != ACTIVE_SCHEMA:
        raise ValueError("unsupported schemaId")
    require_str(record["id"], "id", nonempty=True)
    require_str(record["tier"], "tier", nonempty=True)
    require_hash(record["cardRef"], "cardRef")
    if require_str(record["action"], "action", nonempty=True) != "authorityMigration":
        raise ValueError("certificate action must be authorityMigration")
    _validate_authority_diff(require_object(record["authorityDiff"], "authorityDiff"))
    _validate_selection_diff(require_object(record["selectionDiff"], "selectionDiff"))
    _validate_agenda_diff(require_object(record["agendaDiff"], "agendaDiff"))
    evidence = require_ref_list(record["evidence"], "evidence")
    if not evidence:
        raise ValueError("certificate evidence must be nonempty")
    require_str_list(record["obligations"], "obligations")
    _validate_effect_envelope(require_object(record["effectEnvelope"], "effectEnvelope"))
    _validate_rollback(require_object(record["rollback"], "rollback"))
    _validate_floors(require_object(record["floors"], "floors"))
    _validate_privacy(require_object(record["privacy"], "privacy"))
    _validate_bypass(require_object(record["bypass"], "bypass"))
    _validate_kernel(require_object(record["kernel"], "kernel"))
    require_str_list(record["threats"], "threats")
    _validate_timeouts(require_object(record["timeouts"], "timeouts"))
    _validate_certificate_acceptance(require_object(record["acceptance"], "acceptance"))
    _validate_residuals(require_object(record["residuals"], "residuals"))
    require_str(record["notes"], "notes")
    require_hash(record["recordHash"], "recordHash")


def _validate_authority_diff(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["removesLivePositiveAuthority"])
    require_bool(record["removesLivePositiveAuthority"], "authorityDiff.removesLivePositiveAuthority")


def _validate_selection_diff(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["deterministicSelection"])
    require_bool(record["deterministicSelection"], "selectionDiff.deterministicSelection")


def _validate_agenda_diff(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["boundedAgenda"])
    require_bool(record["boundedAgenda"], "agendaDiff.boundedAgenda")


def _validate_boundary(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["completeInventory", "rootContractRef"])
    require_bool(record["completeInventory"], "boundary.completeInventory")
    require_ref(record["rootContractRef"], "boundary.rootContractRef")


def _validate_boot_decision_summary(record: dict[str, JsonValue]) -> tuple[bool, str]:
    require_exact_fields(record, ["seedConsumed", "consumptionRecordRef"])
    seed_consumed = require_bool(record["seedConsumed"], "bootDecision.seedConsumed")
    consumption_ref = require_ref(record["consumptionRecordRef"], "bootDecision.consumptionRecordRef")
    return seed_consumed, consumption_ref


def _validate_provisioning_summary(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["state"])
    require_enum(record["state"], "provisioning.state", PROVISIONING_STATES)


def _validate_inventory_witness(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["complete"])
    require_bool(record["complete"], "inventoryWitness.complete")


def _validate_effect_envelope(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["unknown", "irreversibleInformationRelease"])
    require_bool(record["unknown"], "effectEnvelope.unknown")
    require_bool(record["irreversibleInformationRelease"], "effectEnvelope.irreversibleInformationRelease")


def _validate_selection_envelope(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["deterministic"])
    require_bool(record["deterministic"], "selectionEnvelope.deterministic")


def _validate_negative_agenda(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["bounded"])
    require_bool(record["bounded"], "negativeAgenda.bounded")


def _validate_floors(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["passed"])
    require_bool(record["passed"], "floors.passed")


def _validate_acceptance_window(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["passed", "taskCount"])
    require_bool(record["passed"], "acceptanceWindow.passed")
    task_count = require_int(record["taskCount"], "acceptanceWindow.taskCount")
    if task_count < 0:
        raise ValueError("acceptanceWindow.taskCount must be nonnegative")


def _validate_timeouts(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["exhausted"])
    require_bool(record["exhausted"], "timeouts.exhausted")


def _validate_rollback(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["rollbackCertified"])
    require_bool(record["rollbackCertified"], "rollback.rollbackCertified")


def _validate_privacy(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["noSecretPayload"])
    require_bool(record["noSecretPayload"], "privacy.noSecretPayload")


def _validate_bypass(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["knownBypassAbsent"])
    require_bool(record["knownBypassAbsent"], "bypass.knownBypassAbsent")


def _validate_kernel(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["checkerUpdate", "kernelUpdate"])
    require_bool(record["checkerUpdate"], "kernel.checkerUpdate")
    require_bool(record["kernelUpdate"], "kernel.kernelUpdate")


def _validate_certificate_acceptance(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ["accepted", "expectedTransitionOutcome"])
    require_bool(record["accepted"], "acceptance.accepted")
    require_enum(record["expectedTransitionOutcome"], "acceptance.expectedTransitionOutcome", TRANSITION_OUTCOMES)


def _validate_residuals(record: dict[str, JsonValue]) -> None:
    allowed = [
        "retainedAuthority",
        "retainedAuthorityChannels",
        "humanApprovalRequired",
        "rewardModelRequired",
        "constitutionRequired",
        "openSemanticAuthority",
        "hiddenMaterialSelector",
        "agendaUnbounded",
    ]
    reject_unknown_fields(record, allowed)
    if "retainedAuthority" not in record:
        raise ValueError("residuals.retainedAuthority is required")
    for field in allowed:
        if field == "retainedAuthorityChannels":
            if field in record:
                require_str_list(record[field], f"residuals.{field}")
        elif field in record:
            require_bool(record[field], f"residuals.{field}")
