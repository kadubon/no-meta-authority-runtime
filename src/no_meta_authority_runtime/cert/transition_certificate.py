"""Transition certificate builder wrapper."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.certificate import transition_certificate


def build_transition_certificate(
    *,
    cert_id: str,
    card_ref: str,
    action: str = "authorityMigration",
    expected_transition_outcome: str = "knownInterfaceClaim",
    notes: str = "",
    residuals: dict[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    return transition_certificate(
        cert_id=cert_id,
        card_ref=card_ref,
        action=action,
        expected_transition_outcome=expected_transition_outcome,
        notes=notes,
        residuals=residuals,
    )
