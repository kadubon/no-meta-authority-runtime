"""Acceptance window checks."""

from __future__ import annotations

from no_meta_authority_runtime.canonical.json import JsonValue


def acceptance_window_passed(card: dict[str, JsonValue]) -> bool:
    window = card.get("acceptanceWindow", {})
    if not isinstance(window, dict):
        return False
    if window.get("passed") is not True:
        return False
    task_count = window.get("taskCount", 0)
    return isinstance(task_count, int) and not isinstance(task_count, bool) and task_count > 0
