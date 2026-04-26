"""Forbidden matcher grammar and evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase

from no_meta_authority_runtime.canonical.errors import MatcherError
from no_meta_authority_runtime.canonical.json import JsonValue
from no_meta_authority_runtime.matchers.path_policy import outside_envelope

MATCHER_FIELDS = {"id", "field", "op", "value", "onMatch", "reasonCode"}
MATCHER_OPS = {
    "eq",
    "notEq",
    "in",
    "notIn",
    "contains",
    "intersects",
    "prefix",
    "glob",
    "outsideEnvelope",
    "true",
}
MATCHER_OUTCOMES = {"deny", "halt"}


@dataclass(frozen=True)
class MatchDecision:
    outcome: str
    reason_code: str
    matcher_id: str


def evaluate_forbidden_matchers(
    matchers: list[JsonValue],
    action: dict[str, JsonValue],
) -> MatchDecision | None:
    first_deny: MatchDecision | None = None
    for matcher in sorted(matchers, key=_matcher_id):
        if not isinstance(matcher, dict):
            raise MatcherError("matcher must be an object")
        if _matches(matcher, action):
            decision = MatchDecision(
                outcome=str(matcher["onMatch"]),
                reason_code=str(matcher["reasonCode"]),
                matcher_id=str(matcher["id"]),
            )
            if decision.outcome == "halt":
                return decision
            if first_deny is None:
                first_deny = decision
    return first_deny


def validate_matcher(matcher: dict[str, JsonValue]) -> None:
    if set(matcher) != MATCHER_FIELDS:
        raise MatcherError("matcher fields do not match schema")
    if not isinstance(matcher["id"], str) or not matcher["id"]:
        raise MatcherError("matcher id must be nonempty string")
    if not isinstance(matcher["field"], str) or not matcher["field"]:
        raise MatcherError("matcher field must be nonempty string")
    if matcher["op"] not in MATCHER_OPS:
        raise MatcherError("unknown matcher operator")
    if matcher["onMatch"] not in MATCHER_OUTCOMES:
        raise MatcherError("unknown matcher outcome")
    if not isinstance(matcher["reasonCode"], str) or not matcher["reasonCode"]:
        raise MatcherError("matcher reasonCode must be nonempty")


def _matcher_id(matcher: JsonValue) -> str:
    if isinstance(matcher, dict) and isinstance(matcher.get("id"), str):
        return str(matcher["id"])
    return ""


def _matches(matcher: dict[str, JsonValue], action: dict[str, JsonValue]) -> bool:
    validate_matcher(matcher)
    field = str(matcher["field"])
    op = str(matcher["op"])
    expected = matcher["value"]
    actual = action.get(field)
    if op == "true":
        return True
    if actual is None:
        raise MatcherError(f"action missing matcher field: {field}")
    if op == "eq":
        return bool(actual == expected)
    if op == "notEq":
        return bool(actual != expected)
    if op == "in":
        return isinstance(expected, list) and actual in expected
    if op == "notIn":
        return isinstance(expected, list) and actual not in expected
    if op == "contains":
        return isinstance(actual, list) and expected in actual
    if op == "intersects":
        return isinstance(actual, list) and isinstance(expected, list) and bool(set(actual) & set(expected))
    if op == "prefix":
        return isinstance(actual, str) and isinstance(expected, str) and actual.startswith(expected)
    if op == "glob":
        return isinstance(actual, str) and isinstance(expected, str) and _glob_match(actual, expected)
    if op == "outsideEnvelope":
        if not isinstance(actual, list) or not all(isinstance(item, str) for item in actual):
            raise MatcherError("outsideEnvelope action field must be an array of strings")
        if not isinstance(expected, dict):
            raise MatcherError("outsideEnvelope value must be an object")
        allowed = expected.get("allowedRoots", [])
        denied = expected.get("deniedRoots", [])
        if not isinstance(allowed, list) or not isinstance(denied, list):
            raise MatcherError("outsideEnvelope roots must be arrays")
        allowed_str = [item for item in allowed if isinstance(item, str)]
        denied_str = [item for item in denied if isinstance(item, str)]
        actual_str = [item for item in actual if isinstance(item, str)]
        return outside_envelope(actual_str, allowed_str, denied_str)
    raise MatcherError("unknown matcher operator")


def _glob_match(value: str, pattern: str) -> bool:
    translated = pattern.replace("**", "*")
    return fnmatchcase(value, translated)
