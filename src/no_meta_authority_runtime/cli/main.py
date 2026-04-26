"""Top-level runtime CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from no_meta_authority_runtime.autonomy.assessment import assess_declared_autonomy, blocked_autonomy_assessment
from no_meta_authority_runtime.canonical.json import JsonValue, canonical_dumps, parse_json
from no_meta_authority_runtime.conformance.runner import run_conformance
from no_meta_authority_runtime.host.minimal_host import MinimalHost
from no_meta_authority_runtime.schemas.outcome import outcome_record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="no-meta-runtime")
    parser.add_argument(
        "command",
        choices=["boot", "prepare", "check", "commit", "recover", "digest", "deny", "autonomy", "conformance"],
    )
    args = parser.parse_args(argv)
    if args.command == "conformance":
        print(canonical_dumps(run_conformance()))
        return 0
    try:
        value = parse_json(sys.stdin.buffer.read() or b"{}")
        if not isinstance(value, dict):
            return _halt("inputNotObject")
        if args.command == "autonomy":
            print(canonical_dumps(_run_autonomy(value)))
            return 0
        result = _run_host(args.command, value)
        print(canonical_dumps(result))
        return 0 if result.get("outcome") in {"consumed", "recovered"} or args.command == "digest" else 10
    except Exception as exc:
        return _halt(exc.__class__.__name__)


def _run_host(command: str, request: dict[str, JsonValue]) -> dict[str, JsonValue]:
    host_root = request.get("hostRoot")
    env = request.get("taskEnvelope")
    if not isinstance(host_root, str) or not host_root:
        return outcome_record("halt", fields={"reason": "missingHostRoot"})
    if not isinstance(env, dict):
        return outcome_record("halt", fields={"reason": "missingTaskEnvelope"})
    host = MinimalHost(Path(host_root), env)
    now = int(request.get("clock", 0)) if isinstance(request.get("clock", 0), int) else 0
    operation = request.get("operation")
    if command == "boot":
        out = host.boot()
    elif command == "prepare":
        out = host.prepare(operation if isinstance(operation, dict) else {}, now=now)
    elif command == "check":
        out = host.check(str(request.get("txId", "")), operation if isinstance(operation, dict) else {}, now=now)
    elif command == "commit":
        out = host.commit(str(request.get("txId", "")), operation if isinstance(operation, dict) else {}, now=now)
    elif command == "recover":
        out = host.recover(now=now)
    elif command == "digest":
        out = {"outcome": "consumed", **host.digest()}
    elif command == "deny":
        out = host.deny(str(request.get("reasonCode", "explicitDeny")), now=now)
    else:
        out = {"outcome": "deny", "reason": "unknownCommand"}
    return out


def _run_autonomy(request: dict[str, JsonValue]) -> dict[str, JsonValue]:
    card = request.get("claimCard")
    if not isinstance(card, dict):
        return blocked_autonomy_assessment("missingClaimCard")
    certificate = request.get("transitionCertificate")
    supplied = request.get("transitionOutcome")
    return assess_declared_autonomy(
        card,
        certificate=certificate if isinstance(certificate, dict) else None,
        supplied_transition_outcome=supplied if isinstance(supplied, str) else None,
    )


def _halt(reason: str) -> int:
    print(canonical_dumps(outcome_record("halt", fields={"reason": reason})))
    return 40


if __name__ == "__main__":
    raise SystemExit(main())
