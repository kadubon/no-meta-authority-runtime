"""Certificate normal-form checks."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.json import JsonValue

NORMAL_FORM_KEYS = {
    "schemaId",
    "id",
    "tier",
    "cardRef",
    "action",
    "authorityDiff",
    "selectionDiff",
    "agendaDiff",
    "evidence",
    "obligations",
    "effectEnvelope",
    "rollback",
    "floors",
    "privacy",
    "bypass",
    "kernel",
    "threats",
    "timeouts",
    "acceptance",
    "residuals",
    "notes",
    "recordHash",
}


def is_normal_form(certificate: dict[str, JsonValue]) -> bool:
    return set(certificate) == NORMAL_FORM_KEYS and isinstance(certificate.get("notes"), str)
