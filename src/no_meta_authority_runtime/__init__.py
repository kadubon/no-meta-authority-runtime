"""Reference runtime for seed-mediated, fail-closed authority migration."""

from __future__ import annotations

from typing import Any

from no_meta_authority_runtime.schemas.constants import ACTIVE_SCHEMA, RAW_SCHEMA

__all__ = [
    "ACTIVE_SCHEMA",
    "RAW_SCHEMA",
    "MinimalHost",
    "SeedInterpreter",
    "assess_declared_autonomy",
    "attach_record_hash",
    "is_scoped_authorizing",
    "record_hash",
    "verify_record_hash",
]

__version__ = "0.1.0"


def __getattr__(name: str) -> Any:
    """Lazily expose common integration objects without import cycles."""

    if name == "MinimalHost":
        from no_meta_authority_runtime.host.minimal_host import MinimalHost

        return MinimalHost
    if name == "SeedInterpreter":
        from no_meta_authority_runtime.seed.interpreter import SeedInterpreter

        return SeedInterpreter
    if name == "assess_declared_autonomy":
        from no_meta_authority_runtime.autonomy.assessment import assess_declared_autonomy

        return assess_declared_autonomy
    if name == "is_scoped_authorizing":
        from no_meta_authority_runtime.autonomy.verdict import is_scoped_authorizing

        return is_scoped_authorizing
    if name in {"attach_record_hash", "record_hash", "verify_record_hash"}:
        from no_meta_authority_runtime.canonical import hash as hash_module

        return getattr(hash_module, name)
    raise AttributeError(name)
