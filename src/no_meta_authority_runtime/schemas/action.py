"""Action descriptor schema."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.hash import content_hash
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.base import (
    require_bool,
    require_enum,
    require_exact_fields,
    require_hash,
    require_object,
    require_str,
    require_str_list,
)
from no_meta_authority_runtime.schemas.constants import ACTION_KINDS, EFFECT_TAGS, RISK_CLASSES

ACTION_FIELDS = [
    "kind",
    "target",
    "scope",
    "readSet",
    "writeSet",
    "effectTags",
    "tool",
    "argsHash",
    "needsNetwork",
    "needsCredential",
    "publicOutput",
    "checkerUpdate",
    "kernelUpdate",
    "taskEnvelopeRef",
    "riskClass",
    "nonce",
]


def action_descriptor(
    *,
    kind: str,
    scope: dict[str, JsonValue],
    task_envelope_ref: str,
    args_hash: str,
    nonce: str,
    target: list[str] | None = None,
    read_set: list[str] | None = None,
    write_set: list[str] | None = None,
    effect_tags: list[str] | None = None,
    tool: str = "none",
    needs_network: bool = False,
    needs_credential: bool = False,
    public_output: bool = False,
    checker_update: bool = False,
    kernel_update: bool = False,
    risk_class: str = "micro",
) -> dict[str, JsonValue]:
    record: dict[str, JsonValue] = {
        "kind": kind,
        "target": target or [],
        "scope": scope,
        "readSet": read_set or [],
        "writeSet": write_set or [],
        "effectTags": effect_tags or [],
        "tool": tool,
        "argsHash": args_hash,
        "needsNetwork": needs_network,
        "needsCredential": needs_credential,
        "publicOutput": public_output,
        "checkerUpdate": checker_update,
        "kernelUpdate": kernel_update,
        "taskEnvelopeRef": task_envelope_ref,
        "riskClass": risk_class,
        "nonce": nonce,
    }
    validate_action_descriptor(record)
    return record


def validate_action_descriptor(record: dict[str, JsonValue]) -> None:
    require_exact_fields(record, ACTION_FIELDS)
    require_enum(record["kind"], "kind", ACTION_KINDS)
    require_str_list(record["target"], "target")
    require_object(record["scope"], "scope")
    require_str_list(record["readSet"], "readSet")
    require_str_list(record["writeSet"], "writeSet")
    effect_tags = require_str_list(record["effectTags"], "effectTags")
    for tag in effect_tags:
        if tag not in EFFECT_TAGS:
            raise ValueError(f"invalid effect tag: {tag}")
    require_str(record["tool"], "tool", nonempty=True, ascii_only=True)
    require_hash(record["argsHash"], "argsHash")
    require_bool(record["needsNetwork"], "needsNetwork")
    require_bool(record["needsCredential"], "needsCredential")
    require_bool(record["publicOutput"], "publicOutput")
    require_bool(record["checkerUpdate"], "checkerUpdate")
    require_bool(record["kernelUpdate"], "kernelUpdate")
    require_hash(record["taskEnvelopeRef"], "taskEnvelopeRef")
    require_enum(record["riskClass"], "riskClass", RISK_CLASSES)
    require_str(record["nonce"], "nonce", nonempty=True, ascii_only=True)


def action_hash(record: dict[str, JsonValue]) -> str:
    validate_action_descriptor(record)
    return content_hash(record)
