"""Agent-facing helpers for AutonomyAssessment consumption."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.errors import HashMismatchError, SchemaError
from no_meta_authority_runtime.canonical.hash import verify_record_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.autonomy import validate_autonomy_assessment

_AUTHORIZING_TRANSITIONS = {"knownInterfaceClaim", "completeClaim"}


def is_scoped_authorizing(assessment: dict[str, JsonValue]) -> bool:
    """Return true only when an assessment is valid and scoped-authorizing.

    This helper is intentionally redundant with the record fields. It gives
    wrappers and agents one conservative check to call before treating an
    autonomy assessment as permission for the declared scope.
    """

    try:
        validate_autonomy_assessment(assessment)
        verify_record_hash(assessment)
    except (HashMismatchError, SchemaError, ValueError):
        return False
    if assessment.get("authorizationStatus") != "scopedAuthorizing":
        return False
    if assessment.get("claimIsAuthorizing") is not True:
        return False
    if assessment.get("transitionOutcome") not in _AUTHORIZING_TRANSITIONS:
        return False
    if assessment.get("blockingReasons") != []:
        return False
    return assessment.get("retainedAuthorityChannels") == []
