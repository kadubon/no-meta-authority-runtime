from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import content_hash
from no_meta_authority_runtime.canonical.json import canonical_dumps
from no_meta_authority_runtime.matchers.default_matchers import default_matchers
from no_meta_authority_runtime.matchers.forbidden import evaluate_forbidden_matchers
from no_meta_authority_runtime.schemas.action import action_descriptor
from no_meta_authority_runtime.schemas.task_envelope import empty_task_envelope


def main() -> None:
    env = empty_task_envelope(b"mock agent", expires_at=10)
    safe = action_descriptor(
        kind="safeInventory",
        scope={"resource": "scratch"},
        task_envelope_ref=str(env["recordHash"]),
        args_hash=content_hash({"request": "mock"}),
        nonce="safe",
    )
    network = action_descriptor(
        kind="safeInventory",
        scope={"resource": "scratch"},
        task_envelope_ref=str(env["recordHash"]),
        args_hash=content_hash({"request": "mock-network"}),
        nonce="network",
        needs_network=True,
    )
    credential = action_descriptor(
        kind="safeInventory",
        scope={"resource": "scratch"},
        task_envelope_ref=str(env["recordHash"]),
        args_hash=content_hash({"request": "mock-credential"}),
        nonce="credential",
        needs_credential=True,
    )
    results = {}
    for name, action in {"safe": safe, "network": network, "credential": credential}.items():
        decision = evaluate_forbidden_matchers(default_matchers(env), action)
        results[name] = "wouldDispatchViaSeed" if decision is None else decision.__dict__
    print(canonical_dumps(results))


if __name__ == "__main__":
    main()
