"""Default forbidden matcher set from the paper."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.schemas.constants import PACKAGE_INSTALLER_TOOLS


def default_matchers(task_envelope: dict[str, JsonValue]) -> list[JsonValue]:
    allowed_tools = _sort_unique(["none", *_strings(task_envelope.get("allowedTools", []))])
    read_grants = {
        "grantFields": ["grantedReadMetadata"],
        "deniedField": "deniedRoots",
        "allowedRoots": _strings(task_envelope.get("grantedReadMetadata", [])),
        "deniedRoots": _strings(task_envelope.get("deniedRoots", [])),
    }
    write_grants = {
        "grantFields": ["grantedScratchRoot", "grantedHostRoot", "grantedWriteRoots"],
        "deniedField": "deniedRoots",
        "allowedRoots": _grant_roots(task_envelope),
        "deniedRoots": _strings(task_envelope.get("deniedRoots", [])),
    }
    return [
        _matcher("m001Network", "needsNetwork", "eq", True, "deny", "networkDenied"),
        _matcher("m002Credential", "needsCredential", "eq", True, "halt", "credentialDenied"),
        _matcher("m003PublicOutput", "publicOutput", "eq", True, "deny", "publicOutputDenied"),
        _matcher("m004CheckerUpdate", "checkerUpdate", "eq", True, "halt", "checkerUpdateDenied"),
        _matcher("m005KernelUpdate", "kernelUpdate", "eq", True, "halt", "kernelUpdateDenied"),
        _matcher("m006UnknownEffect", "effectTags", "contains", "unknown", "halt", "unknownEffect"),
        _matcher("m007ExternalWrite", "effectTags", "contains", "externalWrite", "deny", "externalWrite"),
        _matcher("m008InfoRelease", "effectTags", "contains", "infoRelease", "deny", "infoRelease"),
        _matcher("m009Delegation", "effectTags", "contains", "delegation", "deny", "delegation"),
        _matcher("m010MemoryWrite", "effectTags", "contains", "memoryWrite", "deny", "memoryWrite"),
        _matcher("m011PackageTool", "tool", "in", PACKAGE_INSTALLER_TOOLS, "deny", "packageTool"),
        _matcher("m012UndeclaredTool", "tool", "notIn", allowed_tools, "deny", "undeclaredTool"),
        _matcher("m013ReadOutside", "readSet", "outsideEnvelope", read_grants, "halt", "readOutsideEnvelope"),
        _matcher("m014WriteOutside", "writeSet", "outsideEnvelope", write_grants, "halt", "writeOutsideEnvelope"),
    ]


def _matcher(
    matcher_id: str,
    field: str,
    op: str,
    value: JsonValue,
    on_match: str,
    reason_code: str,
) -> JsonValue:
    return {
        "id": matcher_id,
        "field": field,
        "op": op,
        "value": value,
        "onMatch": on_match,
        "reasonCode": reason_code,
    }


def _grant_roots(task_envelope: dict[str, JsonValue]) -> list[str]:
    roots: list[str] = []
    for key in ("grantedScratchRoot", "grantedHostRoot"):
        value = task_envelope.get(key, "")
        if isinstance(value, str) and value:
            roots.append(value)
    roots.extend(_strings(task_envelope.get("grantedWriteRoots", [])))
    return _sort_unique(roots)


def _strings(value: JsonValue) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _sort_unique(values: list[str]) -> list[str]:
    return sorted(set(values))
