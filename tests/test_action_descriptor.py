from __future__ import annotations

import pytest

from no_meta_authority_runtime.canonical.hash import content_hash
from no_meta_authority_runtime.schemas.action import action_descriptor


def test_action_descriptor_validates_kind() -> None:
    action = action_descriptor(
        kind="safeInventory",
        scope={"resource": "scratch"},
        task_envelope_ref="1" * 64,
        args_hash=content_hash({}),
        nonce="n",
    )
    assert action["tool"] == "none"


def test_unknown_action_kind_rejected() -> None:
    with pytest.raises(ValueError):
        action_descriptor(
            kind="unknownKind",
            scope={"resource": "scratch"},
            task_envelope_ref="1" * 64,
            args_hash=content_hash({}),
            nonce="n",
        )
