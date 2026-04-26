from __future__ import annotations

from tempfile import TemporaryDirectory

from no_meta_authority_runtime.canonical.hash import GENESIS_HASH, content_hash
from no_meta_authority_runtime.canonical.json import canonical_dumps
from no_meta_authority_runtime.matchers.default_matchers import default_matchers
from no_meta_authority_runtime.schemas.action import action_descriptor
from no_meta_authority_runtime.schemas.boot_decision import boot_decision
from no_meta_authority_runtime.schemas.task_envelope import empty_task_envelope
from no_meta_authority_runtime.seed.interpreter import SeedInterpreter


def main() -> None:
    with TemporaryDirectory() as tmp:
        env = empty_task_envelope(b"migrate authority", expires_at=10)
        env["rootContractRef"] = "1" * 64
        env["boundaryFloorRef"] = "2" * 64
        env["grantedScratchRoot"] = tmp
        env["allowedTools"] = ["referenceSeedCLI"]
        seed = SeedInterpreter(f"{tmp}/seed-ledger")
        action = action_descriptor(
            kind="safeInventory",
            scope={"resource": "scratch"},
            task_envelope_ref=str(env["recordHash"]),
            args_hash=content_hash({"request": "migrate authority"}),
            nonce="seed-demo-action",
        )
        decision = boot_decision(
            request_id="seed-demo",
            seq=1,
            prev_hash=GENESIS_HASH,
            scope={"resource": "scratch"},
            mode="diagnoseOnly",
            permitted_next_action=action,
            forbidden_matchers=default_matchers(env),
            task_envelope_ref=str(env["recordHash"]),
            issued_at=0,
            expires_at=10,
            nonce="seed-demo-decision",
        )
        issued = seed.issue(decision)
        dispatched = seed.dispatch(str(issued["bootDecisionHash"]), action, env)
        digest = seed.digest()
        print(canonical_dumps({"issued": issued, "dispatched": dispatched, "digest": digest}))


if __name__ == "__main__":
    main()
