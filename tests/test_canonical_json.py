from __future__ import annotations

import pytest

from no_meta_authority_runtime.canonical.errors import CanonicalError
from no_meta_authority_runtime.canonical.json import canonical_bytes, parse_json


def test_canonical_json_sorted_compact() -> None:
    assert canonical_bytes({"b": 1, "a": True}) == b'{"a":true,"b":1}'


def test_duplicate_keys_rejected() -> None:
    with pytest.raises(CanonicalError):
        parse_json(b'{"a":1,"a":2}')


def test_float_rejected() -> None:
    with pytest.raises(CanonicalError):
        parse_json(b'{"a":1.2}')
