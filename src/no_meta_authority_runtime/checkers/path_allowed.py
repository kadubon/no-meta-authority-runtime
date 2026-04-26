"""Path allow/deny checker."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.errors import MatcherError
from no_meta_authority_runtime.checkers.base import CheckerResult, allow, halt
from no_meta_authority_runtime.matchers.path_policy import outside_envelope


def check_path_allowed(path: str, allowed_roots: list[str], denied_roots: list[str]) -> CheckerResult:
    try:
        if outside_envelope([path], allowed_roots, denied_roots):
            return halt("pathOutsideEnvelope", {"path": path})
    except MatcherError:
        return halt("pathNormalizationFailed", {"path": path})
    return allow("pathAllowed", {"path": path})
