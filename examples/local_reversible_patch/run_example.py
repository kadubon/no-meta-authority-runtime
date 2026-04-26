from __future__ import annotations

from tempfile import TemporaryDirectory

from no_meta_authority_runtime.autonomy.assessment import assess_declared_autonomy
from no_meta_authority_runtime.canonical.hash import GENESIS_HASH, attach_record_hash, content_hash
from no_meta_authority_runtime.canonical.json import canonical_dumps
from no_meta_authority_runtime.cert.claim_card import build_claim_card
from no_meta_authority_runtime.cert.transition_certificate import build_transition_certificate
from no_meta_authority_runtime.gate.transition_gate import transition_gate
from no_meta_authority_runtime.host.minimal_host import MinimalHost
from no_meta_authority_runtime.matchers.default_matchers import default_matchers
from no_meta_authority_runtime.schemas.action import action_descriptor
from no_meta_authority_runtime.schemas.boot_decision import boot_decision
from no_meta_authority_runtime.schemas.task_envelope import empty_task_envelope
from no_meta_authority_runtime.seed.interpreter import SeedInterpreter


def main() -> None:
    with TemporaryDirectory() as tmp:
        env = empty_task_envelope(b"local reversible patch", expires_at=100)
        env["rootContractRef"] = "1" * 64
        env["boundaryFloorRef"] = "2" * 64
        env["grantedScratchRoot"] = f"{tmp}/scratch"
        env["grantedHostRoot"] = f"{tmp}/host"
        env["grantedWriteRoots"] = [f"{tmp}/workspace"]
        env = attach_record_hash(env)
        workspace_file = f"{tmp}/workspace/example.txt"

        seed = SeedInterpreter(f"{tmp}/seed-ledger")
        action = action_descriptor(
            kind="safeInventory",
            scope={"resource": "example-workspace"},
            task_envelope_ref=str(env["recordHash"]),
            args_hash=content_hash({"request": "local reversible patch"}),
            nonce="safe-inventory",
        )
        decision = boot_decision(
            request_id="local-example",
            seq=1,
            prev_hash=GENESIS_HASH,
            scope={"resource": "example-workspace"},
            mode="diagnoseOnly",
            permitted_next_action=action,
            forbidden_matchers=default_matchers(env),
            task_envelope_ref=str(env["recordHash"]),
            issued_at=0,
            expires_at=100,
            nonce="boot",
        )
        issued = seed.issue(decision)
        dispatched = seed.dispatch(str(issued["bootDecisionHash"]), action, env)

        host = MinimalHost(f"{tmp}/host", env)
        host.boot()
        operation = {"kind": "writeText", "path": workspace_file, "content": "patched\n"}
        prepared = host.prepare(operation)
        checked = host.check(str(prepared["txId"]), operation)
        committed = host.commit(str(prepared["txId"]), operation)
        probes = host.probes()

        card = build_claim_card(
            scope={"resource": "example-workspace"},
            boot_ref=str(issued["bootDecisionHash"]),
            seed_consumed=True,
            consumption_ref=str(dispatched["consumptionRecordHash"]),
            host_probes=probes,
            acceptance_passed=True,
        )
        cert = build_transition_certificate(cert_id="local-example", card_ref=str(card["recordHash"]))
        gate = transition_gate(cert, card)
        autonomy = assess_declared_autonomy(card, certificate=cert)
        print(
            canonical_dumps(
                {
                    "prepared": prepared,
                    "seed": {"issued": issued, "dispatched": dispatched},
                    "checked": checked,
                    "committed": committed,
                    "gate": gate.__dict__,
                    "autonomy": autonomy,
                }
            )
        )


if __name__ == "__main__":
    main()
