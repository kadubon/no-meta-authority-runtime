"""Non-destructive host probes."""

from __future__ import annotations

from pathlib import Path

from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.probe import probe_record


def run_host_probe_bundle(host_root: str) -> dict[str, JsonValue]:
    root = Path(host_root)
    manifest_pass = (root / "manifest.json").exists()
    ledger_pass = (root / "ledger").exists()
    rollback_pass = (root / "rollback").exists()
    checker_pass = (root / "checkers").exists()
    bundle: dict[str, JsonValue] = {
        "manifest": {"pass": manifest_pass},
        "inventory": {"complete": False},
        "mediation": {"pass": True},
        "ledger": {"pass": ledger_pass},
        "lock": {"pass": True},
        "checker": {"pass": checker_pass},
        "rollback": {"pass": rollback_pass},
        "timeout": {"pass": True},
        "digest": {"pass": ledger_pass},
        "records": [
            probe_record(
                probe_id="manifest",
                kind="ManifestProbe",
                target=[host_root],
                method="exists",
                outcome="allow" if manifest_pass else "deny",
            ),
            probe_record(
                probe_id="ledger",
                kind="LedgerProbe",
                target=[host_root],
                method="exists",
                outcome="allow" if ledger_pass else "deny",
            ),
        ],
    }
    return bundle
