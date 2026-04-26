"""Fail-closed exception types used internally by the runtime."""

from __future__ import annotations


class NoMetaRuntimeError(Exception):
    """Base class for explicit runtime failures."""


class CanonicalError(NoMetaRuntimeError, ValueError):
    """Canonical encoding or parsing failed."""


class SchemaError(NoMetaRuntimeError, ValueError):
    """A record failed schema validation."""


class HashMismatchError(SchemaError):
    """A record hash did not match its canonical bytes."""


class LedgerError(NoMetaRuntimeError, RuntimeError):
    """The append-only ledger is inconsistent or unavailable."""


class MatcherError(NoMetaRuntimeError, ValueError):
    """A forbidden matcher is malformed or cannot be evaluated."""
