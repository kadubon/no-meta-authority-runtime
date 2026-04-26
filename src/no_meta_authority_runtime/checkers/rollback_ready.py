"""Rollback readiness checker."""

from __future__ import annotations

from pathlib import Path

from no_meta_authority_runtime.checkers.base import CheckerResult, allow, halt


def check_rollback_ready(rollback_ref: str, rollback_root: str) -> CheckerResult:
    if not rollback_ref or rollback_ref == "none":
        return halt("missingRollback")
    root = Path(rollback_root).resolve(strict=False)
    path = (root / rollback_ref).resolve(strict=False)
    if root not in path.parents and path != root:
        return halt("rollbackOutsideRoot")
    if not path.exists():
        return halt("rollbackMissing")
    return allow("rollbackReady", {"rollbackRef": rollback_ref})
