from __future__ import annotations

from pathlib import Path

from no_meta_authority_runtime.ledger.append_only import AppendOnlyLedger
from no_meta_authority_runtime.ledger.recovery import scan_ledger


def test_ledger_append_chains(tmp_path: Path) -> None:
    ledger = AppendOnlyLedger(tmp_path / "ledger")
    first = ledger.append({"phase": "test", "recordHash": "pending"})
    second = ledger.append({"phase": "test", "recordHash": "pending"})
    assert second["prevHash"] == first["recordHash"]
    assert scan_ledger(tmp_path / "ledger").ok


def test_hash_mismatch_detected(tmp_path: Path) -> None:
    ledger = AppendOnlyLedger(tmp_path / "ledger")
    first = ledger.append({"phase": "test", "recordHash": "pending"})
    path = next((tmp_path / "ledger").glob("*.json"))
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace(str(first["recordHash"]), "f" * 64), encoding="utf-8")
    assert not scan_ledger(tmp_path / "ledger").ok
