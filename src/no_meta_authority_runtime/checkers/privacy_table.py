"""Diagnostic privacy checker."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.checkers.base import CheckerResult, allow, halt


def check_privacy_table(field: str, privacy_table: list[JsonValue], requested_form: str) -> CheckerResult:
    for row in privacy_table:
        if not isinstance(row, dict) or row.get("field") != field:
            continue
        allowed = row.get("allowedForm")
        if allowed == requested_form or allowed == "public":
            return allow("privacyTableOk", {"field": field, "form": requested_form})
        return halt(str(row.get("onViolation", "privacyViolation")), {"field": field})
    if requested_form in {"public", "hashOnly"}:
        return allow("privacyDefaultOk", {"field": field, "form": requested_form})
    return halt("privacyRuleMissing", {"field": field})
