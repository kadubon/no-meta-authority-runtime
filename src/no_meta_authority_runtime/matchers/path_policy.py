"""Literal path normalization and envelope checks."""

from __future__ import annotations

import os
from pathlib import Path

from no_meta_authority_runtime.canonical.errors import MatcherError


def normalize_literal_path(path: str, *, base: str | None = None, must_exist: bool = False) -> str:
    """Normalize a literal local path into slash-separated absolute form."""

    if path == "":
        raise MatcherError("empty path is not an authorizing literal path")
    if "\x00" in path or "*" in path or "?" in path:
        raise MatcherError("wildcards or NUL are not permitted in literal paths")
    candidate = Path(path)
    if not candidate.is_absolute():
        if base is None:
            raise MatcherError("relative path has no declared base")
        candidate = Path(base) / candidate
    if must_exist:
        try:
            candidate = candidate.resolve(strict=True)
        except OSError as exc:
            raise MatcherError("path cannot be resolved") from exc
    else:
        candidate = candidate.resolve(strict=False)
    normalized = candidate.as_posix()
    if normalized.endswith(" ") or normalized.endswith("."):
        raise MatcherError("trailing-space or trailing-dot aliases are denied")
    return _case_key(normalized)


def is_inside(path: str, root: str) -> bool:
    path_key = _case_key(path).rstrip("/")
    root_key = _case_key(root).rstrip("/")
    return path_key == root_key or path_key.startswith(root_key + "/")


def outside_envelope(paths: list[str], allowed_roots: list[str], denied_roots: list[str]) -> bool:
    """Return true if any path escapes all grants or enters any denied root."""

    if not paths:
        return False
    normalized_allowed = [normalize_literal_path(root) for root in allowed_roots if root]
    normalized_denied = [normalize_literal_path(root) for root in denied_roots if root]
    for raw in paths:
        path = normalize_literal_path(raw)
        if any(is_inside(path, denied) for denied in normalized_denied):
            return True
        if not normalized_allowed or not any(is_inside(path, root) for root in normalized_allowed):
            return True
    return False


def _case_key(path: str) -> str:
    return path.replace("\\", "/").casefold() if os.name == "nt" else path.replace("\\", "/")
