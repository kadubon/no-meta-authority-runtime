from __future__ import annotations

from no_meta_authority_runtime.schemas.task_envelope import empty_task_envelope, validate_task_envelope


def test_empty_envelope_grants_no_authority() -> None:
    env = empty_task_envelope(b"migrate authority")
    assert env["rootContractRef"] == "none"
    assert env["allowedTools"] == []
    validate_task_envelope(env, now=0)
