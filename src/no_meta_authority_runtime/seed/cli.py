"""Command line interface for the seed interpreter."""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from no_meta_authority_runtime.canonical.json import JsonValue, canonical_dumps, parse_json
from no_meta_authority_runtime.schemas.constants import EXIT_BY_OUTCOME
from no_meta_authority_runtime.seed.interpreter import SeedInterpreter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="no-meta-seed")
    parser.add_argument(
        "command",
        choices=["head", "parse", "issue", "dispatch", "consume", "recover", "digest", "deny"],
    )
    args = parser.parse_args(argv)
    try:
        request_value = parse_json(sys.stdin.buffer.read() or b"{}")
        if not isinstance(request_value, dict):
            return _emit_halt(args.command, "inputNotObject")
        request: dict[str, JsonValue] = request_value
        root = request.get("ledgerRoot")
        if not isinstance(root, str) or not root:
            return _emit_halt(args.command, "missingLedgerRoot")
        seed = SeedInterpreter(root)
        result = _run(seed, args.command, request)
        print(canonical_dumps(result))
        return EXIT_BY_OUTCOME.get(str(result.get("outcome")), 40)
    except Exception as exc:  # CLI boundary converts all unexpected failures to halt.
        return _emit_halt(args.command, exc.__class__.__name__)


def _run(
    seed: SeedInterpreter,
    command: str,
    request: dict[str, JsonValue],
) -> dict[str, JsonValue]:
    now = int(request.get("clock", 0)) if isinstance(request.get("clock", 0), int) else 0
    if command == "head":
        return seed.head()
    if command == "parse":
        env = request.get("taskEnvelope")
        return seed.parse(env if isinstance(env, dict) else {}, now=now)
    if command == "issue":
        decision = request.get("decision")
        return seed.issue(decision if isinstance(decision, dict) else {}, now=now)
    if command == "dispatch":
        action = request.get("action")
        env = request.get("taskEnvelope")
        decision_hash = request.get("bootDecisionHash")
        return seed.dispatch(
            str(decision_hash) if isinstance(decision_hash, str) else "",
            action if isinstance(action, dict) else {},
            env if isinstance(env, dict) else {},
            now=now,
        )
    if command == "consume":
        action_result = request.get("actionResult")
        return seed.consume(
            str(request.get("bootDecisionHash", "")),
            str(request.get("dispatchRecordHash", "")),
            action_result if isinstance(action_result, dict) else {},
            now=now,
        )
    if command == "recover":
        return seed.recover(now=now)
    if command == "digest":
        return seed.digest()
    if command == "deny":
        return seed.deny(
            str(request.get("bootDecisionHash", "")),
            str(request.get("reasonCode", "explicitDeny")),
            now=now,
        )
    return seed_command_halt(command, "unknownCommand")


def _emit_halt(command: str, reason: str) -> int:
    print(canonical_dumps(seed_command_halt(command, reason)))
    return 40


def seed_command_halt(command: str, reason: str) -> dict[str, JsonValue]:
    from no_meta_authority_runtime.ledger.head import GENESIS_HEAD
    from no_meta_authority_runtime.seed.commands import seed_command_result

    return seed_command_result(command=command, outcome="halt", head=GENESIS_HEAD, reason_code=reason)


def abort(message: str) -> NoReturn:
    raise SystemExit(message)


if __name__ == "__main__":
    raise SystemExit(main())
