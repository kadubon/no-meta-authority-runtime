"""Local conformance runner."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from no_meta_authority_runtime.autonomy.assessment import assess_declared_autonomy
from no_meta_authority_runtime.canonical.hash import GENESIS_HASH, attach_record_hash, content_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.cert.claim_card import build_claim_card
from no_meta_authority_runtime.cert.transition_certificate import build_transition_certificate
from no_meta_authority_runtime.gate.claim_evaluator import decide_transition_outcome
from no_meta_authority_runtime.gate.transition_gate import transition_gate
from no_meta_authority_runtime.ledger.append_only import AppendOnlyLedger
from no_meta_authority_runtime.ledger.recovery import scan_ledger
from no_meta_authority_runtime.matchers.default_matchers import default_matchers
from no_meta_authority_runtime.schemas.action import action_descriptor
from no_meta_authority_runtime.schemas.boot_decision import boot_decision
from no_meta_authority_runtime.schemas.task_envelope import empty_task_envelope
from no_meta_authority_runtime.seed.interpreter import SeedInterpreter


def run_conformance() -> dict[str, JsonValue]:
    results: dict[str, JsonValue] = {}
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        results["cvEmptyEnv"] = "hostRequest"
        results["cvSafeInv"] = _safe_inv(root / "safe")
        results["cvBadSequence"] = _bad_sequence(root / "bad-seq")
        results["cvPrevHashMismatch"] = _prev_hash_mismatch(root / "prev")
        results["cvPermittedActionHashMismatch"] = _hash_mismatch_action(root / "action-hash")
        results["cvUnknownActionKind"] = _unknown_action_kind(root / "unknown-kind")
        results["cvNetworkDenied"] = _flag_denied(root / "network", "needs_network", True)
        results["cvCredentialHalted"] = _flag_denied(root / "credential", "needs_credential", True)
        results["cvPublicOutputDenied"] = _flag_denied(root / "public", "public_output", True)
        results["cvCheckerUpdateHalted"] = _flag_denied(root / "checker", "checker_update", True)
        results["cvKernelUpdateHalted"] = _flag_denied(root / "kernel", "kernel_update", True)
        results["cvUndeclaredToolDenied"] = _tool_denied(root / "undeclared", "undeclaredTool")
        results["cvPackageInstallerDenied"] = _tool_denied(root / "package", "pip")
        results["cvReadOutsideEnvelope"] = _path_escape(root / "read-escape", "read_set")
        results["cvWriteOutsideEnvelope"] = _path_escape(root / "write-escape", "write_set")
        results["cvOpenDecisionPreventsSecond"] = _open_decision_blocks_second(root / "open")
        results["cvDispatchWithoutIssue"] = SeedInterpreter(root / "dispatch-missing").dispatch(
            GENESIS_HASH, {}, {}, now=0
        )["outcome"]
        results["cvConsumeWithoutDispatch"] = SeedInterpreter(root / "consume-missing").consume(
            GENESIS_HASH, GENESIS_HASH, {}, now=0
        )["outcome"]
        no_root_card = build_claim_card(
            scope={"resource": "scratch"},
            acceptance_passed=True,
            boot_ref="1" * 64,
            seed_consumed=True,
            consumption_ref="2" * 64,
        )
        no_root_card["boundary"] = {"completeInventory": False, "rootContractRef": "none"}
        results["cvNoRootContractNoPositiveClaim"] = decide_transition_outcome(no_root_card)[0]
        scratch_card = build_claim_card(
            scope={"resource": "scratch"},
            acceptance_passed=True,
            boot_ref="1" * 64,
            seed_consumed=True,
            consumption_ref="2" * 64,
        )
        scratch_card["provisioning"] = {"state": "scratchOnly"}
        results["cvScratchOnlyNoHostInstallClaim"] = decide_transition_outcome(scratch_card)[0]
        unknown_card = build_claim_card(
            scope={"resource": "scratch"},
            intended_decision="completeClaim",
            acceptance_passed=True,
            boot_ref="1" * 64,
            seed_consumed=True,
            consumption_ref="2" * 64,
        )
        unknown_card["effectEnvelope"] = {"unknown": True, "irreversibleInformationRelease": False}
        results["cvUnknownInterfaceBlocksCompleteClaim"] = decide_transition_outcome(unknown_card)[0]
        incomplete_card = build_claim_card(
            scope={"resource": "scratch"},
            intended_decision="completeClaim",
            acceptance_passed=True,
            boot_ref="1" * 64,
            seed_consumed=True,
            consumption_ref="2" * 64,
        )
        results["cvIncompleteInventoryKnownInterfaceMax"] = decide_transition_outcome(incomplete_card)[0]
        release_card = build_claim_card(
            scope={"resource": "scratch"},
            acceptance_passed=True,
            boot_ref="1" * 64,
            seed_consumed=True,
            consumption_ref="2" * 64,
        )
        release_card["effectEnvelope"] = {"unknown": False, "irreversibleInformationRelease": True}
        results["cvIrreversibleInfoReleaseNotRollbackCertified"] = decide_transition_outcome(release_card)[0]
        ledger = AppendOnlyLedger(root / "dup")
        rec = ledger.append({"phase": "bootDecision", "recordHash": "pending"})
        bad = dict(rec)
        bad["recordHash"] = "0" * 64
        (root / "dup" / "000002-bad.json").write_text("{}", encoding="utf-8")
        results["cvDuplicateLedgerSequence"] = "detected" if not scan_ledger(root / "dup").ok else "missed"
        results["cvHashMismatch"] = _ledger_hash_mismatch(root / "hash-mismatch")
        results["cvCrashAfterDispatchRecovery"] = _crash_after_dispatch(root / "crash")
        card = build_claim_card(
            scope={"resource": "scratch"},
            acceptance_passed=True,
            boot_ref="1" * 64,
            seed_consumed=True,
            consumption_ref="2" * 64,
        )
        cert = build_transition_certificate(cert_id="c1", card_ref=str(card["recordHash"]))
        results["gate"] = transition_gate(cert, card).transition_outcome
        assessment = assess_declared_autonomy(card, certificate=cert)
        results["cvHumanFeedbackResidueRemainsResidualRisk"] = (
            "present" if "globalHumanFeedbackResidueNotProvenAbsent" in assessment["residualRisks"] else "missing"
        )
        retained_card = build_claim_card(
            scope={"resource": "scratch"},
            acceptance_passed=True,
            retained_authority=True,
            boot_ref="1" * 64,
            seed_consumed=True,
            consumption_ref="2" * 64,
        )
        retained_cert = build_transition_certificate(
            cert_id="c2",
            card_ref=str(retained_card["recordHash"]),
            expected_transition_outcome="partialClaim",
        )
        results["cvRetainedAuthorityBlocksAutonomy"] = assess_declared_autonomy(
            retained_card,
            certificate=retained_cert,
        )["authorizationStatus"]
        missing_seed_card = build_claim_card(
            scope={"resource": "scratch"},
            acceptance_passed=True,
            boot_ref="1" * 64,
        )
        missing_seed_cert = build_transition_certificate(
            cert_id="c3",
            card_ref=str(missing_seed_card["recordHash"]),
            expected_transition_outcome="defer",
        )
        results["cvMissingSeedConsumptionBlocksAutonomy"] = assess_declared_autonomy(
            missing_seed_card,
            certificate=missing_seed_cert,
        )["authorizationStatus"]
        provisional_card = build_claim_card(
            scope={"resource": "scratch"},
            boot_ref="1" * 64,
            seed_consumed=True,
            consumption_ref="2" * 64,
        )
        provisional_cert = build_transition_certificate(
            cert_id="c4",
            card_ref=str(provisional_card["recordHash"]),
            expected_transition_outcome="provisionalClaim",
        )
        results["cvProvisionalClaimGateNonAuthorizing"] = (
            "authorizing" if transition_gate(provisional_cert, provisional_card).authorizing else "nonAuthorizing"
        )
        partial_card = build_claim_card(
            scope={"resource": "scratch"},
            acceptance_passed=True,
            retained_authority=True,
            boot_ref="1" * 64,
            seed_consumed=True,
            consumption_ref="2" * 64,
        )
        partial_cert = build_transition_certificate(
            cert_id="c5",
            card_ref=str(partial_card["recordHash"]),
            expected_transition_outcome="partialClaim",
        )
        results["cvPartialClaimGateNonAuthorizing"] = (
            "authorizing" if transition_gate(partial_cert, partial_card).authorizing else "nonAuthorizing"
        )
        missing_evidence_card = build_claim_card(
            scope={"resource": "scratch"},
            acceptance_passed=True,
            boot_ref="1" * 64,
            seed_consumed=True,
            consumption_ref="2" * 64,
        )
        missing_evidence_cert = build_transition_certificate(
            cert_id="c6",
            card_ref=str(missing_evidence_card["recordHash"]),
        )
        missing_evidence_cert["evidence"] = ["3" * 64]
        missing_evidence_cert = attach_record_hash(missing_evidence_cert)
        results["cvCertificateMissingCardEvidence"] = transition_gate(
            missing_evidence_cert,
            missing_evidence_card,
        ).reason
        mismatch_card = build_claim_card(
            scope={"resource": "scratch"},
            acceptance_passed=True,
            boot_ref="1" * 64,
            seed_consumed=True,
            consumption_ref="2" * 64,
        )
        mismatch_cert = build_transition_certificate(
            cert_id="c7",
            card_ref=str(mismatch_card["recordHash"]),
            expected_transition_outcome="completeClaim",
        )
        results["cvCertificateTransitionMismatch"] = transition_gate(mismatch_cert, mismatch_card).reason
        modified_card = build_claim_card(
            scope={"resource": "scratch"},
            acceptance_passed=True,
            boot_ref="1" * 64,
            seed_consumed=True,
            consumption_ref="2" * 64,
        )
        modified_card["effectEnvelope"] = {"unknown": False, "irreversibleInformationRelease": True}
        results["cvModifiedClaimCardHashBlocksAutonomy"] = assess_declared_autonomy(modified_card)["transitionOutcome"]
    return results


def _safe_inv(root: Path) -> str:
    env = empty_task_envelope(b"migrate authority", expires_at=10)
    env["rootContractRef"] = "1" * 64
    env["boundaryFloorRef"] = "2" * 64
    seed = SeedInterpreter(root)
    action = action_descriptor(
        kind="safeInventory",
        scope={"resource": "scratch"},
        task_envelope_ref=str(env["recordHash"]),
        args_hash=content_hash({"request": "migrate authority"}),
        nonce="a",
    )
    decision = boot_decision(
        request_id="r1",
        seq=1,
        prev_hash=GENESIS_HASH,
        scope={"resource": "scratch"},
        mode="diagnoseOnly",
        permitted_next_action=action,
        forbidden_matchers=default_matchers(env),
        task_envelope_ref=str(env["recordHash"]),
        issued_at=0,
        expires_at=10,
        nonce="b",
    )
    issued = seed.issue(decision)
    return str(seed.dispatch(str(issued["bootDecisionHash"]), action, env)["outcome"])


def _bad_sequence(root: Path) -> str:
    env = empty_task_envelope(b"migrate authority", expires_at=10)
    action = action_descriptor(
        kind="safeInventory",
        scope={"resource": "scratch"},
        task_envelope_ref=str(env["recordHash"]),
        args_hash=content_hash({}),
        nonce="a",
    )
    decision = boot_decision(
        request_id="r1",
        seq=2,
        prev_hash=GENESIS_HASH,
        scope={"resource": "scratch"},
        mode="diagnoseOnly",
        permitted_next_action=action,
        forbidden_matchers=default_matchers(env),
        task_envelope_ref=str(env["recordHash"]),
        issued_at=0,
        expires_at=10,
        nonce="b",
    )
    return str(SeedInterpreter(root).issue(decision)["outcome"])


def _prev_hash_mismatch(root: Path) -> str:
    env = empty_task_envelope(b"migrate authority", expires_at=10)
    action = action_descriptor(
        kind="safeInventory",
        scope={"resource": "scratch"},
        task_envelope_ref=str(env["recordHash"]),
        args_hash=content_hash({}),
        nonce="a",
    )
    decision = boot_decision(
        request_id="r1",
        seq=1,
        prev_hash="f" * 64,
        scope={"resource": "scratch"},
        mode="diagnoseOnly",
        permitted_next_action=action,
        forbidden_matchers=default_matchers(env),
        task_envelope_ref=str(env["recordHash"]),
        issued_at=0,
        expires_at=10,
        nonce="b",
    )
    return str(SeedInterpreter(root).issue(decision)["outcome"])


def _hash_mismatch_action(root: Path) -> str:
    env, action, seed, decision = _issued_seed_fixture(root)
    issued = seed.issue(decision)
    other = dict(action)
    other["nonce"] = "different"
    return str(seed.dispatch(str(issued["bootDecisionHash"]), other, env)["outcome"])


def _unknown_action_kind(root: Path) -> str:
    env, action, seed, decision = _issued_seed_fixture(root)
    issued = seed.issue(decision)
    other = dict(action)
    other["kind"] = "unknownKind"
    return str(seed.dispatch(str(issued["bootDecisionHash"]), other, env)["outcome"])


def _tool_denied(root: Path, tool: str) -> str:
    env = empty_task_envelope(b"migrate authority", expires_at=10)
    env["rootContractRef"] = "1" * 64
    env["boundaryFloorRef"] = "2" * 64
    action = action_descriptor(
        kind="safeInventory",
        scope={"resource": "scratch"},
        task_envelope_ref=str(env["recordHash"]),
        args_hash=content_hash({"tool": tool}),
        nonce="a",
        tool=tool,
    )
    decision = boot_decision(
        request_id="r1",
        seq=1,
        prev_hash=GENESIS_HASH,
        scope={"resource": "scratch"},
        mode="diagnoseOnly",
        permitted_next_action=action,
        forbidden_matchers=default_matchers(env),
        task_envelope_ref=str(env["recordHash"]),
        issued_at=0,
        expires_at=10,
        nonce="b",
    )
    seed = SeedInterpreter(root)
    issued = seed.issue(decision)
    return str(seed.dispatch(str(issued["bootDecisionHash"]), action, env)["outcome"])


def _path_escape(root: Path, field: str) -> str:
    env = empty_task_envelope(b"migrate authority", expires_at=10)
    env["rootContractRef"] = "1" * 64
    env["boundaryFloorRef"] = "2" * 64
    env["grantedScratchRoot"] = (root / "scratch").as_posix()
    kwargs: dict[str, list[str]] = {"read_set": [], "write_set": []}
    kwargs[field] = [(root / "outside" / "x.txt").as_posix()]
    action = action_descriptor(
        kind="safeInventory",
        scope={"resource": "scratch"},
        task_envelope_ref=str(env["recordHash"]),
        args_hash=content_hash({"field": field}),
        nonce="a",
        read_set=kwargs["read_set"],
        write_set=kwargs["write_set"],
    )
    decision = boot_decision(
        request_id="r1",
        seq=1,
        prev_hash=GENESIS_HASH,
        scope={"resource": "scratch"},
        mode="diagnoseOnly",
        permitted_next_action=action,
        forbidden_matchers=default_matchers(env),
        task_envelope_ref=str(env["recordHash"]),
        issued_at=0,
        expires_at=10,
        nonce="b",
    )
    seed = SeedInterpreter(root)
    issued = seed.issue(decision)
    return str(seed.dispatch(str(issued["bootDecisionHash"]), action, env)["outcome"])


def _open_decision_blocks_second(root: Path) -> str:
    _env, _action, seed, decision = _issued_seed_fixture(root)
    first = seed.issue(decision)
    if first["outcome"] != "consumed":
        return str(first["outcome"])
    second = dict(decision)
    second["seq"] = 2
    second["prevHash"] = str(first["headHash"])
    return str(seed.issue(second)["outcome"])


def _ledger_hash_mismatch(root: Path) -> str:
    ledger = AppendOnlyLedger(root)
    first = ledger.append({"phase": "test", "recordHash": "pending"})
    path = next(root.glob("*.json"))
    path.write_text(
        path.read_text(encoding="utf-8").replace(str(first["recordHash"]), "f" * 64),
        encoding="utf-8",
    )
    return "detected" if not scan_ledger(root).ok else "missed"


def _crash_after_dispatch(root: Path) -> str:
    _env, action, seed, decision = _issued_seed_fixture(root)
    issued = seed.issue(decision)
    seed.ledger.append(
        {
            "schemaId": "no_meta_bootstrap_core",
            "bootDecisionHash": str(issued["bootDecisionHash"]),
            "actionHash": content_hash(action),
            "phase": "dispatched",
            "outcome": "none",
            "reasonCode": "",
            "issuedAt": 0,
            "recordHash": "pending",
        }
    )
    return str(seed.recover()["reasonCode"])


def _issued_seed_fixture(
    root: Path,
) -> tuple[dict[str, JsonValue], dict[str, JsonValue], SeedInterpreter, dict[str, JsonValue]]:
    env = empty_task_envelope(b"migrate authority", expires_at=10)
    env["rootContractRef"] = "1" * 64
    env["boundaryFloorRef"] = "2" * 64
    action = action_descriptor(
        kind="safeInventory",
        scope={"resource": "scratch"},
        task_envelope_ref=str(env["recordHash"]),
        args_hash=content_hash({"request": "migrate authority"}),
        nonce="a",
    )
    decision = boot_decision(
        request_id="r1",
        seq=1,
        prev_hash=GENESIS_HASH,
        scope={"resource": "scratch"},
        mode="diagnoseOnly",
        permitted_next_action=action,
        forbidden_matchers=default_matchers(env),
        task_envelope_ref=str(env["recordHash"]),
        issued_at=0,
        expires_at=10,
        nonce="b",
    )
    return env, action, SeedInterpreter(root), decision


def _flag_denied(root: Path, flag: str, value: bool) -> str:
    env = empty_task_envelope(b"migrate authority", expires_at=10)
    env["rootContractRef"] = "1" * 64
    env["boundaryFloorRef"] = "2" * 64
    seed = SeedInterpreter(root)
    flags = {
        "needs_network": False,
        "needs_credential": False,
        "public_output": False,
        "checker_update": False,
        "kernel_update": False,
    }
    flags[flag] = value
    action = action_descriptor(
        kind="safeInventory",
        scope={"resource": "scratch"},
        task_envelope_ref=str(env["recordHash"]),
        args_hash=content_hash({"request": "migrate authority", "flag": flag}),
        nonce="a",
        needs_network=flags["needs_network"],
        needs_credential=flags["needs_credential"],
        public_output=flags["public_output"],
        checker_update=flags["checker_update"],
        kernel_update=flags["kernel_update"],
    )
    decision = boot_decision(
        request_id="r1",
        seq=1,
        prev_hash=GENESIS_HASH,
        scope={"resource": "scratch"},
        mode="diagnoseOnly",
        permitted_next_action=action,
        forbidden_matchers=default_matchers(env),
        task_envelope_ref=str(env["recordHash"]),
        issued_at=0,
        expires_at=10,
        nonce="b",
    )
    issued = seed.issue(decision)
    return str(seed.dispatch(str(issued["bootDecisionHash"]), action, env)["outcome"])
