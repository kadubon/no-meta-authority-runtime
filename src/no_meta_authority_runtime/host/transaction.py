"""Host transaction helpers."""

from __future__ import annotations

from uuid import uuid4


def new_tx_id() -> str:
    return "tx-" + uuid4().hex
